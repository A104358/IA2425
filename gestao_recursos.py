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

    def _identificar_pontos_reabastecimento(self) -> List[str]:
        """Identifica os nodos do grafo que servem como pontos de reabastecimento."""
        pontos = []
        for node, data in self.grafo.nodes(data=True):
            if data.get('tipo') == 'reabastecimento':  # Ajuste conforme o modelo do grafo
                pontos.append(node)
        return pontos

    def calcular_proximo_reabastecimento(self, veiculo: Dict, rota: List[str]) -> str:
        """Calcula o próximo ponto de reabastecimento baseado na rota."""
        for node in rota:
            if node in self.pontos_reabastecimento:
                return node
            return None
