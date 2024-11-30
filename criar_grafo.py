import networkx as nx
import matplotlib.pyplot as plt

# Importar o estado inicial
from estado_inicial import estado_inicial

# Criar o grafo
def criar_grafo(estado):
    grafo = nx.DiGraph()  # Grafo direcionado para representar rotas

    # Adicionar nós (zonas e base)
    for nodo in estado["grafo"]["nodos"]:
        grafo.add_node(nodo, tipo="zona" if nodo != "base" else "base")

    # Adicionar arestas com pesos (custo, tempo e condição geográfica)
    for aresta in estado["grafo"]["arestas"]:
        custo = aresta["custo"]
        tempo = aresta["tempo"]
        # Simulação de condição geográfica: aumentar custo se for zona montanhosa
        condicao_geografica = 1.2 if aresta["destino"] in ["A", "C"] else 1.0
        custo_ajustado = custo * condicao_geografica
        grafo.add_edge(
            aresta["origem"],
            aresta["destino"],
            custo=custo_ajustado,
            tempo=tempo
        )
    
    return grafo

# Adicionar informações dos veículos
def exibir_informacoes_veiculos(estado):
    print("\nInformações dos Veículos:")
    for veiculo in estado["veiculos"]:
        print(f"ID: {veiculo['id']}, Tipo: {veiculo['tipo']}, "
              f"Localização: {veiculo['localizacao']}, Capacidade: {veiculo['capacidade']}, "
              f"Autonomia: {veiculo['autonomia']}, Combustível: {veiculo['combustivel']}")

# Visualizar o grafo
def visualizar_grafo(grafo):
    pos = nx.spring_layout(grafo)
    nx.draw(grafo, pos, with_labels=True, node_size=2000, node_color="lightblue", font_size=10, font_weight="bold")
    edge_labels = nx.get_edge_attributes(grafo, "custo")
    nx.draw_networkx_edge_labels(grafo, pos, edge_labels=edge_labels, font_size=8)
    plt.title("Grafo de Zonas de Entrega com Pesos (Custos)")
    plt.show()

# Função principal
if __name__ == "__main__":
    grafo = criar_grafo(estado_inicial)
    print("Nós do Grafo:", grafo.nodes(data=True))
    print("Arestas do Grafo:")
    for u, v, atributos in grafo.edges(data=True):
        print(f"{u} -> {v}: {atributos}")

    exibir_informacoes_veiculos(estado_inicial)
    visualizar_grafo(grafo)
