# Definição do estado inicial
estado_inicial = {
    "veiculos": [
        {"id": 1, "tipo": "caminhão", "localizacao": "base", "capacidade": 500, "autonomia": 300},
        {"id": 2, "tipo": "drone", "localizacao": "base", "capacidade": 50, "autonomia": 50},
        {"id": 3, "tipo": "helicóptero", "localizacao": "base", "capacidade": 200, "autonomia": 150},
    ],
    "zonas_afetadas": {
        "A": {"necessidades": {"alimentos": 100, "agua": 50}, "populacao": 200, "prioridade": 3, "acessivel": True},
        "B": {"necessidades": {"alimentos": 200, "agua": 100}, "populacao": 500, "prioridade": 5, "acessivel": True},
        "C": {"necessidades": {"alimentos": 150, "agua": 80}, "populacao": 300, "prioridade": 4, "acessivel": False},
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
