import random
from enum import Enum
import networkx as nx
from typing import Dict, List, Tuple

class CondicaoMeteorologica(Enum):
    NORMAL = "normal"
    CHUVA_LEVE = "chuva_leve"
    CHUVA_FORTE = "chuva_forte"
    NEVOEIRO = "nevoeiro"
    TEMPESTADE = "tempestade"
    NEVE = "neve"

class GestorMeteorologico:
    def __init__(self, grafo: nx.DiGraph):
        self.grafo = grafo
        self.condicoes_por_regiao = {}
        self.multiplicadores = {
            CondicaoMeteorologica.NORMAL: {
                'custo': 1.0,
                'tempo': 1.0,
                'bloqueio': 0.0
            },
            CondicaoMeteorologica.CHUVA_LEVE: {
                'custo': 1.1,
                'tempo': 1.1,
                'bloqueio': 0.05
            },
            CondicaoMeteorologica.CHUVA_FORTE: {
                'custo': 1.1,
                'tempo': 1.3,
                'bloqueio': 0.15
            },
            CondicaoMeteorologica.NEVOEIRO: {
                'custo': 1.3,
                'tempo': 1.8,
                'bloqueio': 0.1
            },
            CondicaoMeteorologica.TEMPESTADE: {
                'custo': 1.7,
                'tempo': 2,
                'bloqueio': 0.25
            },
            CondicaoMeteorologica.NEVE: {
                'custo': 1.8,
                'tempo': 1.8,
                'bloqueio': 0.2
            }
        }
        self.valores_originais = {
            (u, v): {
                'custo': data['custo'],
                'tempo': data['tempo']
            }
            for u, v, data in self.grafo.edges(data=True)
        }
        self.inicializar_condicoes()

    def inicializar_condicoes(self):
        """Inicializa todas as regiões com condição normal"""
        regioes = set(nx.get_node_attributes(self.grafo, 'regiao').values())
        self.condicoes_por_regiao = {
            regiao: CondicaoMeteorologica.NORMAL for regiao in regioes
        }
        self.atualizar_grafo()

    def atualizar_grafo(self):
        """Atualiza o grafo com base nas condições meteorológicas"""
        for (u, v), valores in self.valores_originais.items():
            self.grafo[u][v]['custo'] = valores['custo']
            self.grafo[u][v]['tempo'] = valores['tempo']
            self.grafo[u][v]['bloqueado'] = False

            regiao = self.grafo.nodes[u]['regiao']
            condicao = self.condicoes_por_regiao[regiao]
            multiplicadores = self.multiplicadores[condicao]

            self.grafo[u][v]['custo'] *= multiplicadores['custo']
            self.grafo[u][v]['tempo'] *= multiplicadores['tempo']

            if random.random() < multiplicadores['bloqueio']:
                self.grafo[u][v]['bloqueado'] = True
                self.grafo[u][v]['custo'] = float('inf')
                self.grafo[u][v]['tempo'] = float('inf')

    def atualizar_condicoes(self):
        """Atualiza as condições meteorológicas para cada região"""
        for regiao in self.condicoes_por_regiao:
            condicao_atual = self.condicoes_por_regiao[regiao]
            nova_condicao = self.gerar_nova_condicao(condicao_atual)
            self.condicoes_por_regiao[regiao] = nova_condicao
        
        self.atualizar_grafo()

    def gerar_nova_condicao(self, condicao_atual: CondicaoMeteorologica) -> CondicaoMeteorologica:
        """Gera uma nova condição meteorológica baseada na atual"""
        probabilidades = {
            CondicaoMeteorologica.NORMAL: {
                CondicaoMeteorologica.NORMAL: 0.5,
                CondicaoMeteorologica.CHUVA_LEVE: 0.3,
                CondicaoMeteorologica.NEVOEIRO: 0.2
            },
            CondicaoMeteorologica.CHUVA_LEVE: {
                CondicaoMeteorologica.NORMAL: 0.2,
                CondicaoMeteorologica.CHUVA_LEVE: 0.3,
                CondicaoMeteorologica.CHUVA_FORTE: 0.3,
                CondicaoMeteorologica.NEVOEIRO: 0.2
            },
            CondicaoMeteorologica.CHUVA_FORTE: {
                CondicaoMeteorologica.CHUVA_LEVE: 0.3,
                CondicaoMeteorologica.CHUVA_FORTE: 0.3,
                CondicaoMeteorologica.TEMPESTADE: 0.4
            },
            CondicaoMeteorologica.TEMPESTADE: {
                CondicaoMeteorologica.CHUVA_FORTE: 0.4,
                CondicaoMeteorologica.TEMPESTADE: 0.4,
                CondicaoMeteorologica.NORMAL: 0.2
            },
            CondicaoMeteorologica.NEVOEIRO: {
                CondicaoMeteorologica.NEVOEIRO: 0.4,
                CondicaoMeteorologica.NORMAL: 0.4,
                CondicaoMeteorologica.CHUVA_LEVE: 0.2
            }
        }
        opcoes = list(probabilidades[condicao_atual].keys())
        pesos = list(probabilidades[condicao_atual].values())
        return random.choices(opcoes, weights=pesos)[0]
    
    def verificar_condicoes_adversas(self, rota: List[str]) -> bool:
        """Verifica se há condições meteorológicas adversas em qualquer ponto da rota."""
        for node in rota:
            regiao = self.grafo.nodes[node].get('regiao')
            if not regiao:
                continue  # Ignorar nós sem região definida
            
            condicao = self.condicoes_por_regiao.get(regiao, CondicaoMeteorologica.NORMAL)
            if condicao in [CondicaoMeteorologica.CHUVA_FORTE, CondicaoMeteorologica.TEMPESTADE, CondicaoMeteorologica.NEVE]:
                return True  # Condições adversas detectadas

        return False  # Nenhuma condição adversa encontrada

