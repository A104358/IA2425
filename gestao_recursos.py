from typing import Dict, Set, List

# gestao_recursos.py
class RecursosVeiculo:
    def __init__(self, capacidade_peso: float, capacidade_volume: float):
        self.capacidade_peso = capacidade_peso
        self.capacidade_volume = capacidade_volume
        self.peso_atual = 0.0
        self.volume_atual = 0.0
    
    def pode_adicionar_carga(self, peso: float, volume: float) -> bool:
        return (self.peso_atual + peso <= self.capacidade_peso and 
                self.volume_atual + volume <= self.capacidade_volume)
    
    def adicionar_carga(self, peso: float, volume: float) -> bool:
        if self.pode_adicionar_carga(peso, volume):
            self.peso_atual += peso
            self.volume_atual += volume
            return True
        return False

class PlanejadorReabastecimento:
    def __init__(self, grafo):
        self.grafo = grafo
        self.pontos_reabastecimento = self._identificar_pontos_reabastecimento()
    
    def _identificar_pontos_reabastecimento(self) -> Set[str]:
        """Identifica nós que podem servir como pontos de reabastecimento"""
        return {node for node, data in self.grafo.nodes(data=True) 
                if data['tipo'] in ['base', 'hub']}
    
    def calcular_proximo_reabastecimento(self, veiculo: Dict, rota: List[str]) -> str:
        """Determina o próximo ponto de reabastecimento necessário"""
        combustivel_atual = veiculo['combustivel']
        posicao_atual = veiculo['localizacao']
        
        custo_acumulado = 0
        ultimo_ponto_reabastecimento = None
        
        for i in range(len(rota) - 1):
            custo_trecho = self.grafo[rota[i]][rota[i+1]]['custo']
            if custo_acumulado + custo_trecho > combustivel_atual * 0.8:  # Margem de segurança
                # Procurar ponto de reabastecimento mais próximo
                for ponto in self.pontos_reabastecimento:
                    if ponto in rota[i:i+2] and ponto != rota[i]:
                        return ponto
            
            custo_acumulado += custo_trecho
        
        return None  # Não necessita reabastecimento