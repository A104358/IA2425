import random
import networkx as nx
from eventos_dinamicos import TipoObstaculo
from condicoes_meteorologicas import CondicaoMeteorologica, GestorMeteorologico
from datetime import datetime, timedelta
from janela_tempo import JanelaTempoZona

estado_inicial = {
    "veiculos": [
        {
            "id": 1, 
            "tipo": "camião", 
            "localizacao": "BASE_LISBOA", 
            "capacidade": 500, 
            "volume_max": 1000,  # Adicione esta linha
            "autonomia": 300, 
            "combustivel": 300
        },
        # Atualize os outros veículos similarmente...
    ],
    "suprimentos": {
        "alimentos": {"peso": 1000, "volume": 2000},  # Modifique para incluir volume
        "água": {"peso": 500, "volume": 500},
        "medicamentos_básicos": {"peso": 300, "volume": 200},
        "medicamentos_especializados": {"peso": 150, "volume": 100},
        "kits_primeiros_socorros": {"peso": 200, "volume": 400}
    }
}

def inicializar_zonas_afetadas(grafo: nx.DiGraph):
    """Inicializa zonas afetadas baseado nos eventos e obstáculos possíveis."""
    zonas = {}
    agora = datetime.now()

    for node, data in grafo.nodes(data=True):
        if data['tipo'] == 'entrega':
            densidade_populacional = data.get('densidade_populacional', 'normal')

            necessidades = {
                "alimentos": random.randint(50, 150),
                "água": random.randint(30, 100),
                "medicamentos_básicos": random.randint(20, 80),
                "kits_primeiros_socorros": random.randint(10, 50)
            }

            # Ajustar necessidades com base na densidade populacional
            if densidade_populacional == 'alta':
                for key in necessidades:
                    necessidades[key] = int(necessidades[key] * 1.5)
                populacao = random.randint(800, 1500)  # Alta densidade
            elif densidade_populacional == 'baixa':
                for key in necessidades:
                    necessidades[key] = int(necessidades[key] * 0.8)
                populacao = random.randint(100, 500)  # Baixa densidade
            else:
                populacao = random.randint(500, 800)  # Densidade normal

            # Criar janela de tempo
            duracao_horas = random.randint(6, 24)
            janela_tempo = JanelaTempoZona(node, agora, duracao_horas)

            zonas[node] = {
                "necessidades": necessidades,
                "densidade_populacional": densidade_populacional,
                "prioridade": random.randint(1, 5),
                "suprida": False,
                "populacao": populacao,
                "janela_tempo": janela_tempo
            }

    return zonas

def exibir_estado_inicial(estado):
    """Exibe o estado inicial formatado para melhor legibilidade."""
    print("\n=== Estado Inicial ===")
    print("\nVeículos:")
    for veiculo in estado["veiculos"]:
        print(f"- ID: {veiculo['id']} | Tipo: {veiculo['tipo']} | Localização: {veiculo['localizacao']} "
              f"| Capacidade: {veiculo['capacidade']} | Autonomia: {veiculo['autonomia']} | Combustível: {veiculo['combustivel']}")

    print("\nSuprimentos:")
    for tipo, quantidade in estado["suprimentos"].items():
        print(f"- {tipo.capitalize()}: {quantidade}")

    print("\nZonas Afetadas:")
    if estado["zonas_afetadas"]:
        for zona, detalhes in estado["zonas_afetadas"].items():
            print(f"- Zona: {zona}")
            print(f"  Densidade populacional: {detalhes['densidade_populacional']}")
            print(f"  Prioridade: {detalhes['prioridade']}")
            print(f"  População: {detalhes['populacao']}")
            print("  Necessidades:")
            for tipo, qtd in detalhes["necessidades"].items():
                print(f"    - {tipo.capitalize()}: {qtd}")
            janela = detalhes['janela_tempo']
            print(f"  Janela de tempo: {janela.inicio} a {janela.fim} (Criticidade: {janela.criticidade:.2f})")
            print(f"  Suprida: {'Sim' if detalhes['suprida'] else 'Não'}")
    else:
        print("- Nenhuma zona afetada registrada.")


# Teste do estado inicial
if __name__ == "__main__":
    grafo_teste = nx.DiGraph()
    grafo_teste.add_node("PE_1", tipo="entrega", densidade_populacional="alta")
    grafo_teste.add_node("PE_2", tipo="entrega", densidade_populacional="baixa")
    grafo_teste.add_node("PE_3", tipo="entrega", densidade_populacional="normal")

    estado_inicial["zonas_afetadas"] = inicializar_zonas_afetadas(grafo_teste)
    exibir_estado_inicial(estado_inicial)
