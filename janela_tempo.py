# janela_tempo.py
from datetime import datetime, timedelta

class JanelaTempoZona:
    def __init__(self, zona_id: str, inicio: datetime, duracao_horas: int):
        self.zona_id = zona_id
        self.inicio = inicio
        self.fim = inicio + timedelta(hours=duracao_horas)
        self.criticidade = self._calcular_criticidade()
    
    def _calcular_criticidade(self) -> float:
        """Calcula nível de criticidade baseado no tempo restante"""
        agora = datetime.now()
        if agora > self.fim:
            return 0.0  # Janela fechada
        
        tempo_total = (self.fim - self.inicio).total_seconds()
        tempo_restante = (self.fim - agora).total_seconds()
        return max(0.0, min(1.0, tempo_restante / tempo_total))
    
    def esta_acessivel(self) -> bool:
        return datetime.now() <= self.fim
