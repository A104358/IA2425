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
            "camião": {TipoTerreno.MONTANHOSO, TipoTerreno.FLORESTAL, TipoTerreno.COSTEIRO},
            "camioneta": {TipoTerreno.MONTANHOSO, TipoTerreno.COSTEIRO},
            "barco": {TipoTerreno.URBANO, TipoTerreno.MONTANHOSO, TipoTerreno.FLORESTAL, TipoTerreno.RURAL},
            "drone": set(),  # Drones podem aceder todos os terrenos
            "helicóptero": {TipoTerreno.COSTEIRO}  # Helicópteros não podem aceder terrenos costeiros
        }