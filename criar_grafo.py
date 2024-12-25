import networkx as nx
import matplotlib.pyplot as plt
import random
import math

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

    def gerar_coordenadas_regiao(self, regiao):
        bounds = self.regioes[regiao]
        lat = random.uniform(bounds['min_lat'], bounds['max_lat'])
        lon = random.uniform(bounds['min_lon'], bounds['max_lon'])
        return (lat, lon)

    def calcular_custo_tempo(self, coord1, coord2):
        dist = math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)
        custo_base = dist * 100
        tempo_base = dist * 60
        custo = custo_base * random.uniform(0.8, 1.2)
        tempo = tempo_base * random.uniform(0.9, 1.3)
        return round(custo, 2), round(tempo, 2)

    def criar_grafo_grande(self, num_pontos_entrega=500):
        # Adicionar base principal em Lisboa
        self.grafo.add_node('BASE_LISBOA', 
                           tipo='base',
                           coordenadas=(38.7223, -9.1393),
                           regiao='Lisboa')

        # Adicionar principais cidades como hubs
        for regiao, cidades in self.cidades_principais.items():
            for cidade in cidades:
                coords = self.gerar_coordenadas_regiao(regiao)
                self.grafo.add_node(cidade,
                                  tipo='hub',
                                  coordenadas=coords,
                                  regiao=regiao)

        # Adicionar pontos de entrega
        for i in range(num_pontos_entrega):
            regiao = random.choice(list(self.regioes.keys()))
            coords = self.gerar_coordenadas_regiao(regiao)
            node_id = f'PE_{i+1}'
            self.grafo.add_node(node_id,
                              tipo='entrega',
                              coordenadas=coords,
                              regiao=regiao)

        self._criar_conexoes()
        return self.grafo

    def _criar_conexoes(self):
        nodes = list(self.grafo.nodes(data=True))
        
        # Conectar BASE_LISBOA com todos os hubs
        hubs = [n for n, d in nodes if d['tipo'] == 'hub']
        for hub in hubs:
            coord_base = self.grafo.nodes['BASE_LISBOA']['coordenadas']
            coord_hub = self.grafo.nodes[hub]['coordenadas']
            custo, tempo = self.calcular_custo_tempo(coord_base, coord_hub)
            
            self.grafo.add_edge('BASE_LISBOA', hub, custo=custo, tempo=tempo)
            self.grafo.add_edge(hub, 'BASE_LISBOA', custo=custo, tempo=tempo)

        # Conectar hubs da mesma região
        for regiao in self.regioes:
            hubs_regiao = [n for n, d in nodes if d['tipo'] == 'hub' and d['regiao'] == regiao]
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
        
        # Desenhar arestas com menor opacidade e linhas mais finas
        nx.draw_networkx_edges(self.grafo, pos, alpha=0.1, edge_color='gray', width=0.5)
        
        # Desenhar nodos por tipo com tamanhos ajustados e cores mais distintas
        nx.draw_networkx_nodes(self.grafo, pos, nodelist=bases, node_color='red',
                             node_size=800, alpha=1.0, label='Base')
        nx.draw_networkx_nodes(self.grafo, pos, nodelist=hubs, node_color='blue',
                             node_size=400, alpha=0.8, label='Hubs')
        nx.draw_networkx_nodes(self.grafo, pos, nodelist=entregas, node_color='lightgreen',
                             node_size=50, alpha=0.3, label='Pontos de Entrega')
        
        if mostrar_labels:
            # Mostrar labels apenas para base e hubs, com melhor posicionamento
            labels = {node: node for node in bases + hubs}
            nx.draw_networkx_labels(self.grafo, pos, labels, font_size=8, font_weight='bold')
        
        plt.title("Rede de Distribuição em Portugal", pad=20, fontsize=14, fontweight='bold')
        
        # Definir posição específica para a legenda para evitar o warning
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Ajustar os limites do plot para acomodar a legenda
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
    
    # Contar nodos por tipo
    tipos = {}
    for node in grafo.nodes(data=True):
        tipo = node[1]['tipo']
        tipos[tipo] = tipos.get(tipo, 0) + 1
    
    # Visualizar
    plt = pdg.visualizar_grafo(mostrar_labels=True)
    plt.show()

if __name__ == "__main__":
    main()