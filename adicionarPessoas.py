#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QComboBox, QDoubleSpinBox, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class AdicionarPessoasDialog(QDialog):
    def __init__(self, gestor_bd, parent=None):
        super().__init__(parent)
        self.gestor = gestor_bd
        self.parent = parent
        
        self.setWindowTitle("Adicionar/Editar Pessoas")
        self.setGeometry(300, 200, 900, 700)
        
        self.pessoas = []
        
        self.carregar_pessoas()
        self.setup_ui()
    
    def carregar_pessoas(self):
        """Carrega pessoas da base de dados"""
        try:
            conn = self.gestor._conectar()
            cursor = conn.cursor()
            
            # Carregar pessoas com suas configurações
            cursor.execute('''
                SELECT p.id, p.nome, p.ativo, dt.turno, cp.percentagem_min, cp.percentagem_max
                FROM pessoas p
                LEFT JOIN disponibilidade_turno dt ON p.id = dt.pessoa_id
                LEFT JOIN configuracao_percentagens cp ON p.id = cp.pessoa_id
                ORDER BY p.nome
            ''')
            self.pessoas = cursor.fetchall()
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar pessoas: {e}")
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Grupo: Adicionar/Editar pessoa
        grupo_edicao = QGroupBox("Adicionar/Editar Pessoa")
        grupo_edicao.setFont(QFont("Arial", 12, QFont.Bold))
        
        form_layout = QFormLayout()
        
        # Nome
        self.edit_nome = QLineEdit()
        self.edit_nome.setPlaceholderText("Digite o nome da pessoa")
        form_layout.addRow("Nome*:", self.edit_nome)
        
        # Turno
        self.combo_turno = QComboBox()
        self.combo_turno.addItems(["Manhã", "Tarde", "Ambos"])
        self.combo_turno.setCurrentText("Ambos")
        form_layout.addRow("Turno*:", self.combo_turno)
        
        # Percentagens
        percentagens_layout = QHBoxLayout()
        
        self.spin_perc_min = QDoubleSpinBox()
        self.spin_perc_min.setRange(0.0, 100.0)
        self.spin_perc_min.setValue(10.0)
        self.spin_perc_min.setSuffix("%")
        self.spin_perc_min.setDecimals(1)
        percentagens_layout.addWidget(QLabel("Mín:"))
        percentagens_layout.addWidget(self.spin_perc_min)
        
        self.spin_perc_max = QDoubleSpinBox()
        self.spin_perc_max.setRange(0.0, 100.0)
        self.spin_perc_max.setValue(20.0)
        self.spin_perc_max.setSuffix("%")
        self.spin_perc_max.setDecimals(1)
        percentagens_layout.addWidget(QLabel("Máx:"))
        percentagens_layout.addWidget(self.spin_perc_max)
        
        percentagens_layout.addStretch()
        form_layout.addRow("Percentagens:", percentagens_layout)
        
        # Botões de ação
        btn_acao_layout = QHBoxLayout()
        
        self.btn_adicionar = QPushButton("➕ Adicionar Pessoa")
        self.btn_adicionar.clicked.connect(self.adicionar_pessoa)
        self.btn_adicionar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.btn_editar = QPushButton("✏️ Editar Selecionada")
        self.btn_editar.clicked.connect(self.editar_pessoa)
        self.btn_editar.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        
        self.btn_limpar = QPushButton("🗑️ Limpar Campos")
        self.btn_limpar.clicked.connect(self.limpar_campos)
        self.btn_limpar.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        
        btn_acao_layout.addWidget(self.btn_adicionar)
        btn_acao_layout.addWidget(self.btn_editar)
        btn_acao_layout.addWidget(self.btn_limpar)
        btn_acao_layout.addStretch()
        
        form_layout.addRow("", btn_acao_layout)
        grupo_edicao.setLayout(form_layout)
        layout.addWidget(grupo_edicao)
        
        # Grupo: Lista de pessoas
        grupo_lista = QGroupBox("Pessoas Existentes")
        grupo_lista.setFont(QFont("Arial", 12, QFont.Bold))
        
        lista_layout = QVBoxLayout()
        
        # Tabela de pessoas
        self.tabela_pessoas = QTableWidget()
        self.tabela_pessoas.setColumnCount(6)
        self.tabela_pessoas.setHorizontalHeaderLabels(["ID", "Nome", "Ativo", "Turno", "Min%", "Max%"])
        self.tabela_pessoas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_pessoas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_pessoas.itemSelectionChanged.connect(self.selecionar_pessoa)
        
        lista_layout.addWidget(self.tabela_pessoas)
        
        # Botões para a tabela
        btn_tabela_layout = QHBoxLayout()
        
        btn_desativar = QPushButton("⏸️ Desativar/Ativar")
        btn_desativar.clicked.connect(self.alternar_ativo)
        btn_desativar.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        
        btn_remover = QPushButton("❌ Remover Selecionada")
        btn_remover.clicked.connect(self.remover_pessoa)
        btn_remover.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        btn_atualizar = QPushButton("🔄 Atualizar Lista")
        btn_atualizar.clicked.connect(self.atualizar_lista)
        btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        
        btn_tabela_layout.addWidget(btn_desativar)
        btn_tabela_layout.addWidget(btn_remover)
        btn_tabela_layout.addWidget(btn_atualizar)
        btn_tabela_layout.addStretch()
        
        lista_layout.addLayout(btn_tabela_layout)
        grupo_lista.setLayout(lista_layout)
        layout.addWidget(grupo_lista)
        
        # Botões de ação
        btn_fechar_layout = QHBoxLayout()
        
        btn_fechar = QPushButton("🚪 Fechar")
        btn_fechar.clicked.connect(self.close)
        btn_fechar.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        
        btn_fechar_layout.addStretch()
        btn_fechar_layout.addWidget(btn_fechar)
        
        layout.addLayout(btn_fechar_layout)
        
        self.setLayout(layout)
        
        # Carregar dados na tabela
        self.atualizar_lista()
        self.limpar_campos()
    
    def adicionar_pessoa(self):
        """Adiciona uma nova pessoa"""
        try:
            nome = self.edit_nome.text().strip()
            turno = self.combo_turno.currentText()
            perc_min = self.spin_perc_min.value()
            perc_max = self.spin_perc_max.value()
            
            if not nome:
                QMessageBox.warning(self, "Aviso", "Digite o nome da pessoa!")
                return
            
            if perc_min > perc_max:
                QMessageBox.warning(self, "Aviso", "A percentagem mínima não pode ser maior que a máxima!")
                return
            
            conn = self.gestor._conectar()
            cursor = conn.cursor()
            
            # Verificar se pessoa já existe
            cursor.execute('SELECT id FROM pessoas WHERE nome = ?', (nome,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Aviso", f"A pessoa '{nome}' já existe!")
                conn.close()
                return
            
            # Inserir pessoa
            cursor.execute('INSERT INTO pessoas (nome, ativo) VALUES (?, 1)', (nome,))
            pessoa_id = cursor.lastrowid
            
            # Inserir turno
            cursor.execute('''
                INSERT INTO disponibilidade_turno (pessoa_id, turno)
                VALUES (?, ?)
            ''', (pessoa_id, turno))
            
            # Inserir percentagens
            cursor.execute('''
                INSERT INTO configuracao_percentagens 
                (pessoa_id, percentagem_min, percentagem_max)
                VALUES (?, ?, ?)
            ''', (pessoa_id, perc_min, perc_max))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Sucesso", 
                                  f"Pessoa '{nome}' adicionada com sucesso!\n"
                                  f"Turno: {turno}\n"
                                  f"Percentagens: {perc_min}% - {perc_max}%")
            
            # Atualizar lista e limpar campos
            self.carregar_pessoas()
            self.atualizar_lista()
            self.limpar_campos()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar pessoa: {e}")
    
    def editar_pessoa(self):
        """Edita a pessoa selecionada"""
        try:
            linha_selecionada = self.tabela_pessoas.currentRow()
            
            if linha_selecionada == -1:
                QMessageBox.warning(self, "Aviso", "Selecione uma pessoa para editar!")
                return
            
            # Obter ID da pessoa
            id_item = self.tabela_pessoas.item(linha_selecionada, 0)
            if not id_item:
                return
            
            pessoa_id = int(id_item.text())
            nome_atual = self.tabela_pessoas.item(linha_selecionada, 1).text()
            
            nome_novo = self.edit_nome.text().strip()
            turno_novo = self.combo_turno.currentText()
            perc_min_novo = self.spin_perc_min.value()
            perc_max_novo = self.spin_perc_max.value()
            
            if not nome_novo:
                QMessageBox.warning(self, "Aviso", "Digite o nome da pessoa!")
                return
            
            if perc_min_novo > perc_max_novo:
                QMessageBox.warning(self, "Aviso", "A percentagem mínima não pode ser maior que a máxima!")
                return
            
            conn = self.gestor._conectar()
            cursor = conn.cursor()
            
            # Verificar se nome já existe (para outra pessoa)
            if nome_novo != nome_atual:
                cursor.execute('SELECT id FROM pessoas WHERE nome = ? AND id != ?', (nome_novo, pessoa_id))
                if cursor.fetchone():
                    QMessageBox.warning(self, "Aviso", f"A pessoa '{nome_novo}' já existe!")
                    conn.close()
                    return
            
            # Atualizar pessoa
            cursor.execute('UPDATE pessoas SET nome = ? WHERE id = ?', (nome_novo, pessoa_id))
            
            # Atualizar turno
            cursor.execute('''
                UPDATE disponibilidade_turno SET turno = ? 
                WHERE pessoa_id = ?
            ''', (turno_novo, pessoa_id))
            
            # Atualizar percentagens
            cursor.execute('''
                UPDATE configuracao_percentagens 
                SET percentagem_min = ?, percentagem_max = ?
                WHERE pessoa_id = ?
            ''', (perc_min_novo, perc_max_novo, pessoa_id))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Sucesso", f"Pessoa '{nome_novo}' atualizada com sucesso!")
            
            # Atualizar lista
            self.carregar_pessoas()
            self.atualizar_lista()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao editar pessoa: {e}")
    
    def alternar_ativo(self):
        """Alterna o estado ativo/inativo da pessoa selecionada"""
        try:
            linha_selecionada = self.tabela_pessoas.currentRow()
            
            if linha_selecionada == -1:
                QMessageBox.warning(self, "Aviso", "Selecione uma pessoa!")
                return
            
            id_item = self.tabela_pessoas.item(linha_selecionada, 0)
            nome_item = self.tabela_pessoas.item(linha_selecionada, 1)
            ativo_item = self.tabela_pessoas.item(linha_selecionada, 2)
            
            if not all([id_item, nome_item, ativo_item]):
                return
            
            pessoa_id = int(id_item.text())
            pessoa_nome = nome_item.text()
            ativo_atual = ativo_item.text()
            ativo_novo = 0 if ativo_atual == "Sim" else 1
            
            conn = self.gestor._conectar()
            cursor = conn.cursor()
            
            cursor.execute('UPDATE pessoas SET ativo = ? WHERE id = ?', (ativo_novo, pessoa_id))
            
            conn.commit()
            conn.close()
            
            estado = "ativada" if ativo_novo else "desativada"
            QMessageBox.information(self, "Sucesso", f"Pessoa '{pessoa_nome}' {estado}!")
            
            # Atualizar lista
            self.carregar_pessoas()
            self.atualizar_lista()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao alterar estado: {e}")
    
    def remover_pessoa(self):
        """Remove a pessoa selecionada"""
        try:
            linha_selecionada = self.tabela_pessoas.currentRow()
            
            if linha_selecionada == -1:
                QMessageBox.warning(self, "Aviso", "Selecione uma pessoa para remover!")
                return
            
            id_item = self.tabela_pessoas.item(linha_selecionada, 0)
            nome_item = self.tabela_pessoas.item(linha_selecionada, 1)
            
            if not id_item or not nome_item:
                return
            
            pessoa_id = int(id_item.text())
            pessoa_nome = nome_item.text()
            
            # Confirmar remoção
            reply = QMessageBox.question(
                self, 'Confirmar Remoção',
                f"Remover permanentemente a pessoa '{pessoa_nome}'?\n\n"
                "Esta ação irá remover todas as configurações e permanências fixas associadas.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                conn = self.gestor._conectar()
                cursor = conn.cursor()
                
                # Remover em cascata (depende das constraints da BD)
                cursor.execute('DELETE FROM configuracao_percentagens WHERE pessoa_id = ?', (pessoa_id,))
                cursor.execute('DELETE FROM disponibilidade_turno WHERE pessoa_id = ?', (pessoa_id,))
                cursor.execute('DELETE FROM permanencias_fixas WHERE pessoa_id = ?', (pessoa_id,))
                cursor.execute('DELETE FROM pessoas WHERE id = ?', (pessoa_id,))
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Sucesso", f"Pessoa '{pessoa_nome}' removida!")
                
                # Atualizar lista
                self.carregar_pessoas()
                self.atualizar_lista()
                self.limpar_campos()
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao remover pessoa: {e}")
    
    def selecionar_pessoa(self):
        """Preenche os campos quando uma pessoa é selecionada na tabela"""
        try:
            linha_selecionada = self.tabela_pessoas.currentRow()
            
            if linha_selecionada == -1:
                return
            
            id_item = self.tabela_pessoas.item(linha_selecionada, 0)
            nome_item = self.tabela_pessoas.item(linha_selecionada, 1)
            turno_item = self.tabela_pessoas.item(linha_selecionada, 3)
            min_item = self.tabela_pessoas.item(linha_selecionada, 4)
            max_item = self.tabela_pessoas.item(linha_selecionada, 5)
            
            if all([id_item, nome_item, turno_item, min_item, max_item]):
                self.edit_nome.setText(nome_item.text())
                self.combo_turno.setCurrentText(turno_item.text())
                self.spin_perc_min.setValue(float(min_item.text().replace('%', '')))
                self.spin_perc_max.setValue(float(max_item.text().replace('%', '')))
                
        except Exception as e:
            print(f"Erro ao selecionar pessoa: {e}")
    
    def atualizar_lista(self):
        """Atualiza a tabela com as pessoas"""
        try:
            self.tabela_pessoas.setRowCount(len(self.pessoas))
            
            for row, (pessoa_id, nome, ativo, turno, perc_min, perc_max) in enumerate(self.pessoas):
                # ID
                item_id = QTableWidgetItem(str(pessoa_id))
                item_id.setFlags(item_id.flags() & ~Qt.ItemIsEditable)
                self.tabela_pessoas.setItem(row, 0, item_id)
                
                # Nome
                item_nome = QTableWidgetItem(nome)
                item_nome.setFlags(item_nome.flags() & ~Qt.ItemIsEditable)
                self.tabela_pessoas.setItem(row, 1, item_nome)
                
                # Ativo
                item_ativo = QTableWidgetItem("Sim" if ativo else "Não")
                item_ativo.setFlags(item_ativo.flags() & ~Qt.ItemIsEditable)
                self.tabela_pessoas.setItem(row, 2, item_ativo)
                
                # Turno
                item_turno = QTableWidgetItem(turno if turno else "Ambos")
                item_turno.setFlags(item_turno.flags() & ~Qt.ItemIsEditable)
                self.tabela_pessoas.setItem(row, 3, item_turno)
                
                # Percentagem Min
                item_min = QTableWidgetItem(f"{perc_min if perc_min else 10.0}%")
                item_min.setFlags(item_min.flags() & ~Qt.ItemIsEditable)
                self.tabela_pessoas.setItem(row, 4, item_min)
                
                # Percentagem Max
                item_max = QTableWidgetItem(f"{perc_max if perc_max else 20.0}%")
                item_max.setFlags(item_max.flags() & ~Qt.ItemIsEditable)
                self.tabela_pessoas.setItem(row, 5, item_max)
            
            # Ocultar coluna ID
            self.tabela_pessoas.setColumnHidden(0, True)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar lista: {e}")
    
    def limpar_campos(self):
        """Limpa os campos de edição"""
        self.edit_nome.clear()
        self.combo_turno.setCurrentText("Ambos")
        self.spin_perc_min.setValue(10.0)
        self.spin_perc_max.setValue(20.0)
        self.tabela_pessoas.clearSelection()

def main():
    """Função para teste independente"""
    from gestor_basedados import GestorBaseDados
    
    app = QApplication(sys.argv)
    gestor = GestorBaseDados()
    dialog = AdicionarPessoasDialog(gestor)
    dialog.exec_()

if __name__ == '__main__':
    main()