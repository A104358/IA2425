from typing import Dict, List, Counter
import networkx as nx
from estado_inicial import estado_inicial
from criar_grafo import PortugalDistributionGraph
from busca_emergencia import BuscaEmergencia
from condicoes_meteorologicas import GestorMeteorologico, CondicaoMeteorologica
from eventos_dinamicos import GestorEventos
from limitacoes_geograficas import RestricaoAcesso, TipoTerreno
from gestao_recursos import RecursosVeiculo, PlanejadorReabastecimento
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
        self.planejador_reabastecimento = PlanejadorReabastecimento(self.grafo)

        # Inicialização das estatísticas da simulação
        self.estatisticas = {
            'entregas_realizadas': 0,
            'entregas_falhas': 0,
            'rotas_bloqueadas': 0,
            'tempo_total': 0,
            'falhas_por_clima': 0,
            'falhas_por_obstaculo': 0,
            'falhas_por_evento': 0,
            'falhas_por_terreno': 0,
            'distribuicao_terrenos': Counter(),
            'acessos_por_terreno': Counter(),
            'sucessos_por_tipo_veiculo': Counter(),
            'falhas_por_tipo_veiculo': Counter(),
            'impacto_populacao_alta': 0,
            'impacto_populacao_baixa': 0,
            'tempo_medio_restante': 0,
            'zonas_expiradas': 0,
            'janelas_criticas': 0,
            'entregas_dentro_janela': 0,
            'entregas_fora_janela': 0,
            'eficiencia_carga_media': 0,  # Inicializado
        }

        self.recursos_veiculos = {}
        self._inicializar_terrenos()
        self._inicializar_recursos_veiculos()

    def _inicializar_terrenos(self):
        """Inicializa tipos de terrenos para todos os nodos no grafo."""
        terrenos_possiveis = ['urbano', 'rural', 'montanhoso', 'florestal', 'costeiro']

        self.estatisticas['distribuicao_terrenos'] = Counter()
        self.estatisticas['acessos_por_terreno'] = Counter()

        for node in self.grafo.nodes():
            if 'tipo_terreno' not in self.grafo.nodes[node]:
                # Distribuir terrenos aleatoriamente com pesos ajustados
                terreno = random.choices(
                    terrenos_possiveis, 
                    weights=[0.4, 0.2, 0.2, 0.1, 0.1],  # Pesos ajustados para balancear
                    k=1
                )[0]
                self.grafo.nodes[node]['tipo_terreno'] = terreno

            terreno_str = str(self.grafo.nodes[node]['tipo_terreno'])
            self.estatisticas['distribuicao_terrenos'][terreno_str] += 1

    def _inicializar_recursos_veiculos(self):
        """Inicializa os recursos para cada veículo baseado em seu tipo."""
        for veiculo in self.busca.estado["veiculos"]:
            capacidades = {
                'camião': (1000, 20),  # (peso em kg, volume em m³)
                'drone': (10, 2),
                'helicóptero': (200, 5),
                'barco': (800, 15),
                'camioneta': (300, 6)
            }
            # Valores padrão caso o tipo do veículo não esteja no dicionário
            peso_max, volume_max = capacidades.get(veiculo['tipo'], (100, 2))
            
            # Cria uma instância de RecursosVeiculo
            self.recursos_veiculos[veiculo['id']] = RecursosVeiculo(
                capacidade_peso=peso_max,
                capacidade_volume=volume_max,
                tipo_veiculo=veiculo['tipo']
            )

    def _inicializar_janela_tempo(self, zona_id: str) -> JanelaTempoZona:
        """Inicializa uma janela de tempo padrão para uma zona."""
        inicio = datetime.now()
        duracao_base = random.randint(4, 12)  # Definir duração base da janela em horas
        prioridade = self.busca.estado["zonas_afetadas"][zona_id]["prioridade"]  # Obter a prioridade da zona
        return JanelaTempoZona(zona_id, inicio, duracao_base, prioridade)


    def executar_simulacao(self, num_ciclos: int):
        print(f"Iniciando simulação com {num_ciclos} ciclos...")
        for ciclo in range(num_ciclos):
            print(f"\n=== Ciclo {ciclo + 1} ===")
            
            # Atualização de condições a cada 5 ciclos
            if ciclo % 5 == 0:
                self.gestor_meteo.atualizar_condicoes()
                self.gestor_meteo.imprimir_status()
                
            self.gestor_eventos.gerar_eventos_aleatorios(prob_novo_evento=0.3)
            self.gestor_eventos.atualizar_eventos()
            self.gestor_eventos.aplicar_efeitos()

            for veiculo in self.busca.estado["veiculos"]:
                print(f"\nPlanejando rota para {veiculo['tipo']} (ID: {veiculo['id']})")
                
                # Verificar se precisa reabastecimento
                if veiculo['combustivel'] < veiculo['autonomia'] * 0.2:
                    ponto_reabastecimento = self.planejador_reabastecimento.calcular_proximo_reabastecimento(veiculo, [veiculo['localizacao']])
                    if ponto_reabastecimento:
                        print(f"Veículo {veiculo['id']} necessita reabastecimento em {ponto_reabastecimento}")
                        self.estatisticas['reabastecimentos'] += 1
                        continue

                node_atual = veiculo['localizacao']
                tipo_terreno = self.grafo.nodes[node_atual]['tipo_terreno']
                self.estatisticas['acessos_por_terreno'][tipo_terreno] += 1

                if not self.restricao_acesso.pode_acessar(veiculo['tipo'], TipoTerreno(tipo_terreno)):
                    print(f"Veículo {veiculo['id']} não pode acessar terreno {tipo_terreno}")
                    self.estatisticas['falhas_por_terreno'] += 1
                    continue

                # Buscar rota considerando recursos
                rota = self.busca.busca_rota_prioritaria(veiculo['id'])
                if not rota:
                    print("Não foi possível encontrar uma rota válida")
                    self.estatisticas['rotas_bloqueadas'] += 1
                    continue

                # Verificar capacidade de carga
                recursos_veiculo = self.recursos_veiculos[veiculo['id']]
                if recursos_veiculo.peso_atual >= recursos_veiculo.capacidade_peso * 0.9:
                    print(f"Veículo {veiculo['id']} está próximo da capacidade máxima")
                    self.estatisticas['falhas_por_carga'] += 1
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
                    
                    # Atualizar eficiência de carga
                    recursos_veiculo = self.recursos_veiculos[veiculo['id']]
                    self.estatisticas['eficiencia_carga_media'] += recursos_veiculo.calcular_eficiencia_carga()
                else:
                    self.estatisticas['entregas_falhas'] += 1
                    self.estatisticas['falhas_por_tipo_veiculo'][veiculo['tipo']] += 1

            # Atualizar média de eficiência de carga
            if self.estatisticas['entregas_realizadas'] > 0:
                self.estatisticas['eficiencia_carga_media'] /= self.estatisticas['entregas_realizadas']
            
            # Normalizar a eficiência média no final da simulação
            if len(self.recursos_veiculos) > 0:
                self.estatisticas['eficiencia_carga_media'] /= len(self.recursos_veiculos)


    def simular_entrega(self, veiculo: Dict, rota: List[str], custo_total: float, tempo_total: float) -> bool:
        # Verificar autonomia com margem de segurança
        if custo_total > veiculo['autonomia'] * 1.5:
            print(f"Entrega falhou: autonomia insuficiente ({custo_total:.2f} > {veiculo['autonomia']})")
            self.estatisticas['falhas_por_obstaculo'] += 1
            return False

        # Verificar janela de tempo
        zona_id = rota[-1]
        if zona_id in self.busca.estado["zonas_afetadas"]:
            zona = self.busca.estado["zonas_afetadas"][zona_id]
            janela = zona.get("janela_tempo", self._inicializar_janela_tempo(zona_id))
            
            if janela.esta_acessivel():
                tempo_restante = janela.tempo_restante()
                self.estatisticas['tempo_medio_restante'] += tempo_restante
                
                if janela.esta_em_periodo_critico():
                    self.estatisticas['janelas_criticas'] += 1
                self.estatisticas['entregas_dentro_janela'] += 1
            else:
                self.estatisticas['entregas_fora_janela'] += 1
                print(f"Entrega fora da janela de tempo para zona {zona_id}")
                return False

        # Verificar eventos dinâmicos
        for i in range(len(rota) - 1):
            edge = (rota[i], rota[i + 1])
            if edge in self.gestor_eventos.eventos:
                if random.random() < 0.25:
                    print(f"Entrega falhou devido a um evento dinâmico em {edge}")
                    self.estatisticas['falhas_por_evento'] += 1
                    return False

        # Atualizar posição e combustível do veículo
        veiculo['localizacao'] = rota[-1]
        veiculo['combustivel'] = max(veiculo['combustivel'] - custo_total * 0.7,
                                   veiculo['autonomia'] * 0.3)

        print(f"Entrega realizada com sucesso! Novo nível de combustível: {veiculo['combustivel']:.2f}")
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
        """Imprime as estatísticas de distribuição de terrenos."""
        print("\n" + "-" * 60)
        print(f"{'DISTRIBUIÇÃO DE TERRENOS':^60}")
        print("-" * 60)

        terrenos_data = []
        total_acessos = sum(self.estatisticas['acessos_por_terreno'].values())

        for terreno, count in sorted(self.estatisticas['distribuicao_terrenos'].items()):
            # Considere apenas os terrenos esperados
            if terreno not in ['costeiro', 'florestal', 'montanhoso', 'rural', 'urbano']:
                continue

            acessos = self.estatisticas['acessos_por_terreno'].get(terreno, 0)
            # Calcular porcentagem com base nos acessos totais
            taxa_utilizacao = (acessos / max(total_acessos, 1)) * 100
            terrenos_data.append([
                terreno.capitalize(),
                count,
                acessos,
                f"{taxa_utilizacao:.1f}%"
            ])

        print(tabulate(terrenos_data, headers=["Tipo", "Quantidade", "Acessos", "Taxa Utilização"], tablefmt="simple"))

        # Seção 5: Desempenho por Tipo de Veículo
        print("\n" + "-"*60)
        print(f"{'DESEMPENHO POR TIPO DE VEÍCULO':^60}")
        print("-"*60)
        veiculos_data = []
        for tipo in set(self.estatisticas['sucessos_por_tipo_veiculo'].keys()) | set(self.estatisticas['falhas_por_tipo_veiculo'].keys()):
            sucessos = self.estatisticas['sucessos_por_tipo_veiculo'][tipo]
            falhas = self.estatisticas['falhas_por_tipo_veiculo'][tipo]
            total = sucessos + falhas
            if total > 0:
                taxa_sucesso = (sucessos / total) * 100
                veiculos_data.append([
                    tipo.capitalize(),
                    sucessos,
                    falhas,
                    f"{taxa_sucesso:.1f}%"
                ])
        print(tabulate(veiculos_data, 
                      headers=["Tipo", "Sucessos", "Falhas", "Taxa Sucesso"],
                      tablefmt="simple"))

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
    NUM_PONTOS_ENTREGA = 60
    NUM_CICLOS = 30
    
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
