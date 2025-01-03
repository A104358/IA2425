import networkx as nx
import heapq
from typing import Dict, List
from estado_inicial import estado_inicial, inicializar_zonas_afetadas
from criar_grafo import PortugalDistributionGraph
from algoritmos_busca import (
    busca_em_largura,
    busca_em_profundidade,
    busca_gulosa,
    busca_a_estrela,
    calcular_heuristica
)
from limitacoes_geograficas import TipoTerreno, RestricaoAcesso
from janela_tempo import JanelaTempoZona
import time
from datetime import datetime, timedelta
import math


class BuscaEmergencia:
    def __init__(self, grafo: nx.DiGraph, estado_inicial: Dict):
        self.grafo = grafo
        self.estado = estado_inicial
        self.estado["zonas_afetadas"] = inicializar_zonas_afetadas(grafo)
        self.restricao_acesso = RestricaoAcesso()
        self.algoritmo_escolhido = self.escolher_melhor_algoritmo()
        self.pdg = PortugalDistributionGraph()
    
    def escolher_melhor_algoritmo(self):
        """
        Avalia os algoritmos considerando critérios principais:
        - Tempo de execução do algoritmo
        - Tempo real da rota (baseado nos pesos das arestas)
        - Custo total da rota
        """
        pontos_entrega = [n for n, d in self.grafo.nodes(data=True) if d.get('tipo') == 'entrega']
        bases = [n for n, d in self.grafo.nodes(data=True) if n.startswith('BASE_')]
        
        if not pontos_entrega or not bases:
            print("Erro: Não foram encontrados pontos suficientes no grafo")
            return "A*"
            
        inicio = bases[0]
        objetivo = pontos_entrega[0]
        
        # Calcular heurística para o objetivo escolhido
        heuristica = calcular_heuristica(self.grafo, objetivo)
        
        algoritmos = {
            "Busca em Largura": lambda: busca_em_largura(self.grafo, inicio, objetivo),
            "Busca em Profundidade": lambda: busca_em_profundidade(self.grafo, inicio, objetivo),
            "Busca Gulosa": lambda: busca_gulosa(self.grafo, inicio, objetivo, heuristica),
            "A*": lambda: busca_a_estrela(self.grafo, inicio, objetivo, heuristica)
        }

        resultados = {}
        num_testes = 5  # Número de testes para média
        
        print("\n=== Avaliação de Algoritmos ===")
        for nome, funcao in algoritmos.items():
            print(f"\nA testar {nome}...")
            tempos_execucao = []
            caminhos = []
            
            # Realizar múltiplos testes
            for i in range(num_testes):
                try:
                    inicio_tempo = time.time()
                    caminho = funcao()
                    tempo_execucao = time.time() - inicio_tempo
                    
                    if caminho:
                        tempos_execucao.append(tempo_execucao)
                        caminhos.append(caminho)
                except Exception as e:
                    print(f"Erro no teste {i+1}: {e}")
                    
            if caminhos:
                # Calcular médias dos testes
                tempo_exec_medio = sum(tempos_execucao) / len(tempos_execucao)
                
                # Para cada caminho, calcular tempo e custo total
                caminhos_metricas = []
                for caminho in caminhos:
                    tempo_rota = sum(self.grafo[caminho[i]][caminho[i+1]]['tempo'] 
                                   for i in range(len(caminho)-1))
                    custo_rota = sum(self.grafo[caminho[i]][caminho[i+1]]['custo'] 
                                   for i in range(len(caminho)-1))
                    caminhos_metricas.append({
                        'caminho': caminho,
                        'tempo_rota': tempo_rota,
                        'custo_rota': custo_rota
                    })
                
                # Escolher o melhor caminho baseado em tempo e custo
                melhor_caminho = min(caminhos_metricas, 
                                   key=lambda x: (x['tempo_rota'] + x['custo_rota']))
                
                resultados[nome] = {
                    "tempo_execucao": tempo_exec_medio,
                    "tempo_rota": melhor_caminho['tempo_rota'],
                    "custo_rota": melhor_caminho['custo_rota'],
                    "caminho": melhor_caminho['caminho']
                }
                
                print(f"Resultados para {nome}:")
                print(f"- Tempo médio de execução: {tempo_exec_medio:.4f} segundos")
                print(f"- Tempo da rota: {melhor_caminho['tempo_rota']:.2f} minutos")
                print(f"- Custo da rota: {melhor_caminho['custo_rota']:.2f} unidades")

        if resultados:
            # Normalizar as métricas para uma escala de 0 a 1
            max_tempo_exec = max(r["tempo_execucao"] for r in resultados.values())
            max_tempo_rota = max(r["tempo_rota"] for r in resultados.values())
            max_custo = max(r["custo_rota"] for r in resultados.values())
            
            scores = {}
            for nome, metricas in resultados.items():
                # Calcular score ponderado (focando no que realmente importa)
                score = (
                    0.2 * (metricas["tempo_execucao"] / max_tempo_exec) +  # 20% peso
                    0.4 * (metricas["tempo_rota"] / max_tempo_rota) +      # 40% peso
                    0.4 * (metricas["custo_rota"] / max_custo)            # 40% peso
                )
                scores[nome] = score
            
            # Escolher algoritmo com menor score (menor é melhor)
            melhor_algoritmo = min(scores.items(), key=lambda x: x[1])
            print(f"\nMelhor algoritmo escolhido: {melhor_algoritmo[0]}")
            print(f"Score final: {melhor_algoritmo[1]:.4f}")
            return melhor_algoritmo[0]
        else:
            print("Nenhum dos algoritmos encontrou um caminho válido")
            return "A*"  # Algoritmo padrão em caso de falha

    def busca_rota_prioritaria(self, veiculo_id: int, destino_especifico: str = None) -> List[str]:
        """
        Busca a rota prioritária considerando proximidade e prioridade da zona.
        
        Args:
            veiculo_id: ID do veículo
            destino_especifico: Opcional - ID da zona específica de destino
        
        Returns:
            List[str]: Lista de nós representando a rota, ou None se não encontrar rota válida
        """
        veiculo = next(v for v in self.estado["veiculos"] if v["id"] == veiculo_id)
        inicio = veiculo["localizacao"]
        
        # Obter coordenadas do veículo
        coord_veiculo = self.grafo.nodes[inicio]['coordenadas']
        
        # Se tiver um destino específico, verificar apenas esse destino
        if destino_especifico:
            if destino_especifico not in self.estado["zonas_afetadas"]:
                return None
                
            zona_info = self.estado["zonas_afetadas"][destino_especifico]
            if zona_info.get("suprida", False) or not zona_info["janela_tempo"].esta_acessivel():
                return None
                
            if not self.verificar_capacidade_veiculo(veiculo, zona_info):
                return None
                
            heuristica = calcular_heuristica(self.grafo, destino_especifico)
            evitar = [e.value for e in self.restricao_acesso.restricoes_veiculo[veiculo["tipo"]]]
            
            if self.algoritmo_escolhido == "Busca em Largura":
                return busca_em_largura(self.grafo, inicio, destino_especifico, evitar=evitar)
            elif self.algoritmo_escolhido == "Busca em Profundidade":
                return busca_em_profundidade(self.grafo, inicio, destino_especifico, evitar=evitar)
            elif self.algoritmo_escolhido == "Busca Gulosa":
                return busca_gulosa(self.grafo, inicio, destino_especifico, heuristica, evitar=evitar)
            else:  # A* como padrão
                return busca_a_estrela(self.grafo, inicio, destino_especifico, heuristica, evitar=evitar)
        
        # Filtrar zonas acessíveis e calcular scores
        zonas_candidatas = []
        for zona_id, zona_info in self.estado["zonas_afetadas"].items():
            if not zona_info["janela_tempo"].esta_acessivel() or zona_info.get("suprida", False):
                continue
                
            if not self.verificar_capacidade_veiculo(veiculo, zona_info):
                continue
                
            # Usar o método calcula_distancia do PDG em vez de cálculo euclidiano
            coord_zona = self.grafo.nodes[zona_id]['coordenadas']
            distancia = self.pdg.calcula_distancia(coord_veiculo, coord_zona)
            
            # Normalizar distância (quanto menor a distância, maior o score)
            max_dist = 300.0  # Ajustado para distâncias reais em km
            score_distancia = 1 - min(distancia / max_dist, 1.0)
            
            # Identificar região da zona para considerações adicionais
            regiao_zona = self.pdg._determinar_regiao(coord_zona)
            
            score_emergencia = self.calcular_score_emergencia(zona_id)
            # Adicionar peso para zonas na mesma região
            regiao_veiculo = self.pdg._determinar_regiao(coord_veiculo)
            bonus_regiao = 0.1 if regiao_zona == regiao_veiculo else 0
            
            score_total = (0.5 * score_emergencia) + (0.4 * score_distancia) + (0.1 * bonus_regiao)
            
            zonas_candidatas.append({
                'zona_id': zona_id,
                'score': score_total,
                'distancia': distancia,
                'regiao': regiao_zona
            })
        
        # Ordenar zonas por score total
        zonas_candidatas.sort(key=lambda x: x['score'], reverse=True)
        
        # Cache para heurística
        heuristica = None
        
        # Tentar encontrar um caminho válido para cada zona candidata
        for zona in zonas_candidatas:
            zona_id = zona['zona_id']
            
            if zona_id == inicio:
                continue
            
            if self.algoritmo_escolhido in ["Busca Gulosa", "A*"] and not heuristica:
                heuristica = calcular_heuristica(self.grafo, zona_id)
            
            evitar = [e.value for e in self.restricao_acesso.restricoes_veiculo[veiculo["tipo"]]]
            caminho = None
            if self.algoritmo_escolhido == "Busca em Largura":
                caminho = busca_em_largura(self.grafo, inicio, zona_id, evitar=evitar)
            elif self.algoritmo_escolhido == "Busca em Profundidade":
                caminho = busca_em_profundidade(self.grafo, inicio, zona_id, evitar=evitar)
            elif self.algoritmo_escolhido == "Busca Gulosa":
                caminho = busca_gulosa(self.grafo, inicio, zona_id, heuristica, evitar=evitar)
            else:  # A* como padrão
                caminho = busca_a_estrela(self.grafo, inicio, zona_id, heuristica, evitar=evitar)
            
            if caminho and self.verificar_autonomia(veiculo, caminho):
                print(f"Veículo {veiculo_id} indo para zona {zona_id} na região {zona['regiao']}")
                return caminho
        
        return None
    def planear_reabastecimento(self, veiculo: Dict) -> List[str]:
        """Planea uma rota para o posto de reabastecimento mais próximo."""
        coord_veiculo = self.grafo.nodes[veiculo["localizacao"]]['coordenadas']
        regiao_veiculo = self.pdg._determinar_regiao(coord_veiculo)
        
        # Primeiro tentar posto da mesma região
        posto_regiao = self.estado["postos_reabastecimento"].get(regiao_veiculo)
        
        postos = [
            node for node, data in self.grafo.nodes(data=True) if data.get('tipo') == 'posto'
        ]
        if not postos:
            print("Erro: Nenhum posto de reabastecimento disponível.")
            return None

        # Se houver posto na mesma região, dar prioridade a ele
        if posto_regiao in postos:
            postos.remove(posto_regiao)
            postos.insert(0, posto_regiao)

        # Tentar cada posto, começando pelo da mesma região
        for posto in postos:
            coord_posto = self.grafo.nodes[posto]['coordenadas']
            distancia = self.pdg.calcula_distancia(coord_veiculo, coord_posto)
            
            if distancia <= veiculo["combustivel"]:  # Se tiver autonomia para chegar
                heuristica = calcular_heuristica(self.grafo, posto)
                caminho = busca_a_estrela(self.grafo, veiculo["localizacao"], posto, heuristica)
                if caminho:
                    print(f"Rota de reabastecimento planejada para {posto}")
                    print(f"Distância até o posto: {distancia:.2f} km")
                    return caminho

        print("Não foi possível encontrar um posto de reabastecimento acessível.")
        return None

    def verificar_autonomia(self, veiculo: Dict, caminho: List[str]) -> bool:
        """Verifica se o veículo tem autonomia suficiente para a rota."""
        if not caminho:
            return False
        custo_total = sum(
            self.grafo[caminho[i]][caminho[i + 1]]['custo']
            for i in range(len(caminho) - 1)
        )
        return veiculo["combustivel"] >= custo_total

    def calcular_score_emergencia(self, zona_id: str) -> float:
        """Calcula o score de emergência para uma zona."""
        zona = self.estado["zonas_afetadas"].get(zona_id, {})
        if zona.get("suprida", False):
            return 0

        necessidades_total = sum(zona.get("necessidades", {}).values())

        janela_tempo = zona.get("janela_tempo")
        if not janela_tempo:
            janela_tempo = JanelaTempoZona(
                zona_id=zona_id,
                inicio=datetime.now(),
                duracao_horas=24,
                prioridade=zona.get("prioridade", 1)
            )

        criticidade = janela_tempo.criticidade

        score = (
            zona.get("prioridade", 0) * 2
            + (zona.get("populacao", 0) / 1000)
            + (necessidades_total / 300)
            + (criticidade * 2)
        )
        return score
    
    def verificar_capacidade_veiculo(self, veiculo: Dict, zona: Dict) -> bool:
        """Verifica se o veículo tem capacidade suficiente para atender às necessidades da zona."""
        capacidade_necessaria = sum(zona.get("necessidades", {}).values())
        return veiculo["capacidade"] >= capacidade_necessaria
    
    def calcular_prioridade_zona(self, zona: Dict) -> float:
        """Calcula a prioridade de uma zona considerando a janela de tempo."""
        janela = zona["janela_tempo"]
        prioridade_base = float(zona.get("prioridade", 1.0))
        
        if janela.esta_em_periodo_critico():
            fator_urgencia = janela.get_fator_urgencia()
            return prioridade_base * fator_urgencia
            
        return prioridade_base