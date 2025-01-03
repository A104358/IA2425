from datetime import datetime, timedelta
from enum import Enum

class PrioridadeZona(Enum):
    BAIXA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4
    EMERGENCIA = 5

class JanelaTempoZona:
    def __init__(self, zona_id: str, inicio: datetime, duracao_horas: int, prioridade: int):
        self.zona_id = zona_id
        self.inicio = inicio
        self.duracao = duracao_horas
        self.fim = inicio + timedelta(hours=duracao_horas)
        self.prioridade = prioridade
        self.penalizacao_atraso = self._calcular_penalizacao_base()
        self.criticidade = self._calcular_criticidade() 

    def _calcular_penalizacao_base(self) -> float:
        """Calcula penalização com base na prioridade."""
        penalizacoes = {
            1: 0.1,  # Prioridade muito baixa
            2: 0.2,  # Prioridade baixa
            3: 0.5,  # Prioridade média
            4: 0.7,  # Prioridade alta
            5: 1.0   # Prioridade muito alta
        }
        if self.prioridade not in penalizacoes:
            raise ValueError(f"Prioridade inválida: {self.prioridade}. Penalizações disponíveis: {list(penalizacoes.keys())}")
        return penalizacoes[self.prioridade]

    def _calcular_criticidade(self) -> float:
        """Calcula a criticidade com base no tempo restante e prioridade."""
        tempo_restante = self.tempo_restante()
        tempo_total = self.duracao
        
        if tempo_total == 0:
            return 0.0
            
        # Inverte a lógica: menos tempo = maior criticidade
        proporcao_tempo = 1 - (tempo_restante / tempo_total)
        
        # Aumenta exponencialmente a criticidade quando abaixo de 25%
        if tempo_restante < (tempo_total * 0.25):
            proporcao_tempo = proporcao_tempo * 2
            
        return min(1.0, proporcao_tempo * self.prioridade)
        
    def esta_em_periodo_critico(self) -> bool:
        """Verifica se a janela está em período crítico (<25% do tempo restante)."""
        tempo_total = self.duracao
        tempo_restante = self.tempo_restante()
        
        if tempo_restante <= 0:
            return False  
        return tempo_restante < (tempo_total * 0.25)
        
    def get_fator_urgencia(self) -> float:
        """Retorna um multiplicador de urgência baseado no estado da janela."""
        if not self.esta_acessivel():
            return 0.0
            
        if self.esta_em_periodo_critico():
            proporcao_restante = self.tempo_restante() / (self.duracao * 0.25)
            return 2.0 + (1 - proporcao_restante)
            
        return 1.0
    
    def esta_acessivel(self) -> bool:
        """Verifica se a janela ainda está aberta."""
        return datetime.now() <= self.fim

    def tempo_restante(self) -> float:
        """Calcula o tempo restante em horas."""
        agora = datetime.now()
        if agora > self.fim:
            return 0.0
        return (self.fim - agora).total_seconds() / 3600

