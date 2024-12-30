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
        self.criticidade = self._calcular_criticidade()  # Novo atributo

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
        criticidade_base = (tempo_restante / tempo_total) if tempo_restante > 0 else 0.0
        return criticidade_base * self.prioridade

    def esta_acessivel(self) -> bool:
        """Verifica se a janela ainda está aberta."""
        return datetime.now() <= self.fim

    def tempo_restante(self) -> float:
        """Calcula o tempo restante em horas."""
        agora = datetime.now()
        if agora > self.fim:
            return 0.0
        return (self.fim - agora).total_seconds() / 3600

    def esta_em_periodo_critico(self) -> bool:
        """Verifica se a janela está em período crítico (<25% do tempo restante)."""
        tempo_total = self.duracao
        tempo_restante = self.tempo_restante()
        return tempo_restante < (tempo_total * 0.25)
