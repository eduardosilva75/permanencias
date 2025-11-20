#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QFrame, QHBoxLayout, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit,
                             QTabWidget, QComboBox, QSpinBox, QLineEdit, QFormLayout,
                             QGroupBox, QTextEdit, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QIcon

# Importar os módulos existentes
from escala_algoritmo import GeradorEscala
from escala_ler_excel import ler_excel_folgas
from escala_bd_consultas import GestorBaseDados

class EscalaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.gestor = GestorBaseDados()
        self.df_folgas = None
        self.escala_gerada = None
        
        self.setWindowTitle("Sistema de Gestão de Escalas")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Título
        title = QLabel("Sistema de Gestão de Escalas")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel("Gerir permanências e escalas de trabalho")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Frame para os botões principais (CENTRADO)
        main_buttons_frame = QFrame()
        main_buttons_layout = QHBoxLayout()
        main_buttons_layout.setSpacing(15)
        
        # Adicionar espaçador à esquerda para centralizar
        main_buttons_layout.addStretch()
        
        # Botão Gerar Escala
        btn_gerar_escala = QPushButton("📅 Gerar Escala Automática")
        btn_gerar_escala.setFont(QFont("Arial", 14))
        btn_gerar_escala.setMinimumHeight(80)
        btn_gerar_escala.setMinimumWidth(200)
        btn_gerar_escala.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        btn_gerar_escala.clicked.connect(self.abrir_gerar_escala)
        main_buttons_layout.addWidget(btn_gerar_escala)
        
        # Botão Fixar Pessoas
        btn_fixar_pessoas = QPushButton("👥 Fixar Pessoas")
        btn_fixar_pessoas.setFont(QFont("Arial", 14))
        btn_fixar_pessoas.setMinimumHeight(80)
        btn_fixar_pessoas.setMinimumWidth(200)
        btn_fixar_pessoas.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0960a8;
            }
        """)
        btn_fixar_pessoas.clicked.connect(self.abrir_fixar_pessoas)
        main_buttons_layout.addWidget(btn_fixar_pessoas)
        
        # Botão Adicionar Pessoas
        btn_adicionar_pessoas = QPushButton("➕ Adicionar Pessoas")
        btn_adicionar_pessoas.setFont(QFont("Arial", 14))
        btn_adicionar_pessoas.setMinimumHeight(80)
        btn_adicionar_pessoas.setMinimumWidth(200)
        btn_adicionar_pessoas.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #6A1B9A;
            }
        """)
        btn_adicionar_pessoas.clicked.connect(self.abrir_adicionar_pessoas)
        main_buttons_layout.addWidget(btn_adicionar_pessoas)
        
        # Adicionar espaçador à direita para centralizar
        main_buttons_layout.addStretch()
        
        main_buttons_frame.setLayout(main_buttons_layout)
        layout.addWidget(main_buttons_frame)
        
        # Área de visualização da escala
        self.escala_view_frame = QGroupBox("Escala Gerada")
        self.escala_view_layout = QVBoxLayout()
        
        self.tabela_escala = QTableWidget()
        self.tabela_escala.setColumnCount(4)
        self.tabela_escala.setHorizontalHeaderLabels(["Data", "Dia da Semana", "Manhã", "Tarde"])
        self.tabela_escala.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_escala.setMinimumHeight(400)  # Altura para ~16 linhas
        self.tabela_escala.setMaximumHeight(600)  # Altura máxima
        self.escala_view_layout.addWidget(self.tabela_escala)
        
        # Botão exportar
        btn_exportar = QPushButton("💾 Exportar para Excel")
        btn_exportar.clicked.connect(self.exportar_escala)
        btn_exportar.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        self.escala_view_layout.addWidget(btn_exportar)
        
        self.escala_view_frame.setLayout(self.escala_view_layout)
        self.escala_view_frame.setVisible(False)  # Inicialmente oculta
        layout.addWidget(self.escala_view_frame)
        
        # Espaçador
        layout.addStretch()
        
        # Botão Fechar Aplicação
        btn_fechar_layout = QHBoxLayout()
        btn_fechar = QPushButton("🚪 Fechar Aplicação")
        btn_fechar.setFont(QFont("Arial", 12))
        btn_fechar.setMinimumHeight(50)
        btn_fechar.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        btn_fechar.clicked.connect(self.fechar_aplicacao)
        btn_fechar_layout.addStretch()
        btn_fechar_layout.addWidget(btn_fechar)
        btn_fechar_layout.addStretch()
        layout.addLayout(btn_fechar_layout)
        
        # Rodapé
        footer = QLabel("© 2025 Sistema de Gestão de Escalas")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #999; font-size: 10px;")
        layout.addWidget(footer)
        
        central_widget.setLayout(layout)
        
        # Estilo geral da janela
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
    
    def abrir_gerar_escala(self):
        """Abre diálogo para gerar escala"""
        dialog = GerarEscalaDialog(self)
        if dialog.exec_():
            data_inicio, data_fim = dialog.get_datas()
            self.gerar_escala(data_inicio, data_fim)
    
    def abrir_fixar_pessoas(self):
        """Abre diálogo para fixar pessoas"""
        try:
            from fixarPessoas import FixarPessoasDialog
            dialog = FixarPessoasDialog(self.gestor, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir fixar pessoas: {e}")
    
    def abrir_adicionar_pessoas(self):
        """Abre diálogo para adicionar pessoas"""
        try:
            from adicionarPessoas import AdicionarPessoasDialog
            dialog = AdicionarPessoasDialog(self.gestor, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir adicionar pessoas: {e}")
    
    def gerar_escala(self, data_inicio, data_fim):
        """Gera a escala para o período especificado"""
        try:
            # Carregar folgas do Excel
            self.df_folgas = ler_excel_folgas('escala_folgas.xlsx')
            
            if self.df_folgas is None:
                QMessageBox.warning(self, "Aviso", "Ficheiro de folgas não encontrado!")
                return
            
            # Criar gerador de escala
            gerador = GeradorEscala(self.gestor, self.df_folgas)
            
            # Gerar escala
            self.escala_gerada = gerador.gerar_escala(data_inicio, data_fim)
            
            # Mostrar na tabela
            self.mostrar_escala_tabela()
            
            # Mostrar frame da escala
            self.escala_view_frame.setVisible(True)
            
            QMessageBox.information(self, "Sucesso", "Escala gerada com sucesso!")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar escala: {str(e)}")
    
    def mostrar_escala_tabela(self):
        """Mostra a escala gerada na tabela"""
        if not self.escala_gerada:
            return
        
        # Ordenar datas
        datas_ordenadas = sorted(self.escala_gerada.keys())
        
        self.tabela_escala.setRowCount(len(datas_ordenadas))
        
        dias_pt = {
            'Monday': 'Segunda',
            'Tuesday': 'Terça', 
            'Wednesday': 'Quarta',
            'Thursday': 'Quinta',
            'Friday': 'Sexta',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        
        for row, data_str in enumerate(datas_ordenadas):
            # Data
            data_obj = QDate.fromString(data_str, 'yyyy-MM-dd')
            item_data = QTableWidgetItem(data_obj.toString('dd/MM/yyyy'))
            self.tabela_escala.setItem(row, 0, item_data)
            
            # Dia da semana
            dia_semana = data_obj.toString('dddd')
            dia_semana_pt = dias_pt.get(dia_semana, dia_semana)
            item_dia = QTableWidgetItem(dia_semana_pt)
            self.tabela_escala.setItem(row, 1, item_dia)
            
            # Manhã
            manha = self.escala_gerada[data_str].get('Manhã', '')
            item_manha = QTableWidgetItem(manha)
            self.tabela_escala.setItem(row, 2, item_manha)
            
            # Tarde
            tarde = self.escala_gerada[data_str].get('Tarde', '')
            item_tarde = QTableWidgetItem(tarde)
            self.tabela_escala.setItem(row, 3, item_tarde)
    
    def exportar_escala(self):
        """Exporta a escala para Excel"""
        if not self.escala_gerada:
            QMessageBox.warning(self, "Aviso", "Nenhuma escala gerada para exportar!")
            return
        
        try:
            from datetime import datetime
            
            # Criar gerador temporário para usar o método de exportação
            gerador = GeradorEscala(self.gestor, self.df_folgas)
            gerador.escala = self.escala_gerada
            
            # Nome do ficheiro com data atual
            data_atual = datetime.now().strftime("%Y%m%d_%H%M")
            caminho = f"escala_gerada_{data_atual}.xlsx"
            
            gerador.exportar_para_excel(caminho)
            QMessageBox.information(self, "Sucesso", f"Escala exportada para:\n{caminho}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar: {str(e)}")
    
    def fechar_aplicacao(self):
        """Fecha a aplicação completamente"""
        reply = QMessageBox.question(self, 'Fechar Aplicação', 
                                   'Tem a certeza que deseja fechar a aplicação?',
                                   QMessageBox.Yes | QMessageBox.No, 
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.close()

class GerarEscalaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerar Escala")
        self.setGeometry(200, 200, 400, 200)
        self.resultado = False
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Formulário de datas
        form_layout = QFormLayout()
        
        self.date_inicio = QDateEdit()
        self.date_inicio.setDate(QDate.currentDate())
        self.date_inicio.setCalendarPopup(True)
        form_layout.addRow("Data Início:", self.date_inicio)
        
        self.date_fim = QDateEdit()
        self.date_fim.setDate(QDate.currentDate().addMonths(1))
        self.date_fim.setCalendarPopup(True)
        form_layout.addRow("Data Fim:", self.date_fim)
        
        layout.addLayout(form_layout)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        btn_gerar = QPushButton("Gerar Escala")
        btn_gerar.clicked.connect(self.aceitar)
        btn_gerar.setStyleSheet("background-color: #4CAF50; color: white;")
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.rejeitar)
        btn_cancelar.setStyleSheet("background-color: #f44336; color: white;")
        
        btn_layout.addWidget(btn_gerar)
        btn_layout.addWidget(btn_cancelar)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def aceitar(self):
        """Fecha o diálogo com resultado positivo"""
        self.resultado = True
        self.accept()
    
    def rejeitar(self):
        """Fecha o diálogo com resultado negativo"""
        self.resultado = False
        self.reject()
    
    def get_datas(self):
        data_inicio = self.date_inicio.date().toPyDate()
        data_fim = self.date_fim.date().toPyDate()
        return data_inicio, data_fim

def main():
    app = QApplication(sys.argv)
    # Estilo moderno
    app.setStyle('Fusion')
    window = EscalaWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()