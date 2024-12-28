from typing import Dict, List
import networkx as nx
from estado_inicial import estado_inicial
from criar_grafo import PortugalDistributionGraph
from busca_emergencia import BuscaEmergencia
from condicoes_meteorologicas import GestorMeteorologico, CondicaoMeteorologica
from eventos_dinamicos import GestorEventos
import time
import random

class SimulacaoEmergencia:
    def __init__(self, grafo: nx.DiGraph):
        self.grafo = grafo
        self.gestor_meteo = GestorMeteorologico(self.grafo)
        self.gestor_eventos = GestorEventos(self.grafo)
        self.busca = BuscaEmergencia(self.grafo, estado_inicial)
        
        self.estatisticas = {
            'entregas_realizadas': 0,
            'entregas_falhas': 0,
            'rotas_bloqueadas': 0,
            'tempo_total': 0,
            'falhas_por_clima': 0,
            'falhas_por_obstaculo': 0,
            'falhas_por_evento': 0,
            'impacto_populacao_alta': 0,
            'impacto_populacao_baixa': 0
        }

    def executar_simulacao(self, num_ciclos: int):
        print(f"Iniciando simulação com {num_ciclos} ciclos...")
        
        for ciclo in range(num_ciclos):
            print(f"\n=== Ciclo {ciclo + 1} ===")
            
            # Atualizar condições meteorológicas com menor frequência
            if ciclo % 5 == 0:  # Atualiza a cada 5 ciclos
                self.gestor_meteo.atualizar_condicoes()
                self.gestor_meteo.imprimir_status()

            # Gerar e atualizar eventos dinâmicos
            self.gestor_eventos.gerar_eventos_aleatorios(prob_novo_evento=0.3)
            self.gestor_eventos.atualizar_eventos()
            self.gestor_eventos.aplicar_efeitos()
            self.gestor_eventos.imprimir_status()

            # Tentar realizar entregas com cada veículo
            for veiculo in self.busca.estado["veiculos"]:
                print(f"\nPlanejando rota para {veiculo['tipo']} (ID: {veiculo['id']})")
                
                # Verificar condições meteorológicas na localização atual
                regiao_atual = self.grafo.nodes[veiculo['localizacao']]['regiao']
                condicao_atual = self.gestor_meteo.get_condicao_regiao(regiao_atual)
                
                # Permitir operação mesmo em tempestade com 60% de chance
                if condicao_atual == CondicaoMeteorologica.TEMPESTADE and random.random() > 0.4:
                    print(f"Veículo {veiculo['id']} operando em condições adversas!")
                else:
                    if condicao_atual == CondicaoMeteorologica.TEMPESTADE:
                        print(f"Veículo {veiculo['id']} não pode operar devido à tempestade!")
                        self.estatisticas['falhas_por_clima'] += 1
                        self.estatisticas['entregas_falhas'] += 1
                        continue
                
                # Buscar rota
                rota = self.busca.busca_rota_prioritaria(veiculo['id'])
                if not rota:
                    print("Não foi possível encontrar uma rota válida")
                    self.estatisticas['rotas_bloqueadas'] += 1
                    continue
                
                # Verificar bloqueios com alta chance de passagem
                tem_bloqueio = False
                for i in range(len(rota) - 1):
                    if self.grafo[rota[i]][rota[i+1]].get('bloqueado', False):
                        if random.random() > 0.2:  # 80% chance de conseguir passar
                            continue
                        tem_bloqueio = True
                        break

                if tem_bloqueio:
                    print("Rota contém trechos bloqueados, buscando alternativa...")
                    self.estatisticas['rotas_bloqueadas'] += 1
                    continue
                
                # Calcular métricas com impactos reduzidos
                impactos = self.gestor_eventos.get_impacto_total(rota)
                # Reduzir o impacto total em 40%
                impactos['impacto_custo'] = max(1.0, impactos['impacto_custo'] * 0.6)
                impactos['impacto_tempo'] = max(1.0, impactos['impacto_tempo'] * 0.6)
                
                custo_total = sum(self.grafo[rota[i]][rota[i+1]]['custo'] for i in range(len(rota)-1)) * impactos['impacto_custo']
                tempo_total = sum(self.grafo[rota[i]][rota[i+1]]['tempo'] for i in range(len(rota)-1)) * impactos['impacto_tempo']
                
                # Reduzir impacto da densidade populacional
                densidade_pop = self.grafo.nodes[rota[-1]].get('densidade_populacional', 'normal')
                if densidade_pop == 'alta':
                    custo_total *= 0.98
                    tempo_total *= 0.98
                    self.estatisticas['impacto_populacao_alta'] += 1
                elif densidade_pop == 'baixa':
                    custo_total *= 1.02
                    tempo_total *= 1.02
                    self.estatisticas['impacto_populacao_baixa'] += 1
                
                print(f"Rota encontrada: {' -> '.join(rota)}")
                print(f"Custo total: {custo_total:.2f}")
                print(f"Tempo estimado: {tempo_total:.2f} minutos")
                
                if self.simular_entrega(veiculo, rota, custo_total, tempo_total):
                    self.estatisticas['entregas_realizadas'] += 1
                    self.estatisticas['tempo_total'] += tempo_total
                else:
                    self.estatisticas['entregas_falhas'] += 1

    def simular_entrega(self, veiculo: Dict, rota: List[str], custo_total: float, tempo_total: float) -> bool:
        # Permitir exceder a autonomia em 50%
        if custo_total > veiculo['autonomia'] * 1.5:
            print(f"Entrega falhou: autonomia insuficiente ({custo_total:.2f} > {veiculo['autonomia']})")
            self.estatisticas['falhas_por_obstaculo'] += 1
            return False
        
        # Manter probabilidade significativa de falha por evento
        for i in range(len(rota) - 1):
            edge = (rota[i], rota[i + 1])
            if edge in self.gestor_eventos.eventos:
                if random.random() < 0.25:  # 25% chance de falha
                    print(f"Entrega falhou devido a um evento dinâmico em {edge}")
                    self.estatisticas['falhas_por_evento'] += 1
                    return False
        
        # Reabastecimento parcial após cada entrega bem-sucedida
        veiculo['localizacao'] = rota[-1]
        veiculo['combustivel'] = max(veiculo['combustivel'] - custo_total * 0.7,  # Reduz o consumo em 30%
                                   veiculo['autonomia'] * 0.3)  # Mantém pelo menos 30% da autonomia
        
        print(f"Entrega realizada com sucesso! Novo nível de combustível: {veiculo['combustivel']:.2f}")
        return True

    def imprimir_estatisticas(self):
        print("\n=== Estatísticas da Simulação ===")
        print(f"Entregas realizadas com sucesso: {self.estatisticas['entregas_realizadas']}")
        print(f"Entregas falhadas: {self.estatisticas['entregas_falhas']}")
        print(f"Rotas bloqueadas: {self.estatisticas['rotas_bloqueadas']}")
        print(f"Falhas por clima: {self.estatisticas['falhas_por_clima']}")
        print(f"Falhas por obstáculos: {self.estatisticas['falhas_por_obstaculo']}")
        print(f"Falhas por eventos: {self.estatisticas['falhas_por_evento']}")
        print(f"Impacto em áreas de alta densidade populacional: {self.estatisticas['impacto_populacao_alta']}")
        print(f"Impacto em áreas de baixa densidade populacional: {self.estatisticas['impacto_populacao_baixa']}")
        
        if self.estatisticas['entregas_realizadas'] > 0:
            tempo_medio = self.estatisticas['tempo_total'] / self.estatisticas['entregas_realizadas']
            print(f"Tempo médio por entrega: {tempo_medio:.2f} minutos")
        
        total_entregas = (self.estatisticas['entregas_realizadas'] + 
                         self.estatisticas['entregas_falhas'])
        if total_entregas > 0:
            taxa_sucesso = (self.estatisticas['entregas_realizadas'] / total_entregas) * 100
            print(f"Taxa de sucesso: {taxa_sucesso:.2f}%")

def main():
    # Configurações da simulação
    NUM_PONTOS_ENTREGA = 50
    NUM_CICLOS = 15
    
    # Criar grafo
    print("Criando o grafo...")
    pdg = PortugalDistributionGraph()
    grafo = pdg.criar_grafo_grande(NUM_PONTOS_ENTREGA)
    
    print("\nInformações do grafo:")
    print(f"Número de nós: {grafo.number_of_nodes()}")
    print(f"Número de arestas: {grafo.number_of_edges()}")
    
    # Criar e executar simulação
    simulacao = SimulacaoEmergencia(grafo)
    simulacao.executar_simulacao(NUM_CICLOS)
    
    # Imprimir estatísticas finais
    simulacao.imprimir_estatisticas()

if __name__ == "__main__":
    random.seed(42)
    main()
