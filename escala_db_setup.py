import sqlite3
import os

def criar_base_dados():
    """
    Cria a base de dados SQLite com todas as tabelas necessárias
    """
    # Conectar à base de dados (cria se não existir)
    conn = sqlite3.connect('escala_permanencias.db')
    cursor = conn.cursor()
    
    # Tabela: Pessoas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pessoas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            ativo INTEGER DEFAULT 1
        )
    ''')
    
    # Tabela: Disponibilidade por turno
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disponibilidade_turno (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pessoa_id INTEGER NOT NULL,
            turno TEXT NOT NULL CHECK(turno IN ('Manhã', 'Tarde', 'Ambos')),
            FOREIGN KEY (pessoa_id) REFERENCES pessoas(id),
            UNIQUE(pessoa_id)
        )
    ''')
    
    # Tabela: Permanências fixas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permanencias_fixas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pessoa_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            turno TEXT NOT NULL CHECK(turno IN ('Manhã', 'Tarde')),
            FOREIGN KEY (pessoa_id) REFERENCES pessoas(id),
            UNIQUE(data, turno)
        )
    ''')
    
    # Tabela: Configuração de percentagens por pessoa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracao_percentagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pessoa_id INTEGER NOT NULL,
            percentagem_min REAL DEFAULT 10.0,
            percentagem_max REAL DEFAULT 20.0,
            FOREIGN KEY (pessoa_id) REFERENCES pessoas(id),
            UNIQUE(pessoa_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✓ Base de dados criada com sucesso!")
    print("✓ Ficheiro: escala_permanencias.db")
    print("\nTabelas criadas:")
    print("  - pessoas")
    print("  - disponibilidade_turno")
    print("  - permanencias_fixas")
    print("  - configuracao_percentagens")


def adicionar_pessoa(nome, turno_disponivel='Ambos', perc_min=10.0, perc_max=20.0):
    """
    Adiciona uma pessoa à base de dados
    
    Args:
        nome: Nome da pessoa
        turno_disponivel: 'Manhã', 'Tarde' ou 'Ambos'
        perc_min: Percentagem mínima de permanências (default: 10%)
        perc_max: Percentagem máxima de permanências (default: 20%)
    """
    conn = sqlite3.connect('escala_permanencias.db')
    cursor = conn.cursor()
    
    try:
        # Inserir pessoa
        cursor.execute('INSERT INTO pessoas (nome) VALUES (?)', (nome,))
        pessoa_id = cursor.lastrowid
        
        # Inserir disponibilidade de turno
        cursor.execute('''
            INSERT INTO disponibilidade_turno (pessoa_id, turno) 
            VALUES (?, ?)
        ''', (pessoa_id, turno_disponivel))
        
        # Inserir configuração de percentagens
        cursor.execute('''
            INSERT INTO configuracao_percentagens (pessoa_id, percentagem_min, percentagem_max)
            VALUES (?, ?, ?)
        ''', (pessoa_id, perc_min, perc_max))
        
        conn.commit()
        print(f"✓ Pessoa adicionada: {nome} (Turno: {turno_disponivel})")
        
    except sqlite3.IntegrityError:
        print(f"✗ Erro: {nome} já existe na base de dados")
    
    finally:
        conn.close()


def listar_pessoas():
    """
    Lista todas as pessoas na base de dados
    """
    conn = sqlite3.connect('escala_permanencias.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.nome, dt.turno, cp.percentagem_min, cp.percentagem_max
        FROM pessoas p
        LEFT JOIN disponibilidade_turno dt ON p.id = dt.pessoa_id
        LEFT JOIN configuracao_percentagens cp ON p.id = cp.pessoa_id
        WHERE p.ativo = 1
        ORDER BY p.nome
    ''')
    
    pessoas = cursor.fetchall()
    conn.close()
    
    if pessoas:
        print("\n" + "="*70)
        print("PESSOAS NA BASE DE DADOS")
        print("="*70)
        print(f"{'Nome':<25} {'Turno':<15} {'% Min':<10} {'% Max':<10}")
        print("-"*70)
        for nome, turno, perc_min, perc_max in pessoas:
            print(f"{nome:<25} {turno:<15} {perc_min:<10.1f} {perc_max:<10.1f}")
        print("="*70)
    else:
        print("\nNenhuma pessoa registada na base de dados.")


# Exemplo de utilização
if __name__ == "__main__":
    # Criar a base de dados
    criar_base_dados()
    
    print("\n" + "="*70)
    print("EXEMPLO: Adicionar algumas pessoas")
    print("="*70)
    
    # Adicionar pessoas de exemplo
    adicionar_pessoa("Eduardo S.", "Ambos", 10, 20)
    adicionar_pessoa("Pedro C.", "Ambos", 10, 15)
    adicionar_pessoa("Filomena R.", "Ambos", 15, 20)
    adicionar_pessoa("Aurora", "Tarde", 10, 20)
    adicionar_pessoa("Patrícia S.", "Manhã", 10, 20)
    adicionar_pessoa("Sandra H.", "Manhã", 10, 20)
    adicionar_pessoa("Magda G.", "Tarde", 10, 20)
    
    # Listar todas as pessoas
    listar_pessoas()
    
    print("\n✓ Passo 1 concluído!")
    print("\nPróximos passos:")
    print("  2. Criar exemplo do ficheiro escala_folgas.xlsx")
    print("  3. Criar função para ler o Excel de folgas")
