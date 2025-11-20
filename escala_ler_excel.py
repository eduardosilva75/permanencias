import pandas as pd
from datetime import datetime
import sqlite3
import os

def ler_excel_folgas(caminho_excel='escala_folgas.xlsx'):
    """
    Lê o ficheiro Excel com as folgas/férias/formação/indisponibilidades
    
    Returns:
        DataFrame com as informações processadas
    """
    if not os.path.exists(caminho_excel):
        print(f"✗ Erro: Ficheiro '{caminho_excel}' não encontrado!")
        return None
    
    try:
        # Ler o Excel
        df = pd.read_excel(caminho_excel)
        
        # Renomear primeira coluna para 'Data' se necessário
        if df.columns[0] != 'Data':
            df.rename(columns={df.columns[0]: 'Data'}, inplace=True)
        
        # CORREÇÃO: Tentar múltiplos formatos de data
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        
        # Se falhou, tentar formato específico português
        if df['Data'].isna().any():
            df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        
        # Verificar se ainda há datas inválidas
        if df['Data'].isna().any():
            print("⚠ Aviso: Algumas datas não puderam ser convertidas")
        
        print(f"✓ Excel lido com sucesso!")
        print(f"✓ Período: {df['Data'].min().strftime('%d/%m/%Y')} a {df['Data'].max().strftime('%d/%m/%Y')}")
        print(f"✓ Total de dias: {len(df)}")
        print(f"✓ Pessoas no ficheiro: {len(df.columns) - 2}")  # -2 porque tem Data e Dia da Semana
        
        return df
        
    except Exception as e:
        print(f"✗ Erro ao ler Excel: {e}")
        return None


def obter_pessoas_disponiveis(df, data):
    """
    Retorna lista de pessoas disponíveis numa determinada data
    (ou seja, que NÃO estão de FOLGA, FÉRIAS, FORMAÇÃO ou INDISPONÍVEL)
    
    Args:
        df: DataFrame com os dados do Excel
        data: Data a verificar (formato datetime ou string 'YYYY-MM-DD')
    
    Returns:
        Lista com nomes das pessoas disponíveis
    """
    if isinstance(data, str):
        try:
            data = datetime.strptime(data, '%Y-%m-%d')
        except ValueError:
            print(f"⚠ Formato de data inválido: {data}")
            return []
    
    # CORREÇÃO: Normalizar a data para comparar apenas a parte da data (sem hora)
    data_normalizada = pd.Timestamp(data).normalize()
    
    # Encontrar a linha correspondente à data
    linha = df[df['Data'].dt.normalize() == data_normalizada]
    
    if linha.empty:
        print(f"⚠ Data {data.strftime('%d/%m/%Y')} não encontrada no Excel")
        return []
    
    # Obter todas as colunas exceto 'Data' e 'Dia da Semana'
    colunas_pessoas = [col for col in df.columns if col not in ['Data', 'Dia da Semana']]
    
    # Filtrar pessoas disponíveis (célula vazia ou não contém palavras-chave de ausência)
    ausencias = ['FOLGA', 'FÉRIAS', 'FORMAÇÃO', 'INDISPONÍVEL', 'FERIAS', 'FORMACAO', 'INDISPONIVEL']
    pessoas_disponiveis = []
    
    for pessoa in colunas_pessoas:
        valor_celula = linha[pessoa].values[0]
        
        # Verificar se está disponível (célula vazia ou sem palavras de ausência)
        if pd.isna(valor_celula) or str(valor_celula).strip() == '':
            pessoas_disponiveis.append(pessoa)
        else:
            valor_upper = str(valor_celula).upper().strip()
            # CORREÇÃO: Verificar se NÃO contém palavras de ausência
            if not any(ausencia in valor_upper for ausencia in ausencias):
                pessoas_disponiveis.append(pessoa)
    
    return pessoas_disponiveis


def sincronizar_pessoas_com_bd(df):
    """
    Sincroniza as pessoas do Excel com a base de dados
    Adiciona pessoas que estão no Excel mas não estão na BD
    """
    conn = sqlite3.connect('escala_permanencias.db')
    cursor = conn.cursor()
    
    # Obter nomes das colunas (pessoas) do Excel
    colunas_pessoas = [col for col in df.columns if col not in ['Data', 'Dia da Semana']]
    
    # Obter pessoas já na base de dados
    cursor.execute('SELECT nome FROM pessoas WHERE ativo = 1')
    pessoas_bd = [row[0] for row in cursor.fetchall()]
    
    pessoas_adicionadas = []
    
    for pessoa in colunas_pessoas:
        if pessoa not in pessoas_bd:
            try:
                # Inserir pessoa
                cursor.execute('INSERT INTO pessoas (nome) VALUES (?)', (pessoa,))
                pessoa_id = cursor.lastrowid
                
                # Inserir disponibilidade padrão (Ambos os turnos)
                cursor.execute('''
                    INSERT INTO disponibilidade_turno (pessoa_id, turno) 
                    VALUES (?, 'Ambos')
                ''', (pessoa_id,))
                
                # Inserir configuração padrão (10-20%)
                cursor.execute('''
                    INSERT INTO configuracao_percentagens 
                    (pessoa_id, percentagem_min, percentagem_max)
                    VALUES (?, 10.0, 20.0)
                ''', (pessoa_id,))
                
                pessoas_adicionadas.append(pessoa)
                
            except sqlite3.IntegrityError:
                pass  # Pessoa já existe
    
    conn.commit()
    conn.close()
    
    if pessoas_adicionadas:
        print(f"\n✓ {len(pessoas_adicionadas)} pessoa(s) adicionada(s) à base de dados:")
        for p in pessoas_adicionadas:
            print(f"  - {p}")
    else:
        print("\n✓ Todas as pessoas do Excel já estão na base de dados")
    
    return pessoas_adicionadas


def mostrar_disponibilidade_periodo(df, data_inicio, data_fim):
    """
    Mostra resumo de disponibilidade num período
    """
    df_periodo = df[(df['Data'] >= data_inicio) & (df['Data'] <= data_fim)]
    
    if df_periodo.empty:
        print("Nenhum dado encontrado para o período especificado")
        return
    
    print(f"\n{'='*80}")
    print(f"DISPONIBILIDADE DE {data_inicio.strftime('%d/%m/%Y')} A {data_fim.strftime('%d/%m/%Y')}")
    print(f"{'='*80}")
    
    colunas_pessoas = [col for col in df.columns if col not in ['Data', 'Dia da Semana']]
    
    for _, row in df_periodo.iterrows():
        data_str = row['Data'].strftime('%d/%m/%Y')
        dia_semana = row['Dia da Semana']
        
        disponiveis = obter_pessoas_disponiveis(df, row['Data'])
        
        print(f"\n{data_str} ({dia_semana}) - {len(disponiveis)} disponíveis")
        print(f"  Disponíveis: {', '.join(disponiveis) if disponiveis else 'Ninguém'}")


# Exemplo de utilização
if __name__ == "__main__":
    print("="*80)
    print("LEITURA DO EXCEL DE FOLGAS")
    print("="*80)
    
    # Ler o Excel
    df = ler_excel_folgas('escala_folgas.xlsx')
    
    if df is not None:
        # Sincronizar pessoas com a base de dados
        print("\n" + "="*80)
        print("SINCRONIZAÇÃO COM BASE DE DADOS")
        print("="*80)
        sincronizar_pessoas_com_bd(df)
        
        # Exemplo: Mostrar disponibilidade da primeira semana
        if len(df) > 0:
            data_inicio = df['Data'].min()
            data_fim = df['Data'].min() + pd.Timedelta(days=6)
            mostrar_disponibilidade_periodo(df, data_inicio, data_fim)
        
        # Exemplo: Verificar disponibilidade de um dia específico
        print("\n" + "="*80)
        print("EXEMPLO: Disponibilidade do dia 01/10/2025")
        print("="*80)
        data_teste = datetime(2025, 10, 1)
        disponiveis = obter_pessoas_disponiveis(df, data_teste)
        print(f"Pessoas disponíveis: {', '.join(disponiveis)}")
    
    print("\n✓ Passos 2 e 3 concluídos!")
    print("\nPróximos passos:")
    print("  4. Criar interface PyQt5 básica")
    print("  5. Implementar algoritmo de distribuição de permanências")