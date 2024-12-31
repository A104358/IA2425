from typing import Dict, List, Counter
import networkx as nx
from estado_inicial import estado_inicial
from criar_grafo import PortugalDistributionGraph
from busca_emergencia import BuscaEmergencia
from condicoes_meteorologicas import GestorMeteorologico, CondicaoMeteorologica
from eventos_dinamicos import GestorEventos
from limitacoes_geograficas import RestricaoAcesso, TipoTerreno
from gestao_recursos import RecursosVeiculo, PlaneadorReabastecimento
from janela_tempo import JanelaTempoZona
from datetime import datetime, timedelta
import time
import random
from tabulate import tabulate

class SimulacaoEmergencia:
    def __init__(self, grafo: nx.DiGraph):
        self.grafo = grafo
        self.gestor_meteo = GestorMeteorologico(self.grafo)
        self.gestor_eventos = GestorEventos(self.grafo)
        self.busca = BuscaEmergencia(self.grafo, estado_inicial)
        self.restricao_acesso = RestricaoAcesso()
        self.planeador_reabastecimento = PlaneadorReabastecimento(self.grafo)
        self.estatisticas = self._inicializar_estatisticas()
        self.recursos_veiculos = {}
        self._inicializar_terrenos()
        self._inicializar_recursos_veiculos()
    
    def _inicializar_estatisticas(self) -> Dict:
        """Inicializa o dicionário de estatísticas com valores zerados."""
        return {
            'entregas_realizadas': 0,
            'entregas_falhas': 0,
            'rotas_bloqueadas': 0,
            'tempo_total': 0,
            'falhas_por_clima': 0,
            'falhas_por_obstaculo': 0,
            'falhas_por_evento': 0,
            'falhas_por_terreno': 0,
            'falhas_por_carga': 0,
            'distribuicao_terrenos': Counter(),
            'acessos_por_terreno': Counter(),
            'entregas_por_terreno': Counter(),
            'sucessos_por_tipo_veiculo': Counter(),
            'falhas_por_tipo_veiculo': Counter(),
            'impacto_populacao_alta': 0,
            'impacto_populacao_baixa': 0,
            'tempo_medio_restante': 0,
            'total_tempo_restante': 0,
            'zonas_expiradas': 0,
            'janelas_criticas': 0,
            'entregas_dentro_janela': 0,
            'entregas_fora_janela': 0,
            'eficiencia_carga_total': 0,
            'reabastecimentos': 0
        }

    def _inicializar_terrenos(self):
        """Inicializa tipos de terrenos para todos os nodos no grafo."""
        terrenos_possiveis = ['urbano', 'rural', 'montanhoso', 'florestal', 'costeiro']
        pesos = [0.4, 0.3, 0.15, 0.1, 0.05]

        for node in self.grafo.nodes():
            if 'tipo_terreno' not in self.grafo.nodes[node]:
                terreno = random.choices(terrenos_possiveis, weights=pesos, k=1)[0]
                self.grafo.nodes[node]['tipo_terreno'] = terreno
        
        terreno_str = str(self.grafo.nodes[node]['tipo_terreno']).lower()
        self.estatisticas['distribuicao_terrenos'][terreno_str] += 1

    def _inicializar_recursos_veiculos(self):
        """Inicializa os recursos para cada veículo baseado em seu tipo."""
        capacidades = {
            'camião': (1000, 20),
            'drone': (10, 2),
            'helicóptero': (200, 5),
            'barco': (800, 15),
            'camioneta': (300, 6)
        }
        
        for veiculo in self.busca.estado["veiculos"]:
            peso_max, volume_max = capacidades.get(veiculo['tipo'], (100, 2))
            self.recursos_veiculos[veiculo['id']] = RecursosVeiculo(
                capacidade_peso=peso_max,
                capacidade_volume=volume_max,
                tipo_veiculo=veiculo['tipo']
            )

    def _formatar_cabecalho(self, texto: str) -> None:
        """Função auxiliar para formatar cabeçalhos de seção."""
        print("\n" + "-"*60)
        print(f"{texto:^60}")
        print("-"*60)

    def _calcular_metricas_finais(self):
        """Calcula métricas finais após a simulação."""
        if self.estatisticas['entregas_realizadas'] > 0:
            self.estatisticas['tempo_medio_restante'] = (
                self.estatisticas['total_tempo_restante'] / 
                self.estatisticas['entregas_realizadas']
            )
            self.estatisticas['eficiencia_carga_media'] = (
                self.estatisticas['eficiencia_carga_total'] / 
                self.estatisticas['entregas_realizadas']
            )

    def executar_simulacao(self, num_ciclos: int):
        """Executa a simulação ao longo de um número definido de ciclos."""
        print(f"Iniciando simulação com {num_ciclos} ciclos...\n")

        for ciclo in range(num_ciclos):
            print(f"=== Ciclo {ciclo + 1} ===")

            # Atualizar condições meteorológicas a cada 5 ciclos
            if ciclo % 5 == 0:
                self.gestor_meteo.atualizar_condicoes()
                self.gestor_meteo.imprimir_status()

            # Gerar eventos dinâmicos e atualizar seus impactos
            self.gestor_eventos.gerar_eventos_aleatorios(prob_novo_evento=0.3)
            self.gestor_eventos.atualizar_eventos()
            self.gestor_eventos.aplicar_efeitos()

            # Planejar e executar entregas para cada veículo
            for veiculo in self.busca.estado["veiculos"]:
                print(f"\nPlanejando rota para {veiculo['tipo']} (ID: {veiculo['id']})")

                # Verificar necessidade de reabastecimento
                if veiculo['combustivel'] < veiculo['autonomia'] * 0.2:
                    ponto_reabastecimento = self.planeador_reabastecimento.calcular_proximo_reabastecimento(
                        veiculo, [veiculo['localizacao']]
                    )
                    if ponto_reabastecimento:
                        print(f"Veículo {veiculo['id']} necessita reabastecimento em {ponto_reabastecimento}")
                        self.estatisticas['reabastecimentos'] += 1
                        continue

                # Planejar a rota do veículo
                rota = self.busca.busca_rota_prioritaria(veiculo['id'])
                if not rota:
                    print(f"Não foi possível encontrar uma rota válida para o veículo {veiculo['id']}")
                    self.estatisticas['rotas_bloqueadas'] += 1
                    continue

                # Calcular custos e impactos
                impactos = self.gestor_eventos.get_impacto_total(rota)
                custo_total = sum(
                    self.grafo[rota[i]][rota[i + 1]]['custo'] for i in range(len(rota) - 1)
                ) * max(1.0, impactos['impacto_custo'] * 0.6)
                tempo_total = sum(
                    self.grafo[rota[i]][rota[i + 1]]['tempo'] for i in range(len(rota) - 1)
                ) * max(1.0, impactos['impacto_tempo'] * 0.6)

                # Executar a entrega
                sucesso = self.simular_entrega(veiculo, rota, custo_total, tempo_total)
                if sucesso:
                    self.estatisticas['tempo_total'] += tempo_total

            print("\nResumo do ciclo concluído.\n")

        # Calcular métricas finais após todos os ciclos
        self._calcular_metricas_finais()
        print("Simulação concluída.")


    def simular_entrega(self, veiculo: Dict, rota: List[str], custo_total: float, tempo_total: float) -> bool:
        """Tenta realizar a entrega de um veículo para o destino."""
        if custo_total > veiculo['autonomia'] * 1.5:
            print(f"Entrega falhou: autonomia insuficiente ({custo_total:.2f} > {veiculo['autonomia']})")
            self.estatisticas['falhas_por_obstaculo'] += 1
            return False

        zona_id = rota[-1]
        if zona_id in self.busca.estado["zonas_afetadas"]:
            zona = self.busca.estado["zonas_afetadas"][zona_id]
            janela = zona["janela_tempo"]
            tempo_restante = janela.tempo_restante()

            # Atualizar métricas de tempo
            self.estatisticas['total_tempo_restante'] += tempo_restante
            if tempo_restante < (janela.duracao * 0.25):
                self.estatisticas['janelas_criticas'] += 1
            if not janela.esta_acessivel():
                self.estatisticas['entregas_fora_janela'] += 1
                print(f"Entrega fora da janela de tempo para zona {zona_id}")
                return False

            self.estatisticas['entregas_dentro_janela'] += 1

        for i in range(len(rota) - 1):
            edge = (rota[i], rota[i + 1])
            if edge in self.gestor_eventos.eventos:
                if random.random() < 0.25:
                    print(f"Entrega falhou devido a um evento dinâmico em {edge}")
                    self.estatisticas['falhas_por_evento'] += 1
                    return False

        # Atualizar veículo e estatísticas
        veiculo['localizacao'] = rota[-1]
        veiculo['combustivel'] -= custo_total
        terreno_destino = str(self.grafo.nodes[rota[-1]]['tipo_terreno']).lower()
        self.estatisticas['entregas_por_terreno'][terreno_destino] += 1
        self.estatisticas['entregas_realizadas'] += 1
        self.estatisticas['sucessos_por_tipo_veiculo'][veiculo['tipo']] += 1
        print(f"Entrega realizada no terreno {terreno_destino.capitalize()} com o veículo {veiculo['tipo']}.")
        return True

    def imprimir_estatisticas(self):
        # Seção 1: Estatísticas Gerais
        print("\n" + "-"*60)
        print(f"{'MÉTRICAS GERAIS':^60}")
        print("-"*60)
        metricas_gerais = [
            ["Entregas Realizadas", self.estatisticas['entregas_realizadas']],
            ["Entregas Falhas", self.estatisticas['entregas_falhas']],
            ["Rotas Bloqueadas", self.estatisticas['rotas_bloqueadas']]
        ]
        print(tabulate(metricas_gerais, tablefmt="simple"))

        # Seção 2: Estatísticas de Janela de Tempo
        print("\n" + "-"*60)
        print(f"{'MÉTRICAS DE JANELA DE TEMPO':^60}")
        print("-"*60)
        metricas_tempo = [
            ["Entregas Dentro da Janela", self.estatisticas['entregas_dentro_janela']],
            ["Entregas Fora da Janela", self.estatisticas['entregas_fora_janela']],
            ["Zonas Expiradas", self.estatisticas['zonas_expiradas']],
            ["Janelas Críticas (<25% tempo)", self.estatisticas['janelas_criticas']]
        ]
        if self.estatisticas['entregas_dentro_janela'] > 0:
            tempo_medio = self.estatisticas['tempo_medio_restante'] / self.estatisticas['entregas_dentro_janela']
            metricas_tempo.append(["Tempo Médio Restante (min)", f"{tempo_medio:.2f}"])
        print(tabulate(metricas_tempo, tablefmt="simple"))

        # Seção 3: Análise de Falhas
        print("\n" + "-"*60)
        print(f"{'ANÁLISE DE FALHAS':^60}")
        print("-"*60)
        metricas_falhas = [
            ["Por Clima", self.estatisticas['falhas_por_clima']],
            ["Por Obstáculos", self.estatisticas['falhas_por_obstaculo']],
            ["Por Eventos", self.estatisticas['falhas_por_evento']],
            ["Por Terreno", self.estatisticas['falhas_por_terreno']]
        ]
        print(tabulate(metricas_falhas, tablefmt="simple"))

        # Seção 4: Distribuição de Terrenos 
    
        print("\n" + "-" * 60)
        print(f"{'DISTRIBUIÇÃO POR TIPO DE TERRENO':^60}")
        print("-" * 60)

        terrenos_data = []
        total_entregas = sum(self.estatisticas['entregas_por_terreno'].values())
        total_acessos = sum(self.estatisticas['acessos_por_terreno'].values())

        for terreno in ['urbano', 'rural', 'montanhoso', 'florestal', 'costeiro']:
            entregas = self.estatisticas['entregas_por_terreno'][terreno]
            acessos = self.estatisticas['acessos_por_terreno'][terreno]
            percentual = (entregas / max(total_entregas, 1)) * 100
            terrenos_data.append([terreno.capitalize(), entregas, acessos, f"{percentual:.1f}%"])

        print(tabulate(terrenos_data, headers=["Tipo de Terreno", "Entregas", "Acessos", "Percentual"], tablefmt="simple"))

        # Estatísticas de Veículo
        print("\n" + "-" * 60)
        print(f"{'DESEMPENHO POR TIPO DE VEÍCULO':^60}")
        print("-" * 60)

        veiculos_data = []
        for tipo_veiculo, sucessos in self.estatisticas['sucessos_por_tipo_veiculo'].items():
            falhas = self.estatisticas['falhas_por_tipo_veiculo'].get(tipo_veiculo, 0)
            taxa_sucesso = (sucessos / max(sucessos + falhas, 1)) * 100
            veiculos_data.append([tipo_veiculo.capitalize(), sucessos, falhas, f"{taxa_sucesso:.1f}%"])

        print(tabulate(veiculos_data, headers=["Tipo", "Sucessos", "Falhas", "Taxa Sucesso"], tablefmt="simple"))

        # Seção 6: Impacto por Densidade Populacional
        print("\n" + "-"*60)
        print(f"{'IMPACTO POR DENSIDADE POPULACIONAL':^60}")
        print("-"*60)
        densidade_data = [
            ["Alta Densidade", self.estatisticas['impacto_populacao_alta']],
            ["Baixa Densidade", self.estatisticas['impacto_populacao_baixa']]
        ]
        print(tabulate(densidade_data, tablefmt="simple"))

        # Métricas Finais
        print("\n" + "="*60)
        print(f"{'MÉTRICAS FINAIS':^60}")
        print("="*60)
        if self.estatisticas['entregas_realizadas'] > 0:
            tempo_medio = self.estatisticas['tempo_total'] / self.estatisticas['entregas_realizadas']
            print(f"\nTempo Médio por Entrega: {tempo_medio:.2f} minutos")
        
        total_entregas = self.estatisticas['entregas_realizadas'] + self.estatisticas['entregas_falhas']
        if total_entregas > 0:
            taxa_sucesso = (self.estatisticas['entregas_realizadas'] / total_entregas) * 100
            print(f"Taxa de Sucesso Global: {taxa_sucesso:.2f}%")
        print("\n" + "="*60)

def main():
    # Configurações da simulação
    NUM_PONTOS_ENTREGA = 30
    NUM_CICLOS = 50
    
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
