from enum import Enum
import random
from typing import Dict, List, Set, Tuple
import networkx as nx

class TipoObstaculo(Enum):
    INUNDACAO = "inundacao"
    DESLIZAMENTO = "deslizamento"
    QUEDA_ARVORES = "queda_arvores"
    EROSÃO = "erosao"
    DESMORONAMENTO = "desmoronamento"

class TipoEvento(Enum):
    FALHA_COMUNICACAO = "falha_comunicacao"
    EVACUACAO = "evacuacao"
    RESGATE_EM_ANDAMENTO = "resgate_em_andamento"
    OBRA_EMERGENCIA = "obra_emergencia"
    FALHA_ESTRUTURAL = "falha_estrutural"

class GestorEventos:
    def __init__(self, grafo: nx.DiGraph):
        self.grafo = grafo
        self.obstaculos = {}
        self.eventos = {}
        self.multiplicadores_densidade = {
            'alta': {'custo': 1.3, 'tempo': 1.2},
            'normal': {'custo': 1.0, 'tempo': 1.0},
            'baixa': {'custo': 0.8, 'tempo': 0.9}
        }
        # Multiplicadores de impacto para obstáculos
        self.multiplicadores_obstaculos = {
            TipoObstaculo.INUNDACAO: {
                'custo': 2.5,
                'tempo': 3.0,
                'duracao': (72, 240),
                'prob_remocao': 0.05
            },
            TipoObstaculo.DESLIZAMENTO: {
                'custo': 3.0,
                'tempo': 3.5,
                'duracao': (48, 168),
                'prob_remocao': 0.03
            },
            TipoObstaculo.QUEDA_ARVORES: {
                'custo': 1.8,
                'tempo': 2.2,
                'duracao': (24, 72),
                'prob_remocao': 0.2
            },
             TipoObstaculo.EROSÃO: {
                'custo': 2.2,
                'tempo': 2.7,
                'duracao': (36, 120),
                'prob_remocao': 0.1
            },
            TipoObstaculo.DESMORONAMENTO: {
                'custo': 3.5,
                'tempo': 4.0,
                'duracao': (72, 240),
                'prob_remocao': 0.02
            }
        }

        # Multiplicadores de impacto para eventos
        self.multiplicadores_eventos = {
            TipoEvento.FALHA_COMUNICACAO: {
                'custo': 2.0,
                'tempo': 2.5,
                'duracao': (6, 24),
                'prob_remocao': 0.1
            },
            TipoEvento.EVACUACAO: {
                'custo': 2.8,
                'tempo': 3.0,
                'duracao': (12, 36),
                'prob_remocao': 0.05
            },
            TipoEvento.RESGATE_EM_ANDAMENTO: {
                'custo': 3.0,
                'tempo': 3.5,
                'duracao': (6, 24),
                'prob_remocao': 0.1
            },
            TipoEvento.OBRA_EMERGENCIA: {
                'custo': 2.2,
                'tempo': 2.8,
                'duracao': (12, 48),
                'prob_remocao': 0.2
            },
            TipoEvento.FALHA_ESTRUTURAL: {
                'custo': 3.5,
                'tempo': 4.0,
                'duracao': (48, 120),
                'prob_remocao': 0.05
            }
        }

        self.contadores_tempo = {}

    def adicionar_obstaculo_fixo(self, node_id: str):
        if node_id in self.grafo and self.grafo.nodes[node_id]['tipo'] != 'base':
            tipo = random.choice(list(TipoObstaculo))
            self.obstaculos[node_id] = tipo
            duracao_min, duracao_max = self.multiplicadores_obstaculos[tipo]['duracao']
            self.contadores_tempo[node_id] = random.randint(duracao_min, duracao_max)
            return True
        return False

    def adicionar_evento_dinamico(self, node1: str, node2: str):
        if (node1, node2) in self.grafo.edges:
            tipo = random.choice(list(TipoEvento))
            self.eventos[(node1, node2)] = tipo
            duracao_min, duracao_max = self.multiplicadores_eventos[tipo]['duracao']
            self.contadores_tempo[(node1, node2)] = random.randint(duracao_min, duracao_max)
            return True
        return False

    def gerar_eventos_aleatorios(self, prob_novo_evento: float = 0.3):
        for node in self.grafo.nodes():
            if (node not in self.obstaculos and 
                random.random() < prob_novo_evento and 
                self.grafo.nodes[node]['tipo'] != 'base'):
                self.adicionar_obstaculo_fixo(node)

        for edge in self.grafo.edges():
            if (edge not in self.eventos and 
                random.random() < prob_novo_evento):
                self.adicionar_evento_dinamico(edge[0], edge[1])

    def atualizar_eventos(self):
        items_to_remove = []

        for node, tipo in self.obstaculos.items():
            self.contadores_tempo[node] -= 1
            if self.contadores_tempo[node] <= 0:
                prob_remocao = self.multiplicadores_obstaculos[tipo]['prob_remocao']
                if random.random() < prob_remocao:
                    items_to_remove.append(('obstaculo', node))

        for edge, tipo in self.eventos.items():
            self.contadores_tempo[edge] -= 1
            if self.contadores_tempo[edge] <= 0:
                prob_remocao = self.multiplicadores_eventos[tipo]['prob_remocao']
                if random.random() < prob_remocao:
                    items_to_remove.append(('evento', edge))

        for item_type, item in items_to_remove:
            if item_type == 'obstaculo':
                del self.obstaculos[item]
                del self.contadores_tempo[item]
            else:
                del self.eventos[item]
                del self.contadores_tempo[item]

    def aplicar_efeitos(self):
        for node, tipo in self.obstaculos.items():
            densidade = self.grafo.nodes[node].get('densidade_populacional', 'normal')
            mult_densidade = self.multiplicadores_densidade[densidade]
            for edge in self.grafo.edges(node):
                self.grafo[edge[0]][edge[1]]['custo'] *= mult_densidade['custo']
                self.grafo[edge[0]][edge[1]]['tempo'] *= mult_densidade['tempo']

        for node, tipo in self.obstaculos.items():
            mult = self.multiplicadores_obstaculos[tipo]
            for edge in self.grafo.edges(node):
                self.grafo[edge[0]][edge[1]]['custo'] *= mult['custo']
                self.grafo[edge[0]][edge[1]]['tempo'] *= mult['tempo']

        for edge, tipo in self.eventos.items():
            mult = self.multiplicadores_eventos[tipo]
            self.grafo[edge[0]][edge[1]]['custo'] *= mult['custo']
            self.grafo[edge[0]][edge[1]]['tempo'] *= mult['tempo']

    def get_impacto_total(self, caminho: List[str]) -> Dict[str, float]:
        """Calcula o impacto total de eventos dinâmicos ao longo de um caminho."""
        if not caminho:
            return {'impacto_custo': 1.0, 'impacto_tempo': 1.0}  # Sem impacto para caminhos inválidos ou vazios

        impacto_custo = 1.0
        impacto_tempo = 1.0

        for node in caminho:
            if node in self.obstaculos:
                tipo = self.obstaculos[node]
                mult = self.multiplicadores_obstaculos[tipo]
                impacto_custo *= mult['custo']
                impacto_tempo *= mult['tempo']

        for i in range(len(caminho) - 1):
            edge = (caminho[i], caminho[i + 1])
            if edge in self.eventos:
                tipo = self.eventos[edge]
                mult = self.multiplicadores_eventos[tipo]
                impacto_custo *= mult['custo']
                impacto_tempo *= mult['tempo']

        return {
            'impacto_custo': impacto_custo,
            'impacto_tempo': impacto_tempo
        }

    def imprimir_status(self):
        print("\n=== Status de Obstáculos e Eventos ===")

        if self.obstaculos:
            print("\nObstáculos ativos:")
            for node, tipo in self.obstaculos.items():
                tempo_restante = self.contadores_tempo[node]
                print(f"- {node}: {tipo.value} (Tempo restante: {tempo_restante}h)")
        else:
            print("\nNenhum obstáculo ativo.")

        if self.eventos:
            print("\nEventos ativos:")
            for edge, tipo in self.eventos.items():
                tempo_restante = self.contadores_tempo[edge]
                print(f"- {edge[0]} -> {edge[1]}: {tipo.value} (Tempo restante: {tempo_restante}h)")
        else:
            print("\nNenhum evento ativo.")
