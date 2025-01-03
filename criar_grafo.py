import random
import networkx as nx
import matplotlib.pyplot as plt
import math
from eventos_dinamicos import TipoObstaculo
from condicoes_meteorologicas import CondicaoMeteorologica, GestorMeteorologico
from limitacoes_geograficas import TipoTerreno
import haversine as hs   
from haversine import Unit

class PortugalDistributionGraph:
    def __init__(self):
        self.grafo = nx.DiGraph()
        self.regioes = {
            'Norte': {'min_lat': 41.0, 'max_lat': 42.0, 'min_lon': -8.5, 'max_lon': -6.5},
            'Centro': {'min_lat': 40.0, 'max_lat': 41.0, 'min_lon': -8.5, 'max_lon': -6.5},
            'Lisboa': {'min_lat': 38.5, 'max_lat': 39.5, 'min_lon': -9.5, 'max_lon': -8.5},
            'Alentejo': {'min_lat': 37.5, 'max_lat': 38.5, 'min_lon': -8.5, 'max_lon': -7.0},
            'Algarve': {'min_lat': 37.0, 'max_lat': 37.5, 'min_lon': -8.5, 'max_lon': -7.0}
        }
        
        self.cidades_principais = {
            'Norte': ['Porto', 'Braga', 'Guimarães', 'Viana do Castelo', 'Vila Real', 'Bragança'],
            'Centro': ['Coimbra', 'Aveiro', 'Viseu', 'Leiria', 'Castelo Branco', 'Guarda'],
            'Lisboa': ['Lisboa', 'Sintra', 'Cascais', 'Amadora', 'Loures', 'Torres Vedras'],
            'Alentejo': ['Évora', 'Beja', 'Portalegre', 'Elvas', 'Sines', 'Estremoz'],
            'Algarve': ['Faro', 'Portimão', 'Albufeira', 'Lagos', 'Tavira', 'Loulé']
        }

        self.postos_reabastecimento = {
            'Norte': 'POSTO_NORTE',
            'Centro': 'POSTO_CENTRO',
            'Lisboa': 'POSTO_LISBOA',
            'Alentejo': 'POSTO_ALENTEJO',
            'Algarve': 'POSTO_ALGARVE'
        }

        self.bases = {
            'BASE_LISBOA': (38.7223, -9.1393),
            'BASE_PORTO': (41.1579, -8.6291),
            'BASE_FARO': (37.0194, -7.9322),
            'BASE_COIMBRA': (40.2033, -8.4103)
        }

    def _determinar_regiao(self, coordenadas):
        """
        Determina a região de Portugal a que pertencem as coordenadas dadas.
        
        Args:
            coordenadas (tuple): Par de coordenadas (latitude, longitude)
            
        Returns:
            str: Nome da região ou None se não pertencer a nenhuma
        """
        lat, lon = coordenadas
        for regiao, bounds in self.regioes.items():
            if (bounds['min_lat'] <= lat <= bounds['max_lat'] and 
                bounds['min_lon'] <= lon <= bounds['max_lon']):
                return regiao
                
        # Se não encontrar uma região exata, determinar a região mais próxima
        min_dist = float('inf')
        closest_region = None
        
        for regiao, bounds in self.regioes.items():
            # Calcular o centro da região
            region_center = (
                (bounds['min_lat'] + bounds['max_lat']) / 2,
                (bounds['min_lon'] + bounds['max_lon']) / 2
            )
            
            # Calcular distância até o centro da região
            dist = self.calcula_distancia(coordenadas, region_center)
            
            if dist < min_dist:
                min_dist = dist
                closest_region = regiao
        
        return closest_region

    # Rest of the class methods remain the same
    def gerar_coordenadas_regiao(self, regiao):
        bounds = self.regioes[regiao]
        lat = random.uniform(bounds['min_lat'], bounds['max_lat'])
        lon = random.uniform(bounds['min_lon'], bounds['max_lon'])
        return (lat, lon)

    def gerar_coordenadas_posto(self, regiao):
        bounds = self.regioes[regiao]
        lat = (bounds['min_lat'] + bounds['max_lat']) / 2
        lon = bounds['max_lon'] + 0.2
        return (lat, lon)

    def calcula_distancia(self, coord1, coord2):
        return hs.haversine(coord1, coord2, unit=Unit.KILOMETERS)

    def calcular_custo_tempo(self, coord1, coord2):
        dist = self.calcula_distancia(coord1, coord2)
        custo_base = dist * 0.08
        tempo_base = dist * 0.0166
        custo = custo_base * random.uniform(0.8, 1.2)
        tempo = tempo_base * random.uniform(0.9, 1.3)
        print(f"{coord1 = } {coord2 = } Distância: {dist:.2f} km, Custo: {custo:.2f}, Tempo: {tempo:.2f}")
        return round(custo, 2), round(tempo, 2)


    def criar_grafo_grande(self, num_pontos_entrega=500):
        # Adicionar base principal em Lisboa
        self.grafo.add_node('BASE_LISBOA', 
                           tipo='base',
                           coordenadas=(38.7223, -9.1393),
                           regiao='Lisboa')

        # Adicionar postos de reabastecimento
        for regiao, posto_id in self.postos_reabastecimento.items():
            coords = self.gerar_coordenadas_posto(regiao)
            self.grafo.add_node(posto_id,
                              tipo='posto',
                              coordenadas=coords,
                              regiao=regiao)

        # Adicionar principais cidades como hubs
        for regiao, cidades in self.cidades_principais.items():
            for cidade in cidades:
                coords = self.gerar_coordenadas_regiao(regiao)
                self.grafo.add_node(cidade,
                                  tipo='hub',
                                  coordenadas=coords,
                                  regiao=regiao,
                                  tipo_terreno=random.choice(list(TipoTerreno)))
        
        for base_id, coordenadas in self.bases.items():
            regiao = self._determinar_regiao(coordenadas)
            self.grafo.add_node(base_id, 
                              tipo='base',
                              coordenadas=coordenadas,
                              regiao=regiao)


        # Adicionar pontos de entrega
        for i in range(num_pontos_entrega):
            regiao = random.choice(list(self.regioes.keys()))
            coords = self.gerar_coordenadas_regiao(regiao)
            densidade_populacional = random.choices(['alta', 'normal', 'baixa'], weights=[0.4, 0.4, 0.2])[0]
            node_id = f'PE_{i+1}'
            self.grafo.add_node(node_id,
                              tipo='entrega',
                              coordenadas=coords,
                              regiao=regiao,
                              densidade_populacional=densidade_populacional,
                              tipo_terreno=random.choice(list(TipoTerreno)))

        self._criar_conexoes()
        return self.grafo

    def _criar_conexoes(self):
        nodes = list(self.grafo.nodes(data=True))
        
        # Conectar todas as bases com os hubs mais próximos
        bases = [n for n, d in nodes if d['tipo'] == 'base']
        hubs = [n for n, d in nodes if d['tipo'] == 'hub']
        
        for base in bases:
            coord_base = self.grafo.nodes[base]['coordenadas']
            # Conectar com os 3 hubs mais próximos
            hubs_dist = [(h, self.calcula_distancia(coord_base, self.grafo.nodes[h]['coordenadas']))
                        for h in hubs]
            hubs_dist.sort(key=lambda x: x[1])
            
            for hub, _ in hubs_dist[:3]:
                coord_hub = self.grafo.nodes[hub]['coordenadas']
                custo, tempo = self.calcular_custo_tempo(coord_base, coord_hub)
                self.grafo.add_edge(base, hub, custo=custo, tempo=tempo)
                self.grafo.add_edge(hub, base, custo=custo, tempo=tempo)

        # Conectar hubs da mesma região
        for regiao in self.regioes:
            hubs_regiao = [n for n, d in nodes if d['tipo'] == 'hub' and d['regiao'] == regiao]
            posto_regiao = self.postos_reabastecimento[regiao]
            
            # Conectar cada hub ao posto de reabastecimento da sua região
            for hub in hubs_regiao:
                coord_hub = self.grafo.nodes[hub]['coordenadas']
                coord_posto = self.grafo.nodes[posto_regiao]['coordenadas']
                custo, tempo = self.calcular_custo_tempo(coord_hub, coord_posto)
                self.grafo.add_edge(hub, posto_regiao, custo=custo, tempo=tempo)
                self.grafo.add_edge(posto_regiao, hub, custo=custo, tempo=tempo)
            
            # Conectar hubs entre si
            for hub1 in hubs_regiao:
                for hub2 in hubs_regiao:
                    if hub1 != hub2:
                        coord1 = self.grafo.nodes[hub1]['coordenadas']
                        coord2 = self.grafo.nodes[hub2]['coordenadas']
                        custo, tempo = self.calcular_custo_tempo(coord1, coord2)
                        self.grafo.add_edge(hub1, hub2, custo=custo, tempo=tempo)

        # Conectar pontos de entrega aos hubs mais próximos
        pontos_entrega = [n for n, d in nodes if d['tipo'] == 'entrega']
        for pe in pontos_entrega:
            regiao_pe = self.grafo.nodes[pe]['regiao']
            hubs_regiao = [n for n, d in nodes if d['tipo'] == 'hub' and d['regiao'] == regiao_pe]
            
            coord_pe = self.grafo.nodes[pe]['coordenadas']
            hubs_dist = [(h, math.sqrt((coord_pe[0] - self.grafo.nodes[h]['coordenadas'][0])**2 + 
                                     (coord_pe[1] - self.grafo.nodes[h]['coordenadas'][1])**2))
                        for h in hubs_regiao]
            hubs_dist.sort(key=lambda x: x[1])
            
            for hub, _ in hubs_dist[:2]:
                coord_hub = self.grafo.nodes[hub]['coordenadas']
                custo, tempo = self.calcular_custo_tempo(coord_pe, coord_hub)
                self.grafo.add_edge(hub, pe, custo=custo, tempo=tempo)
                self.grafo.add_edge(pe, hub, custo=custo, tempo=tempo)

    def visualizar_grafo(self, mostrar_labels=False):
        plt.figure(figsize=(15, 10))
        
        # Usar coordenadas geográficas para posicionamento
        pos = {node: (data['coordenadas'][1], data['coordenadas'][0]) 
               for node, data in self.grafo.nodes(data=True)}
        
        # Separar nodos por tipo
        bases = [node for node, attr in self.grafo.nodes(data=True) if attr['tipo'] == 'base']
        hubs = [node for node, attr in self.grafo.nodes(data=True) if attr['tipo'] == 'hub']
        entregas = [node for node, attr in self.grafo.nodes(data=True) if attr['tipo'] == 'entrega']
        postos = [node for node, attr in self.grafo.nodes(data=True) if attr['tipo'] == 'posto']
        
        # Desenhar arestas com menor opacidade e linhas mais finas
        nx.draw_networkx_edges(self.grafo, pos, alpha=0.1, edge_color='gray', width=0.5)
        
        # Desenhar nodos por tipo com tamanhos ajustados e cores mais distintas
        nx.draw_networkx_nodes(self.grafo, pos, nodelist=bases, node_color='red',
                             node_size=800, alpha=1.0, label='Base')
        nx.draw_networkx_nodes(self.grafo, pos, nodelist=hubs, node_color='blue',
                             node_size=400, alpha=0.8, label='Hubs')
        nx.draw_networkx_nodes(self.grafo, pos, nodelist=entregas, node_color='lightgreen',
                             node_size=50, alpha=0.3, label='Pontos de Entrega')
        nx.draw_networkx_nodes(self.grafo, pos, nodelist=postos, node_color='orange',
                             node_size=600, alpha=0.9, label='Postos de Reabastecimento')
        
        if mostrar_labels:
            # Mostrar labels para base, hubs e postos
            labels = {node: node for node in bases + hubs + postos}
            nx.draw_networkx_labels(self.grafo, pos, labels, font_size=8, font_weight='bold')
        
        plt.title("Rede de Distribuição em Portugal", pad=20, fontsize=14, fontweight='bold')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.subplots_adjust(right=0.85)
        plt.axis('off')
        return plt

def main():
    # Criar e configurar o grafo
    pdg = PortugalDistributionGraph()
    grafo = pdg.criar_grafo_grande(num_pontos_entrega=500)
    
    # Imprimir estatísticas
    print(f"Estatísticas do Grafo:")
    print(f"Número total de nodos: {grafo.number_of_nodes()}")
    print(f"Número total de arestas: {grafo.number_of_edges()}")
    print(f"Grau médio: {sum(dict(grafo.degree()).values())/grafo.number_of_nodes():.2f}")
    
    # Visualizar
    plt = pdg.visualizar_grafo(mostrar_labels=True)
    plt.show()

if __name__ == "__main__":
    main()