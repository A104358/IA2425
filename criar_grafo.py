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
            'Norte': [f'POSTO_NORTE_{i}' for i in range(1, 4)],
            'Centro': [f'POSTO_CENTRO_{i}' for i in range(1, 4)],
            'Lisboa': [f'POSTO_LISBOA_{i}' for i in range(1, 4)],
            'Alentejo': [f'POSTO_ALENTEJO_{i}' for i in range(1, 4)],
            'Algarve': [f'POSTO_ALGARVE_{i}' for i in range(1, 4)]
        }

        self.bases = {
            'BASE_LISBOA': (38.7223, -9.1393),
            'BASE_PORTO': (41.1579, -8.0291),
            'BASE_FARO': (37.0194, -7.9322),
            'BASE_COIMBRA': (40.2033, -7.2103)
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

    def gerar_coordenadas_regiao(self, regiao):
        bounds = self.regioes[regiao]
        lat = random.uniform(bounds['min_lat'], bounds['max_lat'])
        lon = random.uniform(bounds['min_lon'], bounds['max_lon'])
        return (lat, lon)

    def gerar_coordenadas_posto(self, regiao, id):
        bounds = self.regioes[regiao]
        lat = max(bounds['min_lat'], min((bounds['min_lat'] + bounds['max_lat']) / 2 + random.uniform(-0.5, 0.5), bounds['max_lat']))
        
        lon = bounds['min_lon'] + 0.1 + random.uniform(-0.1, 0.1)
        if id == 2:
            lon = bounds['max_lon'] - 0.1 + random.uniform(-0.1, 0.1)
        elif id == 3:
            lon = (bounds['min_lon'] + bounds['max_lon']) / 2 + random.uniform(-0.1, 0.1)
        return (lat, lon)

    def calcula_distancia(self, coord1, coord2):
        return hs.haversine(coord1, coord2, unit=Unit.KILOMETERS)

    def calcular_custo_tempo(self, coord1, coord2):
        dist = self.calcula_distancia(coord1, coord2)
        custo_base = dist * 0.08
        tempo_base = dist * 0.01
        custo = custo_base * random.uniform(0.8, 1.2)
        tempo = tempo_base * random.uniform(0.9, 1.3)
        return round(custo, 2), round(tempo, 3)


    def criar_grafo_grande(self, num_pontos_entrega=500):

        for base_id, coordenadas in self.bases.items():
            regiao = self._determinar_regiao(coordenadas)
            self.grafo.add_node(base_id, 
                              tipo='base',
                              coordenadas=coordenadas,
                              regiao=regiao)

        # Adicionar postos de reabastecimento
        for regiao, postos in self.postos_reabastecimento.items():
            
            for posto in postos:
                coords = self.gerar_coordenadas_posto(regiao, int(posto.split('_')[-1]))
                self.grafo.add_node(posto,
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
        
        # Conectar bases com bases e postos de abastecimento mais próximas
        bases = [n for n, d in nodes if d['tipo'] == 'base']
        
        for base1 in bases:
            coord_base1 = self.grafo.nodes[base1]['coordenadas']
            # Conectar com a base mais próxima
            bases_dist = [(b, self.calcula_distancia(coord_base1, self.grafo.nodes[b]['coordenadas']))
                        for b in bases if b != base1]
            bases_dist.sort(key=lambda x: x[1])
            
            base_mais_proxima, dist_proxima = bases_dist[0]
            custo, tempo = self.calcular_custo_tempo(coord_base1, self.grafo.nodes[base_mais_proxima]['coordenadas'])
            self.grafo.add_edge(base1, base_mais_proxima, custo=custo, tempo=tempo)
            self.grafo.add_edge(base_mais_proxima, base1, custo=custo, tempo=tempo)
            
            # Conectar com o posto de abastecimento mais próximo
            postos = [n for n, d in nodes if d['tipo'] == 'posto']
            postos_dist = [(p, self.calcula_distancia(coord_base1, self.grafo.nodes[p]['coordenadas']))
                        for p in postos]
            postos_dist.sort(key=lambda x: x[1])
            
            for posto, dist in postos_dist[:2]:
                custo, tempo = self.calcular_custo_tempo(coord_base1, self.grafo.nodes[posto]['coordenadas'])
                self.grafo.add_edge(base1, posto, custo=custo, tempo=tempo)
                self.grafo.add_edge(posto, base1, custo=custo, tempo=tempo)
                
        # Conectar todas as cidades com as bases mais próximas
        cidades = [n for n, d in nodes if d['tipo'] == 'hub']

        for cidade in cidades:
            coord_cidade = self.grafo.nodes[cidade]['coordenadas']
            # Conectar com a base mais próxima
            bases_dist = [(b, self.calcula_distancia(coord_cidade, self.grafo.nodes[b]['coordenadas']))
                        for b in bases]
            bases_dist.sort(key=lambda x: x[1])
            
            base_mais_proxima, dist_proxima = bases_dist[0]
            custo, tempo = self.calcular_custo_tempo(coord_cidade, self.grafo.nodes[base_mais_proxima]['coordenadas'])
            self.grafo.add_edge(cidade, base_mais_proxima, custo=custo, tempo=tempo)
            self.grafo.add_edge(base_mais_proxima, cidade, custo=custo, tempo=tempo)
        
        # Conectar todas as bases com os hubs mais próximos
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

        # conectar postos da mesma regiao entre si
        
        for regiao in self.regioes:
            postos_regiao = [n for n, d in nodes if d['tipo'] == 'posto' and d['regiao'] == regiao]
            for posto1 in postos_regiao:
                for posto2 in postos_regiao:
                    if posto1 != posto2:
                        coord1 = self.grafo.nodes[posto1]['coordenadas']
                        coord2 = self.grafo.nodes[posto2]['coordenadas']
                        custo, tempo = self.calcular_custo_tempo(coord1, coord2)
                        self.grafo.add_edge(posto1, posto2, custo=custo, tempo=tempo)
                                            
        # Conectar postos ao posto de outra regiao mais proximo
        postos = [n for n, d in nodes if d['tipo'] == 'posto']
        for posto in postos:
            regiao_posto = self.grafo.nodes[posto]['regiao']
            postos_regiao = [n for n, d in nodes if d['tipo'] == 'posto' and d['regiao'] == regiao_posto]
            postos_dist = [(p, self.calcula_distancia(self.grafo.nodes[posto]['coordenadas'], self.grafo.nodes[p]['coordenadas']))
                        for p in postos if p not in postos_regiao]
            postos_dist.sort(key=lambda x: x[1])
            
            posto_proximo, dist_proxima = postos_dist[0]
            custo, tempo = self.calcular_custo_tempo(self.grafo.nodes[posto]['coordenadas'], self.grafo.nodes[posto_proximo]['coordenadas'])
            self.grafo.add_edge(posto, posto_proximo, custo=custo, tempo=tempo)
            self.grafo.add_edge(posto_proximo, posto, custo=custo, tempo=tempo)
        
        # Conectar hubs da mesma região
        for regiao in self.regioes:
            hubs_regiao = [n for n, d in nodes if d['tipo'] == 'hub' and d['regiao'] == regiao]
            postos_regiao = [n for n, d in nodes if d['tipo'] == 'posto' and d['regiao'] == regiao]
            
            for hub in hubs_regiao:
                    
                # Conectar cada hub ao posto de reabastecimento mais proximo na sua região
                coord_hub = self.grafo.nodes[hub]['coordenadas']
                postos_dist = [(p, self.calcula_distancia(coord_hub, self.grafo.nodes[p]['coordenadas']))
                            for p in postos_regiao]
                postos_dist.sort(key=lambda x: x[1])
                
                posto_proximo1, dist_proxima1 = postos_dist[0]
                custo1, tempo1 = self.calcular_custo_tempo(coord_hub, self.grafo.nodes[posto_proximo1]['coordenadas'])
                self.grafo.add_edge(hub, posto_proximo1, custo=custo1, tempo=tempo1)
                self.grafo.add_edge(posto_proximo1, hub, custo=custo1, tempo=tempo1)
            
                # Conectar cada hub ao posto de reabastecimento mais proximo
                coord_hub = self.grafo.nodes[hub]['coordenadas']
                postos_dist = [(p, self.calcula_distancia(coord_hub, self.grafo.nodes[p]['coordenadas']))
                            for p in postos if p != posto_proximo1]
                postos_dist.sort(key=lambda x: x[1])
                
                posto_proximo2, dist_proxima2 = postos_dist[0]
                custo2, tempo2 = self.calcular_custo_tempo(coord_hub, self.grafo.nodes[posto_proximo2]['coordenadas'])
                self.grafo.add_edge(hub, posto_proximo2, custo=custo2, tempo=tempo2)
                self.grafo.add_edge(posto_proximo2, hub, custo=custo2, tempo=tempo2)

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
    grafo = pdg.criar_grafo_grande()
    
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