import sqlite3
from datetime import datetime, timedelta

class GestorBaseDados:
    """
    Classe para gerir todas as operações com a base de dados
    """
    
    def __init__(self, db_path='escala_permanencias.db'):
        self.db_path = db_path
    
    def _conectar(self):
        """Cria conexão à base de dados"""
        return sqlite3.connect(self.db_path)
    
    def obter_pessoas_por_turno(self, turno):
        """
        Retorna pessoas que podem fazer um determinado turno
        
        Args:
            turno: 'Manhã' ou 'Tarde'
        
        Returns:
            Lista de tuplos (id, nome)
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.nome
            FROM pessoas p
            JOIN disponibilidade_turno dt ON p.id = dt.pessoa_id
            WHERE p.ativo = 1 
            AND (dt.turno = ? OR dt.turno = 'Ambos')
            ORDER BY p.nome
        ''', (turno,))
        
        pessoas = cursor.fetchall()
        conn.close()
        
        return pessoas
    
    def obter_configuracao_pessoa(self, pessoa_id):
        """
        Retorna configuração de percentagens de uma pessoa
        
        Returns:
            Tuplo (percentagem_min, percentagem_max)
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT percentagem_min, percentagem_max
            FROM configuracao_percentagens
            WHERE pessoa_id = ?
        ''', (pessoa_id,))
        
        config = cursor.fetchone()
        conn.close()
        
        return config if config else (10.0, 20.0)
    
    def obter_permanencias_fixas(self, data_inicio, data_fim):
        """
        Retorna todas as permanências fixas num período
        
        Returns:
            Lista de tuplos (data, turno, pessoa_id, nome_pessoa)
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pf.data, pf.turno, pf.pessoa_id, p.nome
            FROM permanencias_fixas pf
            JOIN pessoas p ON pf.pessoa_id = p.id
            WHERE pf.data BETWEEN ? AND ?
            ORDER BY pf.data, pf.turno
        ''', (data_inicio.strftime('%Y-%m-%d'), data_fim.strftime('%Y-%m-%d')))
        
        fixas = cursor.fetchall()
        conn.close()
        
        return fixas
    
    def adicionar_permanencia_fixa(self, pessoa_nome, data, turno):
        """
        Adiciona uma permanência fixa
        
        Args:
            pessoa_nome: Nome da pessoa
            data: Data (datetime ou string 'YYYY-MM-DD')
            turno: 'Manhã' ou 'Tarde'
        """
        if isinstance(data, datetime):
            data = data.strftime('%Y-%m-%d')
        
        conn = self._conectar()
        cursor = conn.cursor()
        
        try:
            # Obter ID da pessoa
            cursor.execute('SELECT id FROM pessoas WHERE nome = ?', (pessoa_nome,))
            resultado = cursor.fetchone()
            
            if not resultado:
                print(f"✗ Pessoa '{pessoa_nome}' não encontrada")
                conn.close()
                return False
            
            pessoa_id = resultado[0]
            
            # Inserir permanência fixa
            cursor.execute('''
                INSERT INTO permanencias_fixas (pessoa_id, data, turno)
                VALUES (?, ?, ?)
            ''', (pessoa_id, data, turno))
            
            conn.commit()
            print(f"✓ Permanência fixa adicionada: {pessoa_nome} - {data} - {turno}")
            return True
            
        except sqlite3.IntegrityError:
            print(f"✗ Já existe uma permanência fixa para {data} - {turno}")
            return False
        
        finally:
            conn.close()
    
    def remover_permanencia_fixa(self, data, turno):
        """
        Remove uma permanência fixa
        """
        if isinstance(data, datetime):
            data = data.strftime('%Y-%m-%d')
        
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM permanencias_fixas
            WHERE data = ? AND turno = ?
        ''', (data, turno))
        
        linhas_afetadas = cursor.rowcount
        conn.commit()
        conn.close()
        
        if linhas_afetadas > 0:
            print(f"✓ Permanência fixa removida: {data} - {turno}")
            return True
        else:
            print(f"✗ Nenhuma permanência fixa encontrada para {data} - {turno}")
            return False
    
    def atualizar_disponibilidade_turno(self, pessoa_nome, novo_turno):
        """
        Atualiza disponibilidade de turno de uma pessoa
        
        Args:
            pessoa_nome: Nome da pessoa
            novo_turno: 'Manhã', 'Tarde' ou 'Ambos'
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM pessoas WHERE nome = ?', (pessoa_nome,))
        resultado = cursor.fetchone()
        
        if not resultado:
            print(f"✗ Pessoa '{pessoa_nome}' não encontrada")
            conn.close()
            return False
        
        pessoa_id = resultado[0]
        
        cursor.execute('''
            UPDATE disponibilidade_turno
            SET turno = ?
            WHERE pessoa_id = ?
        ''', (novo_turno, pessoa_id))
        
        conn.commit()
        conn.close()
        
        print(f"✓ {pessoa_nome} agora pode fazer: {novo_turno}")
        return True
    
    def atualizar_percentagens(self, pessoa_nome, perc_min, perc_max):
        """
        Atualiza percentagens de permanências de uma pessoa
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM pessoas WHERE nome = ?', (pessoa_nome,))
        resultado = cursor.fetchone()
        
        if not resultado:
            print(f"✗ Pessoa '{pessoa_nome}' não encontrada")
            conn.close()
            return False
        
        pessoa_id = resultado[0]
        
        cursor.execute('''
            UPDATE configuracao_percentagens
            SET percentagem_min = ?, percentagem_max = ?
            WHERE pessoa_id = ?
        ''', (perc_min, perc_max, pessoa_id))
        
        conn.commit()
        conn.close()
        
        print(f"✓ {pessoa_nome}: Percentagens atualizadas para {perc_min}% - {perc_max}%")
        return True
    
    def listar_configuracoes(self):
        """
        Lista todas as configurações de pessoas
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.nome, dt.turno, cp.percentagem_min, cp.percentagem_max
            FROM pessoas p
            JOIN disponibilidade_turno dt ON p.id = dt.pessoa_id
            JOIN configuracao_percentagens cp ON p.id = cp.pessoa_id
            WHERE p.ativo = 1
            ORDER BY p.nome
        ''')
        
        configs = cursor.fetchall()
        conn.close()
        
        print("\n" + "="*80)
        print("CONFIGURAÇÕES DE PESSOAS")
        print("="*80)
        print(f"{'Nome':<25} {'Disponibilidade':<20} {'% Min':<10} {'% Max':<10}")
        print("-"*80)
        
        for nome, turno, perc_min, perc_max in configs:
            print(f"{nome:<25} {turno:<20} {perc_min:<10.1f} {perc_max:<10.1f}")
        
        print("="*80)


# Exemplo de utilização
if __name__ == "__main__":
    gestor = GestorBaseDados()
    
    print("="*80)
    print("TESTE: FUNÇÕES DE CONSULTA À BASE DE DADOS")
    print("="*80)
    
    # 1. Listar quem pode fazer turno da Manhã
    print("\n1. PESSOAS QUE PODEM FAZER TURNO DA MANHÃ:")
    print("-"*80)
    pessoas_manha = gestor.obter_pessoas_por_turno('Manhã')
    for pid, nome in pessoas_manha:
        print(f"  - {nome} (ID: {pid})")
    
    # 2. Listar quem pode fazer turno da Tarde
    print("\n2. PESSOAS QUE PODEM FAZER TURNO DA TARDE:")
    print("-"*80)
    pessoas_tarde = gestor.obter_pessoas_por_turno('Tarde')
    for pid, nome in pessoas_tarde:
        print(f"  - {nome} (ID: {pid})")
    
    # 3. Adicionar permanências fixas de exemplo
    print("\n3. ADICIONAR PERMANÊNCIAS FIXAS:")
    print("-"*80)
    gestor.adicionar_permanencia_fixa("Eduardo S.", "2025-10-01", "Manhã")
    gestor.adicionar_permanencia_fixa("Pedro C.", "2025-10-01", "Tarde")
    
    # 4. Listar permanências fixas
    print("\n4. PERMANÊNCIAS FIXAS (Outubro 2025):")
    print("-"*80)
    fixas = gestor.obter_permanencias_fixas(
        datetime(2025, 10, 1), 
        datetime(2025, 10, 31)
    )
    for data, turno, pid, nome in fixas:
        print(f"  {data} - {turno}: {nome}")
    
    # 5. Atualizar configuração de uma pessoa
    print("\n5. ATUALIZAR CONFIGURAÇÃO:")
    print("-"*80)
    gestor.atualizar_disponibilidade_turno("Filomena R.", "Tarde")
    gestor.atualizar_percentagens("Filomena R.", 5.0, 15.0)
    
    # 6. Listar todas as configurações
    gestor.listar_configuracoes()
    
    print("\n✓ Passo 4 concluído!")
