import pandas as pd
from datetime import datetime, timedelta
import random
from collections import defaultdict
from escala_bd_consultas import GestorBaseDados

class GeradorEscala:
    """
    Classe para gerar escalas de permanências equilibradas
    """
    
    def __init__(self, gestor_bd, df_folgas):
        """
        Args:
            gestor_bd: Instância de GestorBaseDados
            df_folgas: DataFrame com folgas/férias do Excel
        """
        self.gestor = gestor_bd
        self.df_folgas = df_folgas
        self.escala = {}  # {data: {'Manhã': pessoa, 'Tarde': pessoa}}
        self.contador_permanencias = defaultdict(int)
        self.historico_turnos = []  # [(data, pessoa, turno)]
    
    def obter_pessoas_disponiveis_dia(self, data, turno):
        """
        Retorna pessoas disponíveis para um dia e turno específico
        Considera: disponibilidade no Excel, configuração de turno, e permanências fixas
        """
        # 1. Obter pessoas disponíveis no Excel (sem FOLGA/FÉRIAS/etc)
        from escala_ler_excel import obter_pessoas_disponiveis
        pessoas_excel = obter_pessoas_disponiveis(self.df_folgas, data)
        
        if not pessoas_excel:
            return []
        
        # 2. Obter pessoas que podem fazer este turno na BD
        pessoas_turno_bd = self.gestor.obter_pessoas_por_turno(turno)
        nomes_turno = [nome for _, nome in pessoas_turno_bd]
        
        # 3. Interseção: disponíveis no Excel E podem fazer o turno
        disponiveis = [p for p in pessoas_excel if p in nomes_turno]
        
        # 4. Verificar se já está escalada no outro turno do mesmo dia
        data_str = data.strftime('%Y-%m-%d')
        if data_str in self.escala:
            outro_turno = 'Tarde' if turno == 'Manhã' else 'Manhã'
            if outro_turno in self.escala[data_str]:
                pessoa_outro_turno = self.escala[data_str][outro_turno]
                if pessoa_outro_turno in disponiveis:
                    disponiveis.remove(pessoa_outro_turno)
        
        return disponiveis
    
    def verificar_restricoes(self, pessoa, data, turno):
        """
        Verifica se pessoa pode ser escalada considerando:
        - Máximo 2 dias consecutivos
        - Se esteve à Tarde, não pode estar Manhã no dia seguinte
        - Máximo 3 permanências por semana
        """
        data_str = data.strftime('%Y-%m-%d')
        
        # Verificar dias consecutivos
        dias_consecutivos = self._contar_dias_consecutivos(pessoa, data)
        if dias_consecutivos >= 2:
            return False
        
        # Verificar regra: Tarde seguida de Manhã
        dia_anterior = data - timedelta(days=1)
        dia_anterior_str = dia_anterior.strftime('%Y-%m-%d')
        
        if turno == 'Manhã' and dia_anterior_str in self.escala:
            if 'Tarde' in self.escala[dia_anterior_str]:
                if self.escala[dia_anterior_str]['Tarde'] == pessoa:
                    return False
        
        # Verificar máximo 3 permanências por semana
        permanencias_semana = self._contar_permanencias_semana(pessoa, data)
        if permanencias_semana >= 3:
            return False
        
        return True
    
    def _contar_dias_consecutivos(self, pessoa, data_atual):
        """
        Conta quantos dias consecutivos a pessoa já está escalada antes desta data
        """
        contador = 0
        data_verificar = data_atual - timedelta(days=1)
        
        for _ in range(10):  # Verificar até 10 dias atrás
            data_str = data_verificar.strftime('%Y-%m-%d')
            
            if data_str not in self.escala:
                break
            
            pessoa_manha = self.escala[data_str].get('Manhã', '')
            pessoa_tarde = self.escala[data_str].get('Tarde', '')
            
            if pessoa in [pessoa_manha, pessoa_tarde]:
                contador += 1
                data_verificar -= timedelta(days=1)
            else:
                break
        
        return contador
    
    def _contar_permanencias_semana(self, pessoa, data):
        """
        Conta permanências da pessoa na semana atual (Segunda a Domingo)
        """
        # Encontrar segunda-feira da semana
        dias_desde_segunda = data.weekday()
        inicio_semana = data - timedelta(days=dias_desde_segunda)
        fim_semana = inicio_semana + timedelta(days=6)
        
        contador = 0
        data_verificar = inicio_semana
        
        while data_verificar <= fim_semana:
            data_str = data_verificar.strftime('%Y-%m-%d')
            
            if data_str in self.escala:
                pessoa_manha = self.escala[data_str].get('Manhã', '')
                pessoa_tarde = self.escala[data_str].get('Tarde', '')
                
                if pessoa in [pessoa_manha, pessoa_tarde]:
                    contador += 1
            
            data_verificar += timedelta(days=1)
        
        return contador
    
    def calcular_prioridade(self, pessoa, total_dias):
        """
        Calcula prioridade de escalar uma pessoa
        Quanto MENOR o valor, MAIOR a prioridade
        """
        # Obter configuração de percentagens da pessoa
        conn = self.gestor._conectar()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM pessoas WHERE nome = ?', (pessoa,))
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return 999999
        
        pessoa_id = resultado[0]
        perc_min, perc_max = self.gestor.obter_configuracao_pessoa(pessoa_id)
        conn.close()
        
        # Calcular percentagem atual
        permanencias_atuais = self.contador_permanencias[pessoa]
        percentagem_atual = (permanencias_atuais / total_dias * 100) if total_dias > 0 else 0
        
        # Prioridade baseada na distância da percentagem mínima
        diferenca = perc_min - percentagem_atual
        
        # Quanto mais abaixo do mínimo, maior prioridade (menor valor)
        return -diferenca
    
    def gerar_escala(self, data_inicio, data_fim):
        """
        Gera escala completa para o período especificado
        """
        print("\n" + "="*80)
        print(f"GERANDO ESCALA: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
        print("="*80)
        
        # Limpar escala anterior
        self.escala = {}
        self.contador_permanencias = defaultdict(int)
        
        # Obter permanências fixas
        permanencias_fixas = self.gestor.obter_permanencias_fixas(data_inicio, data_fim)
        
        # Aplicar permanências fixas primeiro
        for data_str, turno, pessoa_id, nome in permanencias_fixas:
            if data_str not in self.escala:
                self.escala[data_str] = {}
            self.escala[data_str][turno] = nome
            self.contador_permanencias[nome] += 1
            print(f"✓ Permanência fixa: {data_str} - {turno} - {nome}")
        
        # Calcular total de dias
        total_dias = (data_fim - data_inicio).days + 1
        
        # Iterar por cada dia
        data_atual = data_inicio
        while data_atual <= data_fim:
            data_str = data_atual.strftime('%Y-%m-%d')
            
            # Criar entrada se não existir
            if data_str not in self.escala:
                self.escala[data_str] = {}
            
            # Processar cada turno
            for turno in ['Manhã', 'Tarde']:
                # Verificar se já tem permanência fixa
                if turno in self.escala[data_str]:
                    continue
                
                # Obter pessoas disponíveis
                disponiveis = self.obter_pessoas_disponiveis_dia(data_atual, turno)
                
                if not disponiveis:
                    print(f"⚠ {data_str} - {turno}: NENHUMA PESSOA DISPONÍVEL")
                    self.escala[data_str][turno] = "SEM COBERTURA"
                    continue
                
                # Filtrar por restrições
                candidatos = [p for p in disponiveis if self.verificar_restricoes(p, data_atual, turno)]
                
                if not candidatos:
                    # Se ninguém passa restrições, usar quem está disponível
                    candidatos = disponiveis
                
                # Ordenar por prioridade (quem tem menos permanências)
                candidatos_prioridade = sorted(
                    candidatos,
                    key=lambda p: self.calcular_prioridade(p, total_dias)
                )
                
                # Escolher pessoa com maior prioridade
                pessoa_escolhida = candidatos_prioridade[0]
                self.escala[data_str][turno] = pessoa_escolhida
                self.contador_permanencias[pessoa_escolhida] += 1
            
            data_atual += timedelta(days=1)
        
        print("\n✓ Escala gerada com sucesso!")
        self._mostrar_estatisticas(total_dias)
        
        return self.escala
    
    def _mostrar_estatisticas(self, total_dias):
        """
        Mostra estatísticas da escala gerada
        """
        print("\n" + "="*80)
        print("ESTATÍSTICAS DA ESCALA")
        print("="*80)
        print(f"{'Pessoa':<25} {'Permanências':<15} {'Percentagem':<15}")
        print("-"*80)
        
        for pessoa in sorted(self.contador_permanencias.keys()):
            perm = self.contador_permanencias[pessoa]
            perc = (perm / total_dias * 100) if total_dias > 0 else 0
            print(f"{pessoa:<25} {perm:<15} {perc:<14.1f}%")
        
        print("="*80)
    
    def exportar_para_excel(self, caminho_saida='escala_gerada.xlsx'):
        """
        Exporta escala gerada para Excel com estatísticas
        """
        if not self.escala:
            print("✗ Nenhuma escala gerada ainda")
            return
        
        try:
            # Criar DataFrame principal da escala
            dados = []
            
            for data_str in sorted(self.escala.keys()):
                data_obj = datetime.strptime(data_str, '%Y-%m-%d')
                dia_semana = data_obj.strftime('%A')
                
                # Traduzir dia da semana para português
                dias_pt = {
                    'Monday': 'Segunda',
                    'Tuesday': 'Terça',
                    'Wednesday': 'Quarta',
                    'Thursday': 'Quinta',
                    'Friday': 'Sexta',
                    'Saturday': 'Sábado',
                    'Sunday': 'Domingo'
                }
                dia_semana_pt = dias_pt.get(dia_semana, dia_semana)
                
                manha = self.escala[data_str].get('Manhã', '')
                tarde = self.escala[data_str].get('Tarde', '')
                
                dados.append({
                    'Data': data_obj.strftime('%d/%m/%Y'),
                    'Dia da Semana': dia_semana_pt,
                    'Manhã': manha,
                    'Tarde': tarde
                })
            
            df_escala = pd.DataFrame(dados)
            
            # CALCULAR ESTATÍSTICAS
            estatisticas = self._calcular_estatisticas_detalhadas()
            
            # Criar Excel writer
            with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
                # Escrever escala principal
                df_escala.to_excel(writer, sheet_name='Escala', index=False)
                
                # Escrever estatísticas
                estatisticas.to_excel(writer, sheet_name='Estatísticas', index=False)
                
                # Ajustar largura das colunas
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            print(f"\n✓ Escala exportada para: {caminho_saida}")
            print(f"✓ Estatísticas incluídas na aba 'Estatísticas'")
            
        except Exception as e:
            print(f"✗ Erro ao exportar para Excel: {e}")

    def _calcular_estatisticas_detalhadas(self):
        """
        Calcula estatísticas detalhadas por pessoa
        """
        # Contar permanências por tipo
        contador_manhas = defaultdict(int)
        contador_tardes = defaultdict(int)
        contador_total = defaultdict(int)
        
        for data_str, turnos in self.escala.items():
            for turno, pessoa in turnos.items():
                if pessoa and pessoa != "SEM COBERTURA":
                    if turno == 'Manhã':
                        contador_manhas[pessoa] += 1
                    elif turno == 'Tarde':
                        contador_tardes[pessoa] += 1
                    contador_total[pessoa] += 1
        
        # Calcular totais
        total_manhas = sum(contador_manhas.values())
        total_tardes = sum(contador_tardes.values())
        total_permanencias = total_manhas + total_tardes
        
        # Criar DataFrame de estatísticas
        pessoas = sorted(set(list(contador_manhas.keys()) + list(contador_tardes.keys())))
        dados_estatisticas = []
        
        for pessoa in pessoas:
            manhas = contador_manhas[pessoa]
            tardes = contador_tardes[pessoa]
            total = contador_total[pessoa]
            
            # Calcular percentagens
            perc_manhas = (manhas / total_manhas * 100) if total_manhas > 0 else 0
            perc_tardes = (tardes / total_tardes * 100) if total_tardes > 0 else 0
            perc_total = (total / total_permanencias * 100) if total_permanencias > 0 else 0
            
            dados_estatisticas.append({
                'Pessoa': pessoa,
                'Manhãs': manhas,
                '% Manhãs': f"{perc_manhas:.1f}%",
                'Tardes': tardes,
                '% Tardes': f"{perc_tardes:.1f}%",
                'Total': total,
                '% Total': f"{perc_total:.1f}%"
            })
        
        # Adicionar linha de totais
        dados_estatisticas.append({
            'Pessoa': 'TOTAL',
            'Manhãs': total_manhas,
            '% Manhãs': '100.0%',
            'Tardes': total_tardes,
            '% Tardes': '100.0%',
            'Total': total_permanencias,
            '% Total': '100.0%'
        })
        
        return pd.DataFrame(dados_estatisticas)


# Exemplo de utilização
if __name__ == "__main__":
    from escala_ler_excel import ler_excel_folgas
    
    print("="*80)
    print("TESTE: GERAÇÃO DE ESCALA")
    print("="*80)
    
    # Criar gestor e ler Excel
    gestor = GestorBaseDados()
    df_folgas = ler_excel_folgas('escala_folgas.xlsx')
    
    if df_folgas is not None:
        # Criar gerador de escala
        gerador = GeradorEscala(gestor, df_folgas)
        
        # Gerar escala para outubro 2025
        data_inicio = datetime(2025, 10, 1)
        data_fim = datetime(2025, 10, 31)
        
        escala = gerador.gerar_escala(data_inicio, data_fim)
        
        # Exportar para Excel
        gerador.exportar_para_excel('escala_outubro_2025.xlsx')
        
        print("\n✓ Passo 5 concluído!")
        print("\nPróximos passos:")
        print("  6. Criar interface PyQt5")
        print("  7. Adicionar funcionalidades de edição manual")
