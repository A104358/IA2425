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
        
        # Initialize the state with predefined refueling stations
        self._inicializar_postos_reabastecimento()
        self._inicializar_terrenos()
        self._inicializar_recursos_veiculos()
    
    def _inicializar_estatisticas(self) -> Dict:
        """Inicializa o dicionário de estatísticas com valores zerados."""
        return {
            # Métricas básicas de entrega
            'entregas_realizadas': 0,
            'entregas_falhas': 0,
            'rotas_bloqueadas': 0,
            'tempo_total': 0,
            
            # Métricas de falha detalhadas
            'falhas_por_clima': 0,
            'falhas_por_obstaculo': 0,
            'falhas_por_evento': 0,
            'falhas_por_terreno': 0,
            'falhas_por_carga': 0,
            
            # Métricas de terreno
            'distribuicao_terrenos': Counter({
                'urbano': 0,
                'rural': 0,
                'montanhoso': 0,
                'florestal': 0,
                'costeiro': 0
            }),
            'acessos_por_terreno': Counter({
                'urbano': 0,
                'rural': 0,
                'montanhoso': 0,
                'florestal': 0,
                'costeiro': 0
            }),
            'entregas_por_terreno': Counter({
                'urbano': 0,
                'rural': 0,
                'montanhoso': 0,
                'florestal': 0,
                'costeiro': 0
            }),
            
            # Métricas por tipo de veículo
            'sucessos_por_tipo_veiculo': Counter({
                'camião': 0,
                'drone': 0,
                'helicóptero': 0,
                'barco': 0,
                'camioneta': 0
            }),
            'falhas_por_tipo_veiculo': Counter({
                'camião': 0,
                'drone': 0,
                'helicóptero': 0,
                'barco': 0,
                'camioneta': 0
            }),
            
            # Métricas de população
            'impacto_populacao_alta': 0,
            'impacto_populacao_baixa': 0,
            
            # Métricas de tempo
            'tempo_medio_restante': 0,
            'total_tempo_restante': 0,
            'zonas_expiradas': 0,
            'janelas_criticas': 0,
            'entregas_dentro_janela': 0,
            'entregas_fora_janela': 0,
            
            # Métricas de eficiência
            'eficiencia_carga_total': 0,
            
            # Métricas de reabastecimento
            'reabastecimentos': 0,
            'reabastecimentos_por_regiao': Counter({
                'Norte': 0,
                'Centro': 0,
                'Lisboa': 0,
                'Alentejo': 0,
                'Algarve': 0
            }),
            'tentativas_reabastecimento': 0,
            'reabastecimentos_falhos': 0,
            'combustivel_total_reabastecido': 0.0,
            'distancia_media_reabastecimento': 0.0,
            'total_distancia_reabastecimento': 0.0
        }
    
    def _inicializar_terrenos(self):
        """Inicializa e valida os tipos de terreno para todos os nós do grafo."""
        terrenos_validos = {'urbano', 'rural', 'montanhoso', 'florestal', 'costeiro'}
        
        for node in self.grafo.nodes():
            # Pular postos de reabastecimento e base
            if 'POSTO_' in str(node) or node == 'BASE_LISBOA':
                continue
                
            node_data = self.grafo.nodes[node]
            
            # Verificar e corrigir tipo de terreno
            if 'tipo_terreno' not in node_data or node_data['tipo_terreno'] not in terrenos_validos:
                terreno = random.choices(
                    list(terrenos_validos),
                    weights=[0.4, 0.3, 0.15, 0.1, 0.05],
                    k=1
                )[0]
                node_data['tipo_terreno'] = terreno
                self.estatisticas['distribuicao_terrenos'][terreno] += 1
            else:
                self.estatisticas['distribuicao_terrenos'][node_data['tipo_terreno']] += 1
            
            # Verificar e corrigir densidade populacional
            if 'densidade_populacional' not in node_data:
                densidade = random.choices(
                    ['alta', 'normal', 'baixa'],
                    weights=[0.3, 0.4, 0.3],
                    k=1
                )[0]
                node_data['densidade_populacional'] = densidade
                
                if densidade == 'alta':
                    self.estatisticas['impacto_populacao_alta'] += 1
                elif densidade == 'baixa':
                    self.estatisticas['impacto_populacao_baixa'] += 1
                    
            print(f"Node {node}: Terreno={node_data['tipo_terreno']}, "
                f"Densidade={node_data['densidade_populacional']}")
            
    def _inicializar_postos_reabastecimento(self):
        """Initialize predefined refueling stations in the simulation state."""
        if 'postos_reabastecimento' not in self.busca.estado:
            self.busca.estado['postos_reabastecimento'] = {
                'Norte': 'POSTO_NORTE',
                'Centro': 'POSTO_CENTRO',
                'Lisboa': 'POSTO_LISBOA',
                'Alentejo': 'POSTO_ALENTEJO',
                'Algarve': 'POSTO_ALGARVE'
            }
            print("Postos de reabastecimento inicializados:")
            for regiao, posto in self.busca.estado['postos_reabastecimento'].items():
                if posto in self.grafo:
                    print(f"- {posto} na região {regiao}")
                else:
                    print(f"Aviso: {posto} não encontrado no grafo")

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

    def simular_entrega(self, veiculo: Dict, rota: List[str], custo_total: float, tempo_total: float) -> bool:
        """Tenta realizar a entrega de um veículo para o destino."""
        # Verificar se é uma rota de reabastecimento
        destino = rota[-1]
        is_reabastecimento = any(posto in destino for posto in ['POSTO_'])
        
        # Verificar autonomia com margem de segurança
        combustivel_necessario = custo_total * 1.1  # 10% de margem de segurança
        if combustivel_necessario > veiculo['combustivel']:
            print(f"Entrega falhou: combustível insuficiente ({veiculo['combustivel']:.2f} < {combustivel_necessario:.2f})")
            self.estatisticas['falhas_por_obstaculo'] += 1
            if not is_reabastecimento:
                self.estatisticas['entregas_falhas'] += 1
            return False

        # Verificar condições meteorológicas apenas para entregas normais
        if not is_reabastecimento:
            condicoes_adversas = self.gestor_meteo.verificar_condicoes_adversas(rota)
            if condicoes_adversas:
                print(f"Entrega falhou: condições meteorológicas adversas")
                self.estatisticas['falhas_por_clima'] += 1
                self.estatisticas['entregas_falhas'] += 1
                return False

            # Verificar janela de tempo apenas para entregas normais
            zona_id = destino
            if zona_id in self.busca.estado["zonas_afetadas"]:
                zona = self.busca.estado["zonas_afetadas"][zona_id]
                janela = zona["janela_tempo"]
                tempo_restante = janela.tempo_restante()

                self.estatisticas['total_tempo_restante'] += tempo_restante
                if tempo_restante < (janela.duracao * 0.25):
                    self.estatisticas['janelas_criticas'] += 1
                if not janela.esta_acessivel():
                    self.estatisticas['entregas_fora_janela'] += 1
                    print(f"Entrega fora da janela de tempo para zona {zona_id}")
                    return False
                self.estatisticas['entregas_dentro_janela'] += 1

        # Verificar compatibilidade de terreno e atualizar estatísticas
        for node in rota:
            if node in self.grafo and not any(posto in node for posto in ['POSTO_', 'BASE_']):
                terreno = self.grafo.nodes[node].get('tipo_terreno', 'urbano')
                if not self._verificar_compatibilidade_terreno(veiculo['tipo'], terreno):
                    print(f"Entrega falhou: veículo {veiculo['tipo']} incompatível com terreno {terreno} em {node}")
                    self.estatisticas['falhas_por_terreno'] += 1
                    if not is_reabastecimento:
                        self.estatisticas['entregas_falhas'] += 1
                    return False

                # Atualizar estatísticas de terreno para entregas normais
                if not is_reabastecimento:
                    self.estatisticas['acessos_por_terreno'][terreno] = \
                        self.estatisticas['acessos_por_terreno'].get(terreno, 0) + 1

        # Verificar eventos dinâmicos apenas para entregas normais
        if not is_reabastecimento:
            for i in range(len(rota) - 1):
                edge = (rota[i], rota[i + 1])
                if edge in self.gestor_eventos.eventos:
                    if random.random() < 0.25:  # 25% de chance de falha por evento
                        print(f"Entrega falhou devido a um evento dinâmico em {edge}")
                        self.estatisticas['falhas_por_evento'] += 1
                        self.estatisticas['falhas_por_tipo_veiculo'][veiculo['tipo']] = \
                            self.estatisticas['falhas_por_tipo_veiculo'].get(veiculo['tipo'], 0) + 1
                        return False

        # Atualizar veículo e estatísticas
        veiculo['localizacao'] = destino
        veiculo['combustivel'] -= custo_total
        
        if is_reabastecimento:
            # Realizar reabastecimento
            combustivel_anterior = veiculo['combustivel']
            veiculo['combustivel'] = veiculo['autonomia']  # Reabastecimento completo
            
            regiao = next((reg for reg, posto in self.busca.estado['postos_reabastecimento'].items()
                        if posto == destino), 'desconhecida')
            
            self.estatisticas['reabastecimentos'] += 1
            self.estatisticas['reabastecimentos_por_regiao'][regiao] += 1
            combustivel_reabastecido = veiculo['autonomia'] - combustivel_anterior
            self.estatisticas['combustivel_total_reabastecido'] += combustivel_reabastecido
            
            print(f"Reabastecimento realizado com sucesso em {regiao}")
            print(f"- Combustível anterior: {combustivel_anterior:.2f}")
            print(f"- Combustível atual: {veiculo['combustivel']:.2f}")
            print(f"- Quantidade reabastecida: {combustivel_reabastecido:.2f}")
        else:
            # Atualizar estatísticas para entregas normais
            self.estatisticas['entregas_realizadas'] += 1
            self.estatisticas['sucessos_por_tipo_veiculo'][veiculo['tipo']] = \
                self.estatisticas['sucessos_por_tipo_veiculo'].get(veiculo['tipo'], 0) + 1
            
            # Atualizar estatísticas de terreno para o destino
            if destino in self.grafo:
                terreno_destino = self.grafo.nodes[destino].get('tipo_terreno', 'urbano')
                self.estatisticas['entregas_por_terreno'][terreno_destino] = \
                    self.estatisticas['entregas_por_terreno'].get(terreno_destino, 0) + 1
            
            print(f"Entrega realizada com sucesso usando {veiculo['tipo']} (Combustível restante: {veiculo['combustivel']:.2f})")

        return True

    def _verificar_compatibilidade_terreno(self, tipo_veiculo: str, terreno: str) -> bool:
        """Define compatibilidade entre tipos de veículos e terrenos."""
        compatibilidade = {
            'camião': {'urbano', 'rural'},
            'drone': {'urbano', 'rural', 'montanhoso', 'florestal'},
            'helicóptero': {'urbano', 'rural', 'montanhoso', 'florestal'},
            'barco': {'costeiro'},
            'camioneta': {'urbano', 'rural', 'florestal'}
        }
        return terreno in compatibilidade.get(tipo_veiculo, set())
    
    def executar_simulacao(self, num_ciclos: int):
        print(f"Iniciando simulação com {num_ciclos} ciclos...\n")
        
        for ciclo in range(num_ciclos):
            print(f"\n=== Ciclo {ciclo + 1} ===")

            # Atualizar condições meteorológicas
            if ciclo % 5 == 0:
                self.gestor_meteo.atualizar_condicoes()
                self.gestor_meteo.imprimir_status()

            # Atualizar eventos dinâmicos
            self.gestor_eventos.gerar_eventos_aleatorios(prob_novo_evento=0.3)
            self.gestor_eventos.atualizar_eventos()
            self.gestor_eventos.aplicar_efeitos()

            # Processar cada veículo
            for veiculo in self.busca.estado["veiculos"]:
                print(f"\nPlanejando rota para {veiculo['tipo']} (ID: {veiculo['id']})")
                
                # Verificar necessidade de reabastecimento (60% da autonomia)
                if veiculo['combustivel'] <= veiculo['autonomia'] * 0.6:
                    self.estatisticas['tentativas_reabastecimento'] += 1
                    print(f"Veículo {veiculo['id']} com combustível baixo: {veiculo['combustivel']:.2f}")
                    
                    necessita_reabastecimento, rota_reabastecimento = (
                        self.planeador_reabastecimento.calcular_proximo_reabastecimento(
                            veiculo, [veiculo['localizacao']]
                        )
                    )

                    if necessita_reabastecimento and rota_reabastecimento:
                        print(f"Rota de reabastecimento encontrada: {rota_reabastecimento}")
                        
                        # Calcular custo total da rota até o posto
                        custo_total = sum(self.grafo[rota_reabastecimento[i]][rota_reabastecimento[i + 1]]['custo']
                                        for i in range(len(rota_reabastecimento) - 1))
                        
                        # Tentar realizar o reabastecimento
                        if self.simular_entrega(veiculo, rota_reabastecimento, custo_total, 0):
                            continue
                        
                        self.estatisticas['reabastecimentos_falhos'] += 1
                        print(f"Falha no reabastecimento: não foi possível alcançar o posto")
                        continue

                # Buscar próxima rota normal
                rota = self.busca.busca_rota_prioritaria(veiculo['id'])
                if not rota:
                    print(f"Veículo {veiculo['id']} não encontrou rota válida.")
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
                    print(f"Rota completa: {' -> '.join(rota)}")

            print("\nResumo do ciclo concluído.")

        # Calcular métricas finais após todos os ciclos
        self._calcular_metricas_finais()
        print("\nSimulação concluída.")
        
    def imprimir_estatisticas(self):

        # Seção 1: Estatísticas Gerais
        print("\n" + "-"*60)
        print(f"{'MÉTRICAS GERAIS':^60}")
        print("-"*60)
        metricas_gerais = [
            ["Entregas Realizadas", self.estatisticas['entregas_realizadas']],
            ["Entregas Falhadas", self.estatisticas['entregas_falhas']],
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

        # Nova seção: Estatísticas de Reabastecimento
        print("\n" + "-"*60)
        print(f"{'ESTATÍSTICAS DE REABASTECIMENTO':^60}")
        print("-"*60)
        
        reabastecimento_data = [
            ["Total de Reabastecimentos", self.estatisticas['reabastecimentos']],
            ["Tentativas de Reabastecimento", self.estatisticas['tentativas_reabastecimento']],
            ["Reabastecimentos Falhados", self.estatisticas['reabastecimentos_falhos']],
            ["Combustível Total Reabastecido", f"{self.estatisticas['combustivel_total_reabastecido']:.2f}"]
        ]
        
        if self.estatisticas['reabastecimentos'] > 0:
            dist_media = (self.estatisticas['total_distancia_reabastecimento'] / 
                         self.estatisticas['reabastecimentos'])
            reabastecimento_data.append(["Distância Média até Posto", f"{dist_media:.2f}"])

        print(tabulate(reabastecimento_data, tablefmt="simple"))

        print("\nReabastecimentos por Região:")
        regiao_data = [[regiao, count] for regiao, count in 
                      self.estatisticas['reabastecimentos_por_regiao'].most_common()]
        print(tabulate(regiao_data, headers=["Região", "Quantidade"], tablefmt="simple"))

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
    NUM_PONTOS_ENTREGA = 100
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
