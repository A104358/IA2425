# Definição do estado inicial
estado_inicial = {
    "veiculos": [
        {"id": 1, "tipo": "caminhão", "localizacao": "base", "capacidade": 500, "autonomia": 300, "combustivel": 300},
        {"id": 2, "tipo": "drone", "localizacao": "base", "capacidade": 50, "autonomia": 50, "combustivel": 50},
        {"id": 3, "tipo": "helicóptero", "localizacao": "base", "capacidade": 200, "autonomia": 150, "combustivel": 150},
    ],
    "zonas_afetadas": {
        "A": {"necessidades": {"alimentos": 100, "agua": 50}, "populacao": 200, "prioridade": 3, "suprida": False},
        "B": {"necessidades": {"alimentos": 200, "agua": 100}, "populacao": 500, "prioridade": 5, "suprida": False},
        "C": {"necessidades": {"alimentos": 150, "agua": 80}, "populacao": 300, "prioridade": 4, "suprida": False},
    },
    "suprimentos": {"alimentos": 1000, "agua": 500},
    "grafo": {
        "nodos": ["base", "A", "B", "C"],
        "arestas": [
            {"origem": "base", "destino": "A", "custo": 50, "tempo": 30},
            {"origem": "base", "destino": "B", "custo": 70, "tempo": 45},
            {"origem": "A", "destino": "C", "custo": 60, "tempo": 40},
            {"origem": "B", "destino": "C", "custo": 50, "tempo": 35},
        ],
    }
}

# Teste objetivo: verificar se todas as zonas prioritárias receberam suprimentos
def teste_objetivo(estado):
    for zona, dados in estado["zonas_afetadas"].items():
        if not dados["suprida"]:
            return False
    return True

# Operadores (ações possíveis)
def mover_veiculo(veiculo, destino, estado):
    origem = veiculo["localizacao"]
    rota = next((aresta for aresta in estado["grafo"]["arestas"] if aresta["origem"] == origem and aresta["destino"] == destino), None)
    if rota and veiculo["combustivel"] >= rota["custo"]:
        veiculo["localizacao"] = destino
        veiculo["combustivel"] -= rota["custo"]
        return True
    return False

def carregar_suprimentos(veiculo, tipo, quantidade, estado):
    if quantidade <= estado["suprimentos"][tipo] and quantidade <= veiculo["capacidade"]:
        estado["suprimentos"][tipo] -= quantidade
        veiculo[tipo] = veiculo.get(tipo, 0) + quantidade
        return True
    return False

def descarregar_suprimentos(veiculo, destino, estado):
    if destino in estado["zonas_afetadas"]:
        zona = estado["zonas_afetadas"][destino]
        for tipo, quantidade in veiculo.items():
            if tipo in zona["necessidades"] and quantidade > 0:
                entregue = min(zona["necessidades"][tipo], quantidade)
                zona["necessidades"][tipo] -= entregue
                veiculo[tipo] -= entregue
                if zona["necessidades"][tipo] == 0:
                    zona["suprida"] = True
        return True
    return False

# Cálculo do custo da solução
def calcular_custo(estado, veiculo, acao, destino=None):
    custo = 0
    if acao == "mover" and destino:
        rota = next((aresta for aresta in estado["grafo"]["arestas"] if aresta["origem"] == veiculo["localizacao"] and aresta["destino"] == destino), None)
        if rota:
            custo += rota["custo"]
    elif acao in ["carregar", "descarregar"]:
        custo += 1  # Pode ser ajustado para incluir outros fatores
    return custo

# Exibir o estado inicial
if __name__ == "__main__":
    print("Estado inicial do problema:")
    print("Veículos disponíveis:")
    for veiculo in estado_inicial["veiculos"]:
        print(veiculo)
    
    print("\nZonas afetadas:")
    for zona, dados in estado_inicial["zonas_afetadas"].items():
        print(f"Zona {zona}: {dados}")
    
    print("\nSuprimentos disponíveis:")
    print(estado_inicial["suprimentos"])
    
    print("\nGrafo de conexões:")
    for aresta in estado_inicial["grafo"]["arestas"]:
        print(aresta)
