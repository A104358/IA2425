from typing import Dict, Set, List, Tuple
from enum import Enum
from dataclasses import dataclass
import networkx as nx

class TipoRecurso(Enum):
    ALIMENTO = "alimento"
    MEDICAMENTO = "medicamento"
    AGUA = "agua"
    EQUIPAMENTO = "equipamento"

@dataclass
class Recurso:
    tipo: TipoRecurso
    peso: float
    volume: float
    prioridade: int
    perecivel: bool = False
    temperatura_necessaria: float = None

class RecursosVeiculo:
    def __init__(self, capacidade_peso: float, capacidade_volume: float, tipo_veiculo: str):
        self.capacidade_peso = capacidade_peso
        self.capacidade_volume = capacidade_volume
        self.tipo_veiculo = tipo_veiculo
        self.peso_atual = 0.0
        self.volume_atual = 0.0
        self.recursos: Dict[TipoRecurso, List[Recurso]] = {}
        self.temperatura_atual = 20.0  # temperatura padrão em Celsius

    
    def pode_transportar_recurso(self, recurso: Recurso) -> Tuple[bool, str]:
        """Verifica se o veículo pode transportar o recurso considerando restrições"""
        if recurso.temperatura_necessaria:
            if self.tipo_veiculo not in ['refrigerado', 'climatizado']:
                return False, "Veículo não possui sistema de controle de temperatura"
        
        if self.peso_atual + recurso.peso > self.capacidade_peso:
            return False, "Excede capacidade de peso"
            
        if self.volume_atual + recurso.volume > self.capacidade_volume:
            return False, "Excede capacidade de volume"
            
        return True, ""
    
    def adicionar_recurso(self, recurso: Recurso) -> bool:
        pode_transportar, motivo = self.pode_transportar_recurso(recurso)
        if not pode_transportar:
            return False
            
        if recurso.tipo not in self.recursos:
            self.recursos[recurso.tipo] = []
            
        self.recursos[recurso.tipo].append(recurso)
        self.peso_atual += recurso.peso
        self.volume_atual += recurso.volume
        return True
    
    def calcular_espaco_disponivel(self) -> Tuple[float, float]:
        """Retorna espaço disponível em (peso, volume)"""
        return (
            self.capacidade_peso - self.peso_atual,
            self.capacidade_volume - self.volume_atual
        )
    
    def calcular_eficiencia_carga(self) -> float:
        """Calcula a eficiência de carga baseada no peso e volume utilizados."""
        peso_utilizado = self.peso_atual / self.capacidade_peso if self.capacidade_peso > 0 else 0
        volume_utilizado = self.volume_atual / self.capacidade_volume if self.capacidade_volume > 0 else 0
        return (peso_utilizado + volume_utilizado) / 2
    
class PlaneadorReabastecimento:
    def __init__(self, grafo: nx.DiGraph):
        self.grafo = grafo
        self.pontos_reabastecimento = self._identificar_pontos_reabastecimento()
        self.capacidade_maxima = 100  # Capacidade máxima de combustível

    def _identificar_pontos_reabastecimento(self) -> List[str]:
        """Identifica os nodos do grafo que servem como pontos de reabastecimento."""
        return [node for node, data in self.grafo.nodes(data=True) 
                if 'POSTO_' in str(node)]  # Mudança aqui para identificar postos corretamente

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
        
        # Ajuste no limite de reabastecimento para 30% da autonomia
        limite_reabastecimento = autonomia * 0.3

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
        # Verifica se o veículo está em um posto de reabastecimento
        if any(posto in veiculo['localizacao'] for posto in ['POSTO_']):
            veiculo['combustivel'] = veiculo['autonomia']  # Reabastece até a autonomia máxima
            return True
        return False
