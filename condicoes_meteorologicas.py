import random
from enum import Enum
import networkx as nx
from typing import Dict, List, Set, Tuple

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
                'custo': 1.2,
                'tempo': 1.3,
                'bloqueio': 0.05
            },
            CondicaoMeteorologica.CHUVA_FORTE: {
                'custo': 1.5,
                'tempo': 1.7,
                'bloqueio': 0.15
            },
            CondicaoMeteorologica.NEVOEIRO: {
                'custo': 1.3,
                'tempo': 1.8,
                'bloqueio': 0.1
            },
            CondicaoMeteorologica.TEMPESTADE: {
                'custo': 2.0,
                'tempo': 2.5,
                'bloqueio': 0.25
            },
            CondicaoMeteorologica.NEVE: {
                'custo': 1.8,
                'tempo': 2.2,
                'bloqueio': 0.2
            }
        }
        
        # Armazenar valores originais das arestas
        self.valores_originais = {
            (u, v): {
                'custo': data['custo'],
                'tempo': data['tempo']
            }
            for u, v, data in self.grafo.edges(data=True)
        }
        
        # Inicializar condições normais em todas as regiões
        self.inicializar_condicoes()

    def inicializar_condicoes(self):
        """Inicializa todas as regiões com condição normal"""
        regioes = set(nx.get_node_attributes(self.grafo, 'regiao').values())
        self.condicoes_por_regiao = {
            regiao: CondicaoMeteorologica.NORMAL for regiao in regioes
        }
        self.atualizar_grafo()

    def gerar_nova_condicao(self, condicao_atual: CondicaoMeteorologica) -> CondicaoMeteorologica:
        """Gera uma nova condição meteorológica baseada na atual com probabilidades ajustadas"""
        probabilidades = {
            CondicaoMeteorologica.NORMAL: {
                CondicaoMeteorologica.NORMAL: 0.5,  # Reduzido de 0.7
                CondicaoMeteorologica.CHUVA_LEVE: 0.3,  # Aumentado de 0.2
                CondicaoMeteorologica.NEVOEIRO: 0.2  # Aumentado de 0.1
            },
            CondicaoMeteorologica.CHUVA_LEVE: {
                CondicaoMeteorologica.NORMAL: 0.2,  # Reduzido de 0.3
                CondicaoMeteorologica.CHUVA_LEVE: 0.3,  # Reduzido de 0.4
                CondicaoMeteorologica.CHUVA_FORTE: 0.3,  # Aumentado de 0.2
                CondicaoMeteorologica.NEVOEIRO: 0.2  # Aumentado de 0.1
            },
            CondicaoMeteorologica.CHUVA_FORTE: {
                CondicaoMeteorologica.CHUVA_LEVE: 0.3,  # Reduzido de 0.4
                CondicaoMeteorologica.CHUVA_FORTE: 0.3,
                CondicaoMeteorologica.TEMPESTADE: 0.4  # Aumentado de 0.3
            },
            CondicaoMeteorologica.TEMPESTADE: {
                CondicaoMeteorologica.CHUVA_FORTE: 0.4,  # Reduzido de 0.5
                CondicaoMeteorologica.TEMPESTADE: 0.4,  # Aumentado de 0.3
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


    def atualizar_condicoes(self):
        """Atualiza as condições meteorológicas para cada região"""
        for regiao in self.condicoes_por_regiao:
            condicao_atual = self.condicoes_por_regiao[regiao]
            nova_condicao = self.gerar_nova_condicao(condicao_atual)
            self.condicoes_por_regiao[regiao] = nova_condicao
        
        self.atualizar_grafo()

    def atualizar_grafo(self):
        """Atualiza o grafo com base nas condições meteorológicas atuais"""
        # Restaurar valores originais primeiro
        for (u, v), valores in self.valores_originais.items():
            self.grafo[u][v]['custo'] = valores['custo']
            self.grafo[u][v]['tempo'] = valores['tempo']
            self.grafo[u][v]['bloqueado'] = False

        # Aplicar efeitos das condições meteorológicas
        for u, v, data in self.grafo.edges(data=True):
            # Determinar a região da aresta (usando a região do nodo de origem)
            regiao = self.grafo.nodes[u]['regiao']
            condicao = self.condicoes_por_regiao[regiao]
            multiplicadores = self.multiplicadores[condicao]

            # Aplicar multiplicadores
            self.grafo[u][v]['custo'] *= multiplicadores['custo']
            self.grafo[u][v]['tempo'] *= multiplicadores['tempo']

            # Verificar se a aresta deve ser bloqueada
            if random.random() < multiplicadores['bloqueio']:
                self.grafo[u][v]['bloqueado'] = True
                # Usar valores muito altos para evitar o uso de arestas bloqueadas
                self.grafo[u][v]['custo'] = float('inf')
                self.grafo[u][v]['tempo'] = float('inf')

    def get_condicao_regiao(self, regiao: str) -> CondicaoMeteorologica:
        """Retorna a condição meteorológica atual de uma região"""
        return self.condicoes_por_regiao.get(regiao)

    def get_arestas_bloqueadas(self) -> List[Tuple[str, str]]:
        """Retorna lista de arestas bloqueadas"""
        return [(u, v) for u, v, data in self.grafo.edges(data=True)
                if data.get('bloqueado', False)]

    def imprimir_status(self):
        """Imprime o status atual das condições meteorológicas"""
        print("\n=== Status Meteorológico ===")
        for regiao, condicao in self.condicoes_por_regiao.items():
            print(f"Região {regiao}: {condicao.value}")
        
        arestas_bloqueadas = self.get_arestas_bloqueadas()
        if arestas_bloqueadas:
            print("\nArestas bloqueadas:")
            for u, v in arestas_bloqueadas:
                print(f"- {u} -> {v}")
        else:
            print("\nNenhuma aresta bloqueada.")
