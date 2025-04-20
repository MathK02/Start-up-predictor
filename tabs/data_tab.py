from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                           QTableView, QPushButton)
from PyQt5.QtCore import Qt, QAbstractTableModel
import pandas as pd
from data_loader import DataLoader

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Vertical:
                return str(self._data.index[section])
        return None

class DataTab(QWidget):
    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Contrôles
        controls_layout = QHBoxLayout()
        self.table_selector = QComboBox()
        self.table_selector.addItems([
            'Personnes', 
            'Relations', 
            'Investissements', 
            'Bureaux'
        ])
        controls_layout.addWidget(self.table_selector)
        
        export_btn = QPushButton("Exporter vers Excel")
        controls_layout.addWidget(export_btn)
        
        layout.addLayout(controls_layout)
        
        # Vue du tableau
        self.table_view = QTableView()
        layout.addWidget(self.table_view)
        
        # Connexion des signaux
        self.table_selector.currentTextChanged.connect(self.load_table)
        export_btn.clicked.connect(self.export_to_excel)
        
        # Chargement initial
        self.data_loader.load_data()
        self.load_table(self.table_selector.currentText())
        
    def load_table(self, table_name):
        if table_name == 'Personnes':
            data = self.data_loader.people
        elif table_name == 'Relations':
            data = self.data_loader.relationships
        elif table_name == 'Investissements':
            data = self.data_loader.investments
        else:  # Bureaux
            data = self.data_loader.offices
            
        model = PandasModel(data)
        self.table_view.setModel(model)
        
    def export_to_excel(self):
        table_name = self.table_selector.currentText()
        if hasattr(self.data_loader, table_name.lower()):
            data = getattr(self.data_loader, table_name.lower())
            data.to_excel(f"{table_name.lower()}_export.xlsx")
