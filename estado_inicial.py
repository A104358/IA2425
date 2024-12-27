import random
import networkx as nx

# Definição do estado inicial adaptado para o novo formato de grafo
estado_inicial = {
    "veiculos": [
        {"id": 1, "tipo": "camião", "localizacao": "BASE_LISBOA", "capacidade": 500, "autonomia": 300, "combustivel": 300},
        {"id": 2, "tipo": "drone", "localizacao": "BASE_LISBOA", "capacidade": 50, "autonomia": 50, "combustivel": 50},
        {"id": 3, "tipo": "helicóptero", "localizacao": "BASE_LISBOA", "capacidade": 200, "autonomia": 150, "combustivel": 150},
    ],
    "zonas_afetadas": {},  # Será preenchido dinamicamente com pontos de entrega
    "suprimentos": {"alimentos": 1000, "água": 500}
}

def teste_objetivo(estado):
    """Verifica se todas as zonas prioritárias receberam suprimentos."""
    for zona, dados in estado["zonas_afetadas"].items():
        if not dados["suprida"]:
            return False
    return True

def mover_veiculo(veiculo, destino, grafo):
    """Adaptado para usar o novo formato de grafo."""
    origem = veiculo["localizacao"]
    if origem in grafo and destino in grafo:
        try:
            caminho = nx.shortest_path(grafo, origem, destino, weight='custo')
            custo_total = sum(grafo[caminho[i]][caminho[i+1]]['custo'] 
                            for i in range(len(caminho)-1))
            
            if veiculo["combustivel"] >= custo_total:
                veiculo["localizacao"] = destino
                veiculo["combustivel"] -= custo_total
                return True
        except nx.NetworkXNoPath:
            pass
    return False

def carregar_suprimentos(veiculo, tipo, quantidade, estado):
    """Mantido sem alterações pois não depende do formato do grafo."""
    if quantidade <= estado["suprimentos"][tipo] and quantidade <= veiculo["capacidade"]:
        estado["suprimentos"][tipo] -= quantidade
        veiculo[tipo] = veiculo.get(tipo, 0) + quantidade
        return True
    return False

def descarregar_suprimentos(veiculo, destino, estado):
    """Adaptado para trabalhar com o novo formato de zonas afetadas."""
    if destino in estado["zonas_afetadas"]:
        zona = estado["zonas_afetadas"][destino]
        for tipo, quantidade in veiculo.items():
            if tipo in zona["necessidades"] and quantidade > 0:
                entregue = min(zona["necessidades"][tipo], quantidade)
                zona["necessidades"][tipo] -= entregue
                veiculo[tipo] -= entregue
                if all(n == 0 for n in zona["necessidades"].values()):
                    zona["suprida"] = True
        return True
    return False

def calcular_custo(estado, veiculo, acao, destino=None, grafo=None):
    """Adaptado para usar o novo formato de grafo."""
    custo = 0
    if acao == "mover" and destino and grafo:
        try:
            caminho = nx.shortest_path(grafo, veiculo["localizacao"], destino, weight='custo')
            custo = sum(grafo[caminho[i]][caminho[i+1]]['custo'] 
                       for i in range(len(caminho)-1))
        except nx.NetworkXNoPath:
            return float('inf')
    elif acao in ["carregar", "descarregar"]:
        custo += 1
    return custo

def inicializar_zonas_afetadas(grafo):
    """Inicializa zonas afetadas baseado nos pontos de entrega do grafo."""
    zonas = {}
    for node, data in grafo.nodes(data=True):
        if data['tipo'] == 'entrega':
            zonas[node] = {
                "necessidades": {"alimentos": random.randint(50, 200), "água": random.randint(25, 100)},
                "populacao": random.randint(100, 1000),
                "prioridade": random.randint(1, 5),
                "suprida": False
            }
    return zonas

# Teste do estado inicial
if __name__ == "__main__":
    print("Estado inicial do problema:")
    print("\nVeículos disponíveis:")
    for veiculo in estado_inicial["veiculos"]:
        print(veiculo)
    
    print("\nZonas afetadas:")
    if estado_inicial["zonas_afetadas"]:
        for zona, dados in estado_inicial["zonas_afetadas"].items():
            print(f"Zona {zona}: {dados}")
    else:
        print("As zonas afetadas serão inicializadas quando o grafo for criado.")
    
    print("\nSuprimentos disponíveis:")
    print(estado_inicial["suprimentos"])
    
    print("\nNota: O grafo de conexões é agora gerido pela classe PortugalDistributionGraph")