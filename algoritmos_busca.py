import time
import networkx as nx
from estado_inicial import estado_inicial
from criar_grafo import PortugalDistributionGraph


def calcular_heuristica(grafo, objetivo):
    """
    Calcula uma heurística baseada no custo mínimo entre os nodos.
    """
    heuristica = {}
    for nodo in grafo.nodes():
        try:
            # Usa o algoritmo de Dijkstra para encontrar o caminho mais curto
            caminho = nx.dijkstra_path(grafo, nodo, objetivo, weight='custo')
            custo = sum(grafo[caminho[i]][caminho[i+1]]['custo'] 
                       for i in range(len(caminho)-1))
            heuristica[nodo] = custo
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            heuristica[nodo] = float('inf')
    return heuristica

def busca_em_largura(grafo, inicio, objetivo):
    """
    Implementação corrigida da busca em largura.
    """
    if inicio not in grafo or objetivo not in grafo:
        print(f"Nodo inicial {inicio} ou objetivo {objetivo} não encontrado no grafo")
        return None
        
    fronteira = [(inicio, [inicio])]
    explorados = set()
    
    while fronteira:
        nodo, caminho = fronteira.pop(0)
        
        if nodo == objetivo:
            return caminho
        
        if nodo not in explorados:
            explorados.add(nodo)
            vizinhos = sorted(list(grafo.neighbors(nodo)))
            
            for vizinho in vizinhos:
                if vizinho not in explorados and not grafo[nodo][vizinho].get('bloqueado', False):
                    novo_caminho = caminho + [vizinho]
                    if vizinho not in [n for n, _ in fronteira]:
                        fronteira.append((vizinho, novo_caminho))
    
    print(f"Não foi encontrado caminho entre {inicio} e {objetivo}")
    return None

def busca_em_profundidade(grafo, inicio, objetivo):
    """
    Implementação corrigida da busca em profundidade.
    """
    if inicio not in grafo or objetivo not in grafo:
        print(f"Nodo inicial {inicio} ou objetivo {objetivo} não encontrado no grafo")
        return None
        
    fronteira = [(inicio, [inicio])]
    explorados = set()
    
    while fronteira:
        nodo, caminho = fronteira.pop()
        
        if nodo == objetivo:
            return caminho
            
        if nodo not in explorados:
            explorados.add(nodo)
            vizinhos = sorted(list(grafo.neighbors(nodo)), reverse=True)
            
            for vizinho in vizinhos:
                if vizinho not in explorados and not grafo[nodo][vizinho].get('bloqueado', False):
                    novo_caminho = caminho + [vizinho]
                    if vizinho not in [n for n, _ in fronteira]:
                        fronteira.append((vizinho, novo_caminho))
    
    print(f"Não foi encontrado caminho entre {inicio} e {objetivo}")
    return None

def busca_gulosa(grafo, inicio, objetivo, heuristica=None):
    """
    Implementação corrigida da busca gulosa.
    """
    if inicio not in grafo or objetivo not in grafo:
        print(f"Nodo inicial {inicio} ou objetivo {objetivo} não encontrado no grafo")
        return None
    
    if heuristica is None:
        heuristica = calcular_heuristica(grafo, objetivo)
        
    fronteira = [(heuristica[inicio], inicio, [inicio])]
    explorados = set()
    
    while fronteira:
        _, nodo, caminho = sorted(fronteira, key=lambda x: x[0])[0]
        fronteira = [(h, n, p) for h, n, p in fronteira if n != nodo]
        
        if nodo == objetivo:
            return caminho
            
        if nodo not in explorados:
            explorados.add(nodo)
            
            for vizinho in sorted(grafo.neighbors(nodo)):
                if vizinho not in explorados and not grafo[nodo][vizinho].get('bloqueado', False):
                    if vizinho not in [n for _, n, _ in fronteira]:
                        novo_caminho = caminho + [vizinho]
                        fronteira.append((heuristica[vizinho], vizinho, novo_caminho))
    
    print(f"Não foi encontrado caminho entre {inicio} e {objetivo}")
    return None

def busca_a_estrela(grafo, inicio, objetivo, heuristica=None):
    """
    Implementação corrigida do A*.
    """
    if inicio not in grafo or objetivo not in grafo:
        print(f"Nodo inicial {inicio} ou objetivo {objetivo} não encontrado no grafo")
        return None
    
    if heuristica is None:
        heuristica = calcular_heuristica(grafo, objetivo)
        
    open_list = {inicio}
    closed_list = set()
    
    g = {inicio: 0}
    parents = {inicio: None}
    
    while open_list:
        n = min(open_list, key=lambda x: g[x] + heuristica[x])
        
        if n == objetivo:
            path = []
            while n is not None:
                path.append(n)
                n = parents[n]
            path.reverse()
            return path
            
        open_list.remove(n)
        closed_list.add(n)
        
        for vizinho in sorted(grafo.neighbors(n)):
            if grafo[n][vizinho].get('bloqueado', False):
                continue
                
            tentative_g = g[n] + grafo[n][vizinho]['custo']
            
            if vizinho in closed_list and tentative_g >= g.get(vizinho, float('inf')):
                continue
                
            if vizinho not in open_list or tentative_g < g.get(vizinho, float('inf')):
                parents[vizinho] = n
                g[vizinho] = tentative_g
                if vizinho not in open_list:
                    open_list.add(vizinho)
    
    print(f"Não foi encontrado caminho entre {inicio} e {objetivo}")
    return None

def calcular_metricas_caminho(grafo, caminho):
    """Calcula métricas do caminho."""
    if not caminho or len(caminho) < 2:
        return None
    
    custo_total = 0
    tempo_total = 0
    
    for i in range(len(caminho) - 1):
        aresta = grafo[caminho[i]][caminho[i + 1]]
        custo_total += aresta['custo']
        tempo_total += aresta['tempo']
    
    return {
        'custo': round(custo_total, 2),
        'tempo': round(tempo_total, 2),
        'num_paradas': len(caminho) - 1
    }

def avaliar_algoritmos(grafo, inicio, objetivo):
    """
    Avalia os algoritmos de busca com melhor tratamento de erros e logging.
    """
    print(f"\n=== Avaliação dos Algoritmos de Busca ===")
    print(f"Buscando caminho de {inicio} para {objetivo}")
    
    if inicio not in grafo or objetivo not in grafo:
        print("Erro: nodos de início ou objetivo não encontrados no grafo")
        return None
    
    print("\nCalculando heurística...")
    heuristica = calcular_heuristica(grafo, objetivo)
    
    algoritmos = {
        "Busca em Largura": busca_em_largura,
        "Busca em Profundidade": busca_em_profundidade,
        "Busca Gulosa": lambda g, i, o: busca_gulosa(g, i, o, heuristica),
        "A*": lambda g, i, o: busca_a_estrela(g, i, o, heuristica)
    }
    
    resultados = {}
    for nome, algoritmo in algoritmos.items():
        print(f"\nExecutando {nome}...")
        try:
            inicio_tempo = time.time()
            caminho = algoritmo(grafo, inicio, objetivo)
            tempo_execucao = time.time() - inicio_tempo
            
            if caminho:
                metricas = calcular_metricas_caminho(grafo, caminho)
                if metricas:
                    resultados[nome] = {
                        "caminho": caminho,
                        "custo": metricas['custo'],
                        "tempo_percurso": metricas['tempo'],
                        "tempo_execucao": tempo_execucao,
                        "num_paradas": metricas['num_paradas']
                    }
                    print(f"Caminho encontrado: {' -> '.join(caminho)}")
                    print(f"Custo: {metricas['custo']:.2f}")
                    print(f"Tempo de percurso: {metricas['tempo']:.2f}")
                    print(f"Tempo de execução: {tempo_execucao:.4f} segundos")
                else:
                    print("Erro ao calcular métricas do caminho")
                    resultados[nome] = None
            else:
                print("Não encontrou caminho!")
                resultados[nome] = None
        except Exception as e:
            print(f"Erro ao executar {nome}: {str(e)}")
            resultados[nome] = None
    
    return resultados


if __name__ == "__main__":
    try:
        print("Criando o grafo...")
        pdg = PortugalDistributionGraph()
        grafo = pdg.criar_grafo_grande(num_pontos_entrega=100)
        
        print("\nInformações do grafo:")
        print(f"Número de nós: {grafo.number_of_nodes()}")
        print(f"Número de arestas: {grafo.number_of_edges()}")
        
        # Exemplo usando a base em Lisboa e um ponto de entrega
        inicio = 'BASE_LISBOA'
        # Encontrar um ponto de entrega válido para teste
        objetivo = [n for n, d in grafo.nodes(data=True) if d['tipo'] == 'entrega'][2]
        
        resultados = avaliar_algoritmos(grafo, inicio, objetivo)
        
        print("\n=== Comparação Final ===")
        algoritmos_validos = {k: v for k, v in resultados.items() if v is not None}
        
        if algoritmos_validos:
            melhor_custo = min(algoritmos_validos.items(), key=lambda x: x[1]['custo'])
            melhor_tempo = min(algoritmos_validos.items(), key=lambda x: x[1]['tempo_percurso'])
            
            print(f"\nMelhor algoritmo por custo: {melhor_custo[0]}")
            print(f"- Custo: {melhor_custo[1]['custo']:.2f}")
            print(f"- Caminho: {' -> '.join(melhor_custo[1]['caminho'])}")
            
            print(f"\nMelhor algoritmo por tempo de percurso: {melhor_tempo[0]}")
            print(f"- Tempo: {melhor_tempo[1]['tempo_percurso']:.2f}")
            print(f"- Caminho: {' -> '.join(melhor_tempo[1]['caminho'])}")
        else:
            print("Nenhum algoritmo encontrou um caminho válido.")
            
    except Exception as e:
        print(f"Erro durante a execução: {e}")