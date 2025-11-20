#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QDateEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from escala_bd_consultas import GestorBaseDados

class FixarPessoasDialog(QDialog):
    def __init__(self, gestor_bd, parent=None):
        super().__init__(parent)
        self.gestor = gestor_bd
        self.parent = parent
        
        self.setWindowTitle("Fixar Pessoas em Datas Específicas")
        self.setGeometry(300, 200, 800, 600)
        
        self.pessoas = []
        self.permanencias_fixas = []
        
        self.carregar_dados()
        self.setup_ui()
    
    def carregar_dados(self):
        """Carrega pessoas e permanências fixas da base de dados"""
        try:
            conn = self.gestor._conectar()
            cursor = conn.cursor()
            
            # Carregar pessoas
            cursor.execute('SELECT id, nome FROM pessoas WHERE ativo = 1 ORDER BY nome')
            self.pessoas = cursor.fetchall()
            
            # Carregar permanências fixas
            cursor.execute('''
                SELECT pf.id, p.nome, pf.data, pf.turno 
                FROM permanencias_fixas pf
                JOIN pessoas p ON pf.pessoa_id = p.id
                ORDER BY pf.data, pf.turno
            ''')
            self.permanencias_fixas = cursor.fetchall()
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {e}")
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Grupo: Adicionar nova permanência fixa
        grupo_adicionar = QGroupBox("Adicionar Permanência Fixa")
        grupo_adicionar.setFont(QFont("Arial", 12, QFont.Bold))
        
        form_layout = QFormLayout()
        
        # Pessoa
        self.combo_pessoa = QComboBox()
        for pessoa_id, nome in self.pessoas:
            self.combo_pessoa.addItem(nome, pessoa_id)
        form_layout.addRow("Pessoa:", self.combo_pessoa)
        
        # Data
        self.date_data = QDateEdit()
        self.date_data.setDate(QDate.currentDate())
        self.date_data.setCalendarPopup(True)
        self.date_data.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Data:", self.date_data)
        
        # Turno
        self.combo_turno = QComboBox()
        self.combo_turno.addItems(["Manhã", "Tarde"])
        form_layout.addRow("Turno:", self.combo_turno)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_adicionar = QPushButton("➕ Adicionar Permanência")
        btn_adicionar.clicked.connect(self.adicionar_permanencia)
        btn_adicionar.setStyleSheet("""
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
        
        btn_limpar = QPushButton("🗑️ Limpar Seleção")
        btn_limpar.clicked.connect(self.limpar_selecao)
        btn_limpar.setStyleSheet("""
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
        
        btn_layout.addWidget(btn_adicionar)
        btn_layout.addWidget(btn_limpar)
        btn_layout.addStretch()
        
        form_layout.addRow("", btn_layout)
        grupo_adicionar.setLayout(form_layout)
        layout.addWidget(grupo_adicionar)
        
        # Grupo: Permanências fixas existentes
        grupo_lista = QGroupBox("Permanências Fixas Existentes")
        grupo_lista.setFont(QFont("Arial", 12, QFont.Bold))
        
        lista_layout = QVBoxLayout()
        
        # Tabela de permanências fixas
        self.tabela_permanencias = QTableWidget()
        self.tabela_permanencias.setColumnCount(4)
        self.tabela_permanencias.setHorizontalHeaderLabels(["ID", "Pessoa", "Data", "Turno"])
        self.tabela_permanencias.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_permanencias.setSelectionBehavior(QTableWidget.SelectRows)
        
        lista_layout.addWidget(self.tabela_permanencias)
        
        # Botões para a tabela
        btn_tabela_layout = QHBoxLayout()
        
        btn_remover = QPushButton("❌ Remover Selecionada")
        btn_remover.clicked.connect(self.remover_permanencia)
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
        
        btn_tabela_layout.addWidget(btn_remover)
        btn_tabela_layout.addWidget(btn_atualizar)
        btn_tabela_layout.addStretch()
        
        lista_layout.addLayout(btn_tabela_layout)
        grupo_lista.setLayout(lista_layout)
        layout.addWidget(grupo_lista)
        
        # Botões de ação
        btn_acao_layout = QHBoxLayout()
        
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
        
        btn_acao_layout.addStretch()
        btn_acao_layout.addWidget(btn_fechar)
        
        layout.addLayout(btn_acao_layout)
        
        self.setLayout(layout)
        
        # Carregar dados na tabela
        self.atualizar_lista()
    
    def adicionar_permanencia(self):
        """Adiciona uma nova permanência fixa"""
        try:
            pessoa_nome = self.combo_pessoa.currentText()
            pessoa_id = self.combo_pessoa.currentData()
            data = self.date_data.date().toString('yyyy-MM-dd')
            turno = self.combo_turno.currentText()
            
            if not pessoa_id:
                QMessageBox.warning(self, "Aviso", "Selecione uma pessoa!")
                return
            
            # Verificar se já existe permanência para esta data e turno
            conn = self.gestor._conectar()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM permanencias_fixas 
                WHERE data = ? AND turno = ?
            ''', (data, turno))
            
            if cursor.fetchone():
                QMessageBox.warning(self, "Aviso", 
                                  f"Já existe uma permanência fixa para {data} - {turno}!")
                conn.close()
                return
            
            # Inserir nova permanência
            cursor.execute('''
                INSERT INTO permanencias_fixas (pessoa_id, data, turno)
                VALUES (?, ?, ?)
            ''', (pessoa_id, data, turno))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Sucesso", 
                                  f"Permanência fixa adicionada:\n{pessoa_nome} - {data} - {turno}")
            
            # Atualizar lista e limpar seleção
            self.carregar_dados()
            self.atualizar_lista()
            self.limpar_selecao()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar permanência: {e}")
    
    def remover_permanencia(self):
        """Remove a permanência fixa selecionada"""
        try:
            linha_selecionada = self.tabela_permanencias.currentRow()
            
            if linha_selecionada == -1:
                QMessageBox.warning(self, "Aviso", "Selecione uma permanência para remover!")
                return
            
            # Obter ID da permanência
            id_item = self.tabela_permanencias.item(linha_selecionada, 0)
            if not id_item:
                return
            
            permanencia_id = int(id_item.text())
            pessoa = self.tabela_permanencias.item(linha_selecionada, 1).text()
            data = self.tabela_permanencias.item(linha_selecionada, 2).text()
            turno = self.tabela_permanencias.item(linha_selecionada, 3).text()
            
            # Confirmar remoção
            reply = QMessageBox.question(
                self, 'Confirmar Remoção',
                f"Remover permanência fixa?\n{pessoa} - {data} - {turno}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                conn = self.gestor._conectar()
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM permanencias_fixas WHERE id = ?', (permanencia_id,))
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Sucesso", "Permanência fixa removida!")
                
                # Atualizar lista
                self.carregar_dados()
                self.atualizar_lista()
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao remover permanência: {e}")
    
    def atualizar_lista(self):
        """Atualiza a tabela com as permanências fixas"""
        try:
            self.tabela_permanencias.setRowCount(len(self.permanencias_fixas))
            
            for row, (permanencia_id, pessoa_nome, data, turno) in enumerate(self.permanencias_fixas):
                # ID
                item_id = QTableWidgetItem(str(permanencia_id))
                item_id.setFlags(item_id.flags() & ~Qt.ItemIsEditable)
                self.tabela_permanencias.setItem(row, 0, item_id)
                
                # Pessoa
                item_pessoa = QTableWidgetItem(pessoa_nome)
                item_pessoa.setFlags(item_pessoa.flags() & ~Qt.ItemIsEditable)
                self.tabela_permanencias.setItem(row, 1, item_pessoa)
                
                # Data (formatar para DD/MM/YYYY)
                data_obj = QDate.fromString(data, 'yyyy-MM-dd')
                item_data = QTableWidgetItem(data_obj.toString('dd/MM/yyyy'))
                item_data.setFlags(item_data.flags() & ~Qt.ItemIsEditable)
                self.tabela_permanencias.setItem(row, 2, item_data)
                
                # Turno
                item_turno = QTableWidgetItem(turno)
                item_turno.setFlags(item_turno.flags() & ~Qt.ItemIsEditable)
                self.tabela_permanencias.setItem(row, 3, item_turno)
            
            # Ocultar coluna ID
            self.tabela_permanencias.setColumnHidden(0, True)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar lista: {e}")
    
    def limpar_selecao(self):
        """Limpa os campos de seleção"""
        self.combo_pessoa.setCurrentIndex(0)
        self.date_data.setDate(QDate.currentDate())
        self.combo_turno.setCurrentIndex(0)

def main():
    """Função para teste independente"""
    from gestor_basedados import GestorBaseDados
    
    app = QApplication(sys.argv)
    gestor = GestorBaseDados()
    dialog = FixarPessoasDialog(gestor)
    dialog.exec_()

if __name__ == '__main__':
    main()