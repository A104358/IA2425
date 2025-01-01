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


class BuscaEmergencia:
    def __init__(self, grafo: nx.DiGraph, estado_inicial: Dict):
        self.grafo = grafo
        self.estado = estado_inicial.copy()
        self.estado["zonas_afetadas"] = inicializar_zonas_afetadas(grafo)
        self.restricao_acesso = RestricaoAcesso()
        self.algoritmo_escolhido = self.escolher_melhor_algoritmo()
    
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
            print(f"\nTestando {nome}...")
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
            print("Nenhum algoritmo encontrou um caminho válido")
            return "A*"  # Algoritmo padrão em caso de falha

    def busca_rota_prioritaria(self, veiculo_id: int) -> List[str]:
        """Busca a rota prioritária considerando o algoritmo escolhido."""
        veiculo = next(v for v in self.estado["veiculos"] if v["id"] == veiculo_id)
        inicio = veiculo["localizacao"]

        # Filtrar zonas acessíveis e calcular prioridades
        zonas_scores = [
            (zona_id, self.calcular_score_emergencia(zona_id))
            for zona_id in self.estado["zonas_afetadas"]
            if self.estado["zonas_afetadas"][zona_id]["janela_tempo"].esta_acessivel()
        ]
        if not zonas_scores:
            return None  # Nenhuma zona acessível

        zonas_scores.sort(key=lambda x: x[1], reverse=True)
        heuristica = None

        for zona_id, score in zonas_scores:
            if score <= 0:
                continue

            zona = self.estado["zonas_afetadas"][zona_id]
            if not self.verificar_capacidade_veiculo(veiculo, zona):
                continue

            if self.algoritmo_escolhido in ["Busca Gulosa", "A*"] and not heuristica:
                heuristica = calcular_heuristica(self.grafo, zona_id)

            caminho = None
            if self.algoritmo_escolhido == "Busca em Largura":
                caminho = busca_em_largura(self.grafo, inicio, zona_id)
            elif self.algoritmo_escolhido == "Busca em Profundidade":
                caminho = busca_em_profundidade(self.grafo, inicio, zona_id)
            elif self.algoritmo_escolhido == "Busca Gulosa":
                caminho = busca_gulosa(self.grafo, inicio, zona_id, heuristica)
            else:  # A* como padrão
                caminho = busca_a_estrela(self.grafo, inicio, zona_id, heuristica)

            if caminho and self.verificar_autonomia(veiculo, caminho):
                return caminho

        return None


    def planejar_reabastecimento(self, veiculo: Dict) -> List[str]:
        """Planeja uma rota para o posto de reabastecimento mais próximo."""
        postos = [
            node for node, data in self.grafo.nodes(data=True) if data.get('tipo') == 'posto'
        ]
        if not postos:
            print("Erro: Nenhum posto de reabastecimento disponível.")
            return None

        heuristica = calcular_heuristica(self.grafo, veiculo["localizacao"])
        melhor_posto = min(
            postos,
            key=lambda p: heuristica.get(p, float('inf'))
        )

        caminho = busca_a_estrela(self.grafo, veiculo["localizacao"], melhor_posto, heuristica)
        if caminho:
            print(f"Rota de reabastecimento planejada: {caminho}")
        else:
            print(f"Não foi possível planejar uma rota para o posto {melhor_posto}.")

        return caminho

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

        # Verificar se janela de tempo está presente, caso contrário criar padrão
        janela_tempo = zona.get("janela_tempo")
        if not janela_tempo:
            janela_tempo = JanelaTempoZona(
                zona_id=zona_id,
                inicio=datetime.now(),
                duracao_horas=24,
                prioridade=zona.get("prioridade", 1)
            )

        criticidade = janela_tempo.criticidade  # Criticidade baseada no tempo restante

        score = (
            zona.get("prioridade", 0) * 2  # Peso maior para prioridade
            + (zona.get("populacao", 0) / 1000)  # Normalizado para população
            + (necessidades_total / 300)  # Normalizado para necessidades
            + (criticidade * 2)  # Peso adicional para a criticidade
        )
        return score
    
    def verificar_capacidade_veiculo(self, veiculo: Dict, zona: Dict) -> bool:
        """Verifica se o veículo tem capacidade suficiente para atender às necessidades da zona."""
        capacidade_necessaria = sum(zona.get("necessidades", {}).values())
        return veiculo["capacidade"] >= capacidade_necessaria
