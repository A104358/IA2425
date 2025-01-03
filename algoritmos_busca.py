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

def busca_em_largura(grafo, inicio, objetivo, evitar: list[str] = []):
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
        
        pai = None
        if len(caminho) > 1:
            pai = caminho[-2]
        
        if nodo == objetivo:
            return caminho
        
        if nodo not in explorados:
            explorados.add((nodo, pai))
            vizinhos = sorted(list(grafo.neighbors(nodo)))
            
            for vizinho in vizinhos:
                # print(nodo, vizinho, grafo.nodes[vizinho].get("tipo_terreno", None), evitar)
                if (vizinho, nodo) not in explorados and not grafo[nodo][vizinho].get('bloqueado', False) and grafo.nodes[vizinho].get("tipo_terreno", None) not in evitar:
                    novo_caminho = caminho + [vizinho]
                    if vizinho not in caminho:
                        fronteira.append((vizinho, novo_caminho))
    
    print(f"Não foi encontrado caminho entre {inicio} e {objetivo}")
    return None

def busca_em_profundidade(grafo, inicio, objetivo, evitar: list[str] = []):
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
                # print(nodo, vizinho, grafo.nodes[vizinho].get("tipo_terreno", None), evitar)
                if vizinho not in explorados and not grafo[nodo][vizinho].get('bloqueado', False) and grafo.nodes[vizinho].get("tipo_terreno", None) not in evitar:
                    novo_caminho = caminho + [vizinho]
                    if vizinho not in [n for n, _ in fronteira]:
                        fronteira.append((vizinho, novo_caminho))
    
    print(f"Não foi encontrado caminho entre {inicio} e {objetivo}")
    return None

def busca_gulosa(grafo, inicio, objetivo, heuristica=None, evitar: list[str] = []):
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
                # print(nodo, vizinho, grafo.nodes[vizinho].get("tipo_terreno", None), evitar)
                if vizinho not in explorados and not grafo[nodo][vizinho].get('bloqueado', False) and grafo.nodes[vizinho].get("tipo_terreno", None) not in evitar:
                    if vizinho not in [n for _, n, _ in fronteira]:
                        novo_caminho = caminho + [vizinho]
                        fronteira.append((heuristica[vizinho], vizinho, novo_caminho))
    
    print(f"Não foi encontrado caminho entre {inicio} e {objetivo}")
    return None

def busca_a_estrela(grafo, inicio, objetivo, heuristica=None, evitar: list[str] = []):
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
            if grafo[n][vizinho].get('bloqueado', False) or grafo.nodes[vizinho].get("tipo_terreno", None) in evitar:
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
        'num_paragens': len(caminho) - 1
    }

def avaliar_algoritmos(grafo, inicio, objetivo):
    """
    Avalia os algoritmos de busca com melhor tratamento de erros e logging.
    """
    print(f"\n=== Avaliação dos Algoritmos de Busca ===")
    print(f"À procura de caminho de {inicio} para {objetivo}")
    
    if inicio not in grafo or objetivo not in grafo:
        print("Erro: nodos de início ou objetivo não encontrados no grafo")
        return None
    
    print("\nA calcular a heurística...")
    heuristica = calcular_heuristica(grafo, objetivo)
    
    algoritmos = {
        "Busca em Largura": busca_em_largura,
        "Busca em Profundidade": busca_em_profundidade,
        "Busca Gulosa": lambda g, i, o: busca_gulosa(g, i, o, heuristica),
        "A*": lambda g, i, o: busca_a_estrela(g, i, o, heuristica)
    }
    
    resultados = {}
    for nome, algoritmo in algoritmos.items():
        print(f"\n A executar {nome}...")
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
                        "num_paragens": metricas['num_paragens']
                    }
                    print(f"Caminho encontrado: {' -> '.join(caminho)}")
                    print(f"Custo: {metricas['custo']:.2f}")
                    print(f"Tempo de percurso: {metricas['tempo']:.2f}")
                    print(f"Tempo de execução: {tempo_execucao:.4f} segundos")
                else:
                    print("Erro ao calcular as métricas do caminho")
                    resultados[nome] = None
            else:
                print("Não encontrou caminho!")
                resultados[nome] = None
        except Exception as e:
            print(f"Erro ao executar {nome}: {str(e)}")
            resultados[nome] = None
    
    return resultados
