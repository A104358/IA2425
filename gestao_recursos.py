from typing import Dict, List, Tuple
import networkx as nx

class PlaneadorReabastecimento:
    def __init__(self, grafo: nx.DiGraph):
        self.grafo = grafo
        self.pontos_reabastecimento = self._identificar_pontos_reabastecimento()
        
    def _identificar_pontos_reabastecimento(self) -> List[str]:
        """Identifica os nodos do grafo que servem como pontos de reabastecimento."""
        return [node for node, data in self.grafo.nodes(data=True) 
                if 'POSTO_' in str(node)]

    def _calcular_custo_rota(self, rota: List[str]) -> float:
        """Calcula o custo total de uma rota."""
        if not rota or len(rota) < 2:
            return 0
        return sum(self.grafo[rota[i]][rota[i + 1]]['custo'] 
                  for i in range(len(rota) - 1))

    def _encontrar_melhor_posto(self, localizacao: str, autonomia: float) -> Tuple[str, List[str]]:
        """
        Encontra o melhor posto de reabastecimento considerando distância e autonomia.
        """
        melhor_posto = None
        melhor_rota = None
        menor_custo = float('inf')

        for posto in self.pontos_reabastecimento:
            try:
                # Usa Dijkstra para encontrar o caminho mais curto até o posto
                rota = nx.shortest_path(self.grafo, localizacao, posto, weight='custo')
                custo = self._calcular_custo_rota(rota)
                
                # Verifica se é possível chegar ao posto com a autonomia atual
                if custo <= autonomia * 0.9 and custo < menor_custo:  # 90% da autonomia para margem de segurança
                    melhor_posto = posto
                    melhor_rota = rota
                    menor_custo = custo
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        return melhor_posto, melhor_rota

    def calcular_proximo_reabastecimento(self, veiculo: Dict, rota_atual: List[str]) -> Tuple[bool, List[str]]:
        """
        Determina se e onde o veículo deve reabastecer.
        """
        combustivel_atual = veiculo['combustivel']
        autonomia = veiculo['autonomia']
        localizacao = veiculo['localizacao']
        
        # Ajuste no limite de reabastecimento para 60% da autonomia
        limite_reabastecimento = autonomia * 0.6

        if combustivel_atual <= limite_reabastecimento:
            melhor_posto, rota_reabastecimento = self._encontrar_melhor_posto(
                localizacao, combustivel_atual
            )
            
            if melhor_posto and rota_reabastecimento:
                return True, rota_reabastecimento
                
        return False, None

    def executar_reabastecimento(self, veiculo: Dict) -> bool:
        """
        Executa o reabastecimento do veículo.
        """
        # Verifica se o veículo está num posto de reabastecimento
        if any(posto in veiculo['localizacao'] for posto in ['POSTO_']):
            veiculo['combustivel'] = veiculo['autonomia']  # Reabastece até a autonomia máxima
            return True
        return False