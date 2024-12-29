# limitacoes_geograficas.py
from enum import Enum
from typing import Dict, Set

class TipoTerreno(Enum):
    URBANO = "urbano"
    MONTANHOSO = "montanhoso"
    FLORESTAL = "florestal"
    COSTEIRO = "costeiro"
    RURAL = "rural"

class RestricaoAcesso:
    def __init__(self):
        self.restricoes_veiculo = {
            "camião": {TipoTerreno.MONTANHOSO, TipoTerreno.FLORESTAL},
            "drone": set(),  # Drones podem acessar todos os terrenos
            "helicóptero": set()  # Helicópteros podem acessar todos os terrenos
        }
    
    def pode_acessar(self, tipo_veiculo: str, tipo_terreno: TipoTerreno) -> bool:
        return tipo_terreno not in self.restricoes_veiculo.get(tipo_veiculo, set())