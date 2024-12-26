from enum import Enum
import random
from typing import Dict, List, Set, Tuple
import networkx as nx

class TipoObstaculo(Enum):
    CONSTRUCAO = "construcao"
    ACIDENTE = "acidente"
    MANIFESTACAO = "manifestacao"
    EVENTO_CULTURAL = "evento_cultural"
    MANUTENCAO = "manutencao"
    DESMORONAMENTO = "desmoronamento"

class TipoEvento(Enum):
    TRAFEGO_INTENSO = "trafego_intenso"
    ACIDENTE_TRANSITO = "acidente_transito"
    OBRA_EMERGENCIAL = "obra_emergencial"
    EVENTO_ESPORTIVO = "evento_esportivo"
    PROTESTO = "protesto"
    DESFILE = "desfile"

class GestorEventos:
    def __init__(self, grafo: nx.DiGraph):
        self.grafo = grafo
        self.obstaculos = {}  # {node_id: TipoObstaculo}
        self.eventos = {}     # {(node1, node2): TipoEvento}
        
        # Multiplicadores de impacto para obstáculos
        self.multiplicadores_obstaculos = {
            TipoObstaculo.CONSTRUCAO: {
                'custo': 1.8,
                'tempo': 2.0,
                'duracao': (48, 168),  # horas (2-7 dias)
                'prob_remocao': 0.05
            },
            TipoObstaculo.ACIDENTE: {
                'custo': 2.0,
                'tempo': 2.5,
                'duracao': (2, 8),     # horas
                'prob_remocao': 0.3
            },
            TipoObstaculo.MANIFESTACAO: {
                'custo': 1.5,
                'tempo': 2.0,
                'duracao': (4, 12),    # horas
                'prob_remocao': 0.2
            },
            TipoObstaculo.EVENTO_CULTURAL: {
                'custo': 1.3,
                'tempo': 1.7,
                'duracao': (6, 24),    # horas
                'prob_remocao': 0.15
            },
            TipoObstaculo.MANUTENCAO: {
                'custo': 1.6,
                'tempo': 1.8,
                'duracao': (24, 72),   # horas
                'prob_remocao': 0.1
            },
            TipoObstaculo.DESMORONAMENTO: {
                'custo': 2.5,
                'tempo': 3.0,
                'duracao': (72, 240),  # horas (3-10 dias)
                'prob_remocao': 0.03
            }
        }
        
        # Multiplicadores de impacto para eventos
        self.multiplicadores_eventos = {
            TipoEvento.TRAFEGO_INTENSO: {
                'custo': 1.4,
                'tempo': 1.8,
                'duracao': (2, 6),     # horas
                'prob_remocao': 0.3
            },
            TipoEvento.ACIDENTE_TRANSITO: {
                'custo': 1.7,
                'tempo': 2.0,
                'duracao': (1, 4),     # horas
                'prob_remocao': 0.4
            },
            TipoEvento.OBRA_EMERGENCIAL: {
                'custo': 1.6,
                'tempo': 1.9,
                'duracao': (12, 48),   # horas
                'prob_remocao': 0.15
            },
            TipoEvento.EVENTO_ESPORTIVO: {
                'custo': 1.3,
                'tempo': 1.6,
                'duracao': (3, 8),     # horas
                'prob_remocao': 0.25
            },
            TipoEvento.PROTESTO: {
                'custo': 1.8,
                'tempo': 2.2,
                'duracao': (2, 10),    # horas
                'prob_remocao': 0.2
            },
            TipoEvento.DESFILE: {
                'custo': 1.5,
                'tempo': 1.7,
                'duracao': (4, 12),    # horas
                'prob_remocao': 0.25
            }
        }
        
        # Contadores de tempo para cada obstáculo/evento
        self.contadores_tempo = {}

    def adicionar_obstaculo_fixo(self, node_id: str):
        """Adiciona um obstáculo fixo a um nó específico"""
        if node_id in self.grafo and self.grafo.nodes[node_id]['tipo'] != 'base':
            tipo = random.choice(list(TipoObstaculo))
            self.obstaculos[node_id] = tipo
            duracao_min, duracao_max = self.multiplicadores_obstaculos[tipo]['duracao']
            self.contadores_tempo[node_id] = random.randint(duracao_min, duracao_max)
            return True
        return False

    def adicionar_evento_dinamico(self, node1: str, node2: str):
        """Adiciona um evento dinâmico a uma aresta específica"""
        if (node1, node2) in self.grafo.edges:
            tipo = random.choice(list(TipoEvento))
            self.eventos[(node1, node2)] = tipo
            duracao_min, duracao_max = self.multiplicadores_eventos[tipo]['duracao']
            self.contadores_tempo[(node1, node2)] = random.randint(duracao_min, duracao_max)
            return True
        return False

    def gerar_eventos_aleatorios(self, prob_novo_evento: float = 0.1):
        """Gera eventos aleatórios no grafo"""
        # Tentar adicionar novos obstáculos
        for node in self.grafo.nodes():
            if (node not in self.obstaculos and 
                random.random() < prob_novo_evento and 
                self.grafo.nodes[node]['tipo'] != 'base'):
                self.adicionar_obstaculo_fixo(node)
        
        # Tentar adicionar novos eventos
        for edge in self.grafo.edges():
            if (edge not in self.eventos and 
                random.random() < prob_novo_evento):
                self.adicionar_evento_dinamico(edge[0], edge[1])

    def atualizar_eventos(self):
        """Atualiza o estado dos eventos e obstáculos"""
        # Atualizar contadores e remover eventos/obstáculos expirados
        items_to_remove = []
        
        # Processar obstáculos
        for node, tipo in self.obstaculos.items():
            self.contadores_tempo[node] -= 1
            if self.contadores_tempo[node] <= 0:
                prob_remocao = self.multiplicadores_obstaculos[tipo]['prob_remocao']
                if random.random() < prob_remocao:
                    items_to_remove.append(('obstaculo', node))
        
        # Processar eventos
        for edge, tipo in self.eventos.items():
            self.contadores_tempo[edge] -= 1
            if self.contadores_tempo[edge] <= 0:
                prob_remocao = self.multiplicadores_eventos[tipo]['prob_remocao']
                if random.random() < prob_remocao:
                    items_to_remove.append(('evento', edge))
        
        # Remover itens marcados
        for item_type, item in items_to_remove:
            if item_type == 'obstaculo':
                del self.obstaculos[item]
                del self.contadores_tempo[item]
            else:  # evento
                del self.eventos[item]
                del self.contadores_tempo[item]

    def aplicar_efeitos(self):
        """Aplica os efeitos dos obstáculos e eventos ao grafo"""
        # Restaurar valores originais primeiro (assumindo que existem)
        if hasattr(self, 'valores_originais'):
            for (u, v), valores in self.valores_originais.items():
                self.grafo[u][v]['custo'] = valores['custo']
                self.grafo[u][v]['tempo'] = valores['tempo']
        else:
            # Armazenar valores originais na primeira execução
            self.valores_originais = {
                (u, v): {
                    'custo': data['custo'],
                    'tempo': data['tempo']
                }
                for u, v, data in self.grafo.edges(data=True)
            }
        
        # Aplicar efeitos dos obstáculos
        for node, tipo in self.obstaculos.items():
            mult = self.multiplicadores_obstaculos[tipo]
            # Afetar todas as arestas conectadas ao nó
            for edge in self.grafo.edges(node):
                self.grafo[edge[0]][edge[1]]['custo'] *= mult['custo']
                self.grafo[edge[0]][edge[1]]['tempo'] *= mult['tempo']
        
        # Aplicar efeitos dos eventos
        for edge, tipo in self.eventos.items():
            mult = self.multiplicadores_eventos[tipo]
            self.grafo[edge[0]][edge[1]]['custo'] *= mult['custo']
            self.grafo[edge[0]][edge[1]]['tempo'] *= mult['tempo']

    def imprimir_status(self):
        """Imprime o status atual dos obstáculos e eventos"""
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

    def get_impacto_total(self, caminho: List[str]) -> Dict[str, float]:
        """Calcula o impacto total dos obstáculos e eventos em um caminho"""
        impacto_custo = 1.0
        impacto_tempo = 1.0
        
        # Calcular impacto dos obstáculos
        for node in caminho:
            if node in self.obstaculos:
                tipo = self.obstaculos[node]
                mult = self.multiplicadores_obstaculos[tipo]
                impacto_custo *= mult['custo']
                impacto_tempo *= mult['tempo']
        
        # Calcular impacto dos eventos
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
