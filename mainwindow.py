from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from tabs.map_tab import MapTab
from tabs.data_tab import DataTab
from tabs.network_tab import NetworkTab
from tabs.prediction_tab import PredictionTab
from tabs.investment_analysis_tab import InvestmentAnalysisTab
from tabs.search_tab import SearchTab
from tabs.profile_match_tab import ProfileMatchTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Startup Analysis Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Création du widget d'onglets
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Création de l'onglet ProfileMatch en premier
        self.profile_match_tab = ProfileMatchTab()
        
        # Ajout des onglets
        self.tabs.addTab(MapTab(), "Carte")
        self.tabs.addTab(DataTab(), "Données")
        self.tabs.addTab(NetworkTab(), "Réseaux")
        
        
        self.tabs.addTab(InvestmentAnalysisTab(), "Analyse d'Investissement")
        self.tabs.addTab(self.profile_match_tab, "Correspondance de Profil")
        self.tabs.addTab(PredictionTab(self.profile_match_tab), "Prédiction de Succès")
        self.tabs.addTab(SearchTab(), "Recherche")