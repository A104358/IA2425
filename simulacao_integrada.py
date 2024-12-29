from typing import Dict, List, Counter
import networkx as nx
from estado_inicial import estado_inicial
from criar_grafo import PortugalDistributionGraph
from busca_emergencia import BuscaEmergencia
from condicoes_meteorologicas import GestorMeteorologico, CondicaoMeteorologica
from eventos_dinamicos import GestorEventos
from limitacoes_geograficas import RestricaoAcesso, TipoTerreno
from gestao_recursos import RecursosVeiculo, PlanejadorReabastecimento
import time
import random

class SimulacaoEmergencia:
    def __init__(self, grafo: nx.DiGraph):
        self.grafo = grafo
        self.gestor_meteo = GestorMeteorologico(self.grafo)
        self.gestor_eventos = GestorEventos(self.grafo)
        self.busca = BuscaEmergencia(self.grafo, estado_inicial)
        self.restricao_acesso = RestricaoAcesso()
        self.planejador_reabastecimento = PlanejadorReabastecimento(self.grafo)
        
        # Initialize default terrain types for nodes that don't have them
        self._inicializar_terrenos()
        
        self.estatisticas = {
            'entregas_realizadas': 0,
            'entregas_falhas': 0,
            'rotas_bloqueadas': 0,
            'tempo_total': 0,
            'falhas_por_clima': 0,
            'falhas_por_obstaculo': 0,
            'falhas_por_evento': 0,
            'impacto_populacao_alta': 0,
            'impacto_populacao_baixa': 0,
            'falhas_por_terreno': 0,
            'distribuicao_terrenos': Counter(),
            'acessos_por_terreno': Counter(),
            'falhas_por_tipo_veiculo': Counter(),
            'sucessos_por_tipo_veiculo': Counter()
        }
    
    def _inicializar_terrenos(self):
        """Initialize terrain types for all nodes in the graph."""
        terrenos_possiveis = [t.value for t in TipoTerreno]
        for node in self.grafo.nodes():
            if 'tipo_terreno' not in self.grafo.nodes[node]:
                if node.startswith('BASE_'):
                    self.grafo.nodes[node]['tipo_terreno'] = TipoTerreno.URBANO.value
                else:
                    weights = [0.4 if t in ['urbano', 'rural'] else 0.1 for t in terrenos_possiveis]
                    terreno = random.choices(terrenos_possiveis, weights=weights, k=1)[0]
                    self.grafo.nodes[node]['tipo_terreno'] = terreno
                    self.estatisticas['distribuicao_terrenos'][terreno] += 1

    def executar_simulacao(self, num_ciclos: int):
        print(f"Iniciando simulação com {num_ciclos} ciclos...")
        
        for ciclo in range(num_ciclos):
            print(f"\n=== Ciclo {ciclo + 1} ===")
            
            if ciclo % 5 == 0:
                self.gestor_meteo.atualizar_condicoes()
                self.gestor_meteo.imprimir_status()

            self.gestor_eventos.gerar_eventos_aleatorios(prob_novo_evento=0.3)
            self.gestor_eventos.atualizar_eventos()
            self.gestor_eventos.aplicar_efeitos()
            self.gestor_eventos.imprimir_status()

            for veiculo in self.busca.estado["veiculos"]:
                print(f"\nPlanejando rota para {veiculo['tipo']} (ID: {veiculo['id']})")
                
                node_atual = veiculo['localizacao']
                tipo_terreno = TipoTerreno(self.grafo.nodes[node_atual]['tipo_terreno'])
                
                # Atualizar estatísticas de acesso ao terreno
                self.estatisticas['acessos_por_terreno'][tipo_terreno.value] += 1
                
                if not self.restricao_acesso.pode_acessar(veiculo['tipo'], tipo_terreno):
                    print(f"Veículo {veiculo['id']} não pode acessar terreno {tipo_terreno.value}")
                    self.estatisticas['falhas_por_terreno'] += 1
                    self.estatisticas['falhas_por_tipo_veiculo'][veiculo['tipo']] += 1
                    continue    

                regiao_atual = self.grafo.nodes[veiculo['localizacao']]['regiao']
                condicao_atual = self.gestor_meteo.get_condicao_regiao(regiao_atual)
                
                if condicao_atual == CondicaoMeteorologica.TEMPESTADE and random.random() > 0.4:
                    print(f"Veículo {veiculo['id']} operando em condições adversas!")
                else:
                    if condicao_atual == CondicaoMeteorologica.TEMPESTADE:
                        print(f"Veículo {veiculo['id']} não pode operar devido à tempestade!")
                        self.estatisticas['falhas_por_clima'] += 1
                        self.estatisticas['entregas_falhas'] += 1
                        continue
                
                rota = self.busca.busca_rota_prioritaria(veiculo['id'])
                if not rota:
                    print("Não foi possível encontrar uma rota válida")
                    self.estatisticas['rotas_bloqueadas'] += 1
                    continue
                
                impactos = self.gestor_eventos.get_impacto_total(rota)
                impactos['impacto_custo'] = max(1.0, impactos['impacto_custo'] * 0.6)
                impactos['impacto_tempo'] = max(1.0, impactos['impacto_tempo'] * 0.6)
                
                custo_total = sum(self.grafo[rota[i]][rota[i+1]]['custo'] for i in range(len(rota)-1)) * impactos['impacto_custo']
                tempo_total = sum(self.grafo[rota[i]][rota[i+1]]['tempo'] for i in range(len(rota)-1)) * impactos['impacto_tempo']
                
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
                    self.estatisticas['sucessos_por_tipo_veiculo'][veiculo['tipo']] += 1
                else:
                    self.estatisticas['entregas_falhas'] += 1
                    self.estatisticas['falhas_por_tipo_veiculo'][veiculo['tipo']] += 1


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
        print("\n--- Estatísticas Gerais ---")
        print(f"Entregas realizadas com sucesso: {self.estatisticas['entregas_realizadas']}")
        print(f"Entregas falhadas: {self.estatisticas['entregas_falhas']}")
        print(f"Rotas bloqueadas: {self.estatisticas['rotas_bloqueadas']}")
        
        print("\n--- Falhas por Tipo ---")
        print(f"Falhas por clima: {self.estatisticas['falhas_por_clima']}")
        print(f"Falhas por obstáculos: {self.estatisticas['falhas_por_obstaculo']}")
        print(f"Falhas por eventos: {self.estatisticas['falhas_por_evento']}")
        print(f"Falhas por restrições de terreno: {self.estatisticas['falhas_por_terreno']}")
        
        print("\n--- Estatísticas por Tipo de Terreno ---")
        print("Distribuição de terrenos no mapa:")
        for terreno, count in self.estatisticas['distribuicao_terrenos'].items():
            print(f"  - {terreno}: {count} locais")
        
        print("\nAcessos por tipo de terreno:")
        for terreno, count in self.estatisticas['acessos_por_terreno'].items():
            print(f"  - {terreno}: {count} tentativas de acesso")
        
        print("\n--- Estatísticas por Tipo de Veículo ---")
        for tipo_veiculo in set(self.estatisticas['sucessos_por_tipo_veiculo'].keys()) | set(self.estatisticas['falhas_por_tipo_veiculo'].keys()):
            sucessos = self.estatisticas['sucessos_por_tipo_veiculo'][tipo_veiculo]
            falhas = self.estatisticas['falhas_por_tipo_veiculo'][tipo_veiculo]
            total = sucessos + falhas
            if total > 0:
                taxa_sucesso = (sucessos / total) * 100
                print(f"\n{tipo_veiculo.capitalize()}:")
                print(f"  - Entregas bem-sucedidas: {sucessos}")
                print(f"  - Falhas: {falhas}")
                print(f"  - Taxa de sucesso: {taxa_sucesso:.2f}%")
        
        print("\n--- Impacto por Densidade Populacional ---")
        print(f"Impacto em áreas de alta densidade: {self.estatisticas['impacto_populacao_alta']}")
        print(f"Impacto em áreas de baixa densidade: {self.estatisticas['impacto_populacao_baixa']}")
        
        if self.estatisticas['entregas_realizadas'] > 0:
            tempo_medio = self.estatisticas['tempo_total'] / self.estatisticas['entregas_realizadas']
            print(f"\nTempo médio por entrega: {tempo_medio:.2f} minutos")
        
        total_entregas = (self.estatisticas['entregas_realizadas'] + 
                         self.estatisticas['entregas_falhas'])
        if total_entregas > 0:
            taxa_sucesso = (self.estatisticas['entregas_realizadas'] / total_entregas) * 100
            print(f"\nTaxa de sucesso global: {taxa_sucesso:.2f}%")

def main():
    # Configurações da simulação
    NUM_PONTOS_ENTREGA = 50
    NUM_CICLOS = 1
    
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
