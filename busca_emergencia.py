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

class BuscaEmergencia:
    def __init__(self, grafo: nx.DiGraph, estado_inicial: Dict):
        self.grafo = grafo
        self.estado = estado_inicial.copy()
        self.estado["zonas_afetadas"] = inicializar_zonas_afetadas(grafo)
        
        # Escolher dinamicamente o melhor algoritmo
        self.algoritmo_escolhido = self.escolher_melhor_algoritmo()

    def escolher_melhor_algoritmo(self):
        """Avalia os algoritmos e escolhe o melhor com base em custo e tempo."""
        heuristica = calcular_heuristica(self.grafo, "DESTINO")  # Ajustar destino para teste
        inicio = next(iter(self.grafo.nodes))  # Usar um nó qualquer como início para teste
        objetivo = "DESTINO"  # Ajustar para um objetivo válido

        algoritmos = {
            "Busca em Largura": lambda: busca_em_largura(self.grafo, inicio, objetivo),
            "Busca em Profundidade": lambda: busca_em_profundidade(self.grafo, inicio, objetivo),
            "Busca Gulosa": lambda: busca_gulosa(self.grafo, inicio, objetivo, heuristica),
            "A*": lambda: busca_a_estrela(self.grafo, inicio, objetivo, heuristica),
        }

        resultados = {}
        for nome, funcao in algoritmos.items():
            try:
                caminho = funcao()
                if caminho:
                    metricas = self.calcular_metricas_caminho(caminho)
                    resultados[nome] = metricas
            except Exception as e:
                print(f"Erro ao executar {nome}: {e}")

        if resultados:
            melhor = min(resultados.items(), key=lambda x: x[1]["custo"])
            print(f"Melhor algoritmo escolhido: {melhor[0]}")
            return melhor[0]
        else:
            print("Nenhum algoritmo encontrou um caminho válido. Usando A* por padrão.")
            return "A*"

    def calcular_metricas_caminho(self, caminho: List[str]) -> Dict:
        """Calcula métricas do caminho."""
        custo_total = sum(self.grafo[caminho[i]][caminho[i+1]]['custo'] for i in range(len(caminho)-1))
        tempo_total = sum(self.grafo[caminho[i]][caminho[i+1]]['tempo'] for i in range(len(caminho)-1))
        return {
            "custo": custo_total,
            "tempo": tempo_total
        }

    def busca_rota_prioritaria(self, veiculo_id: int) -> List[str]:
        """Implementa a busca com o algoritmo escolhido dinamicamente."""
        veiculo = next(v for v in self.estado["veiculos"] if v["id"] == veiculo_id)
        inicio = veiculo["localizacao"]

        # Ordenar zonas por score de emergência
        zonas_scores = [
            (zona_id, self.calcular_score_emergencia(zona_id))
            for zona_id in self.estado["zonas_afetadas"].keys()
        ]
        zonas_scores.sort(key=lambda x: x[1], reverse=True)

        heuristica = calcular_heuristica(self.grafo, "DESTINO")
        for zona_id, score in zonas_scores:
            if score == 0:  # Zona já suprida
                continue

            zona = self.estado["zonas_afetadas"][zona_id]
            if not self.verificar_capacidade_veiculo(veiculo, zona):
                continue

            if self.algoritmo_escolhido == "Busca em Largura":
                caminho = busca_em_largura(self.grafo, inicio, zona_id)
            elif self.algoritmo_escolhido == "Busca em Profundidade":
                caminho = busca_em_profundidade(self.grafo, inicio, zona_id)
            elif self.algoritmo_escolhido == "Busca Gulosa":
                caminho = busca_gulosa(self.grafo, inicio, zona_id, heuristica)
            elif self.algoritmo_escolhido == "A*":
                caminho = busca_a_estrela(self.grafo, inicio, zona_id, heuristica)
            else:
                caminho = None

            if caminho and self.verificar_autonomia(veiculo, caminho):
                return caminho

        return None

    def calcular_score_emergencia(self, zona_id: str) -> float:
        """Calcula o score de emergência para uma zona."""
        zona = self.estado["zonas_afetadas"][zona_id]
        if zona["suprida"]:
            return 0

        necessidades_total = sum(zona["necessidades"].values())
        score = (
            zona["prioridade"] * 2 +  # Peso maior para prioridade
            (zona["populacao"] / 1000) +  # Normalizado para população
            (necessidades_total / 300)  # Normalizado para necessidades
        )
        return score

    def verificar_capacidade_veiculo(self, veiculo: Dict, zona: Dict) -> bool:
        """Verifica se o veículo tem capacidade para atender às necessidades da zona."""
        return veiculo["capacidade"] >= sum(zona["necessidades"].values())

    def verificar_autonomia(self, veiculo: Dict, caminho: List[str]) -> bool:
        """Verifica se o veículo tem autonomia para completar o caminho."""
        custo_total = sum(self.grafo[caminho[i]][caminho[i+1]]['custo'] 
                         for i in range(len(caminho)-1))
        return veiculo["combustivel"] >= custo_total
