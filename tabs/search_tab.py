from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                           QProgressBar, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt
import pandas as pd
import sys
import os
import traceback

# Add parent directory to path to import data_loader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import DataLoader

class SearchTab(QWidget):
    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()
        self.data_loader.load_data(n_rows=50000)
        self.init_ui()
        self.current_results = []
        
    def init_ui(self):
        # Configuration de la mise en page principale
        layout = QVBoxLayout(self)
        
        # Configuration de la zone de recherche
        search_layout = QHBoxLayout()
        
        # Sélecteur du type de recherche
        self.search_type = QComboBox()
        self.search_type.addItems(["Search Person", "Search Startup", "Search Fund"])
        self.search_type.currentTextChanged.connect(self.on_search_type_changed)
        search_layout.addWidget(self.search_type)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Entrez un nom à rechercher...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(QLabel("Nom:"))
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Rechercher")
        search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Configuration des filtres
        self.filter_layout = QHBoxLayout()
        layout.addLayout(self.filter_layout)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Table de résultats
        self.results_table = QTableWidget()
        self.setup_person_table()  # Table par défaut pour la recherche de personnes
        layout.addWidget(self.results_table)
        
    def setup_person_table(self):
        columns = ["Nom", "Prénom", "Titre", "Diplôme", "Institution", "Année d'obtention"]
        self.setup_table(columns)
    
    def setup_startup_table(self):
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Nom de la Startup", "Catégorie", "Statut", "Date de Création",
            "Étape", "Tour de Financement", "Montant Levé", "Valorisation"
        ])
    
    def setup_fund_table(self):
        columns = ["Nom du Fonds", "Date", "Montant (USD)", "Source", "Lien"]
        self.setup_table(columns)
        
        # Adjust column widths
        self.results_table.setColumnWidth(0, 200)  # Fund name
        self.results_table.setColumnWidth(1, 100)  # Date
        self.results_table.setColumnWidth(2, 150)  # Amount
        self.results_table.setColumnWidth(3, 300)  # Source description
        self.results_table.setColumnWidth(4, 80)   # Link button
    
    def setup_table(self, columns):
        # Clear existing filters
        for i in reversed(range(self.filter_layout.count())): 
            self.filter_layout.itemAt(i).widget().setParent(None)
        
        self.results_table.setColumnCount(len(columns))
        self.results_table.setHorizontalHeaderLabels(columns)
        
        # Add filter checkboxes for each column
        for i, column in enumerate(columns):
            filter_box = QCheckBox(f"Show N/A in {column}")
            filter_box.setChecked(True)
            filter_box.stateChanged.connect(lambda state, col=i: self.apply_filters())
            self.filter_layout.addWidget(filter_box)
        
        # Set column widths
        for i in range(len(columns)):
            self.results_table.setColumnWidth(i, 150)
    
    def apply_filters(self):
        if not self.current_results:
            return
            
        # Get filter states
        filters = []
        for i in range(self.filter_layout.count()):
            checkbox = self.filter_layout.itemAt(i).widget()
            filters.append(checkbox.isChecked())
        
        # Clear current table
        self.results_table.setRowCount(0)
        
        # Apply filters and display results
        row_index = 0
        for result in self.current_results:
            # Check if row should be shown based on filters
            show_row = True
            for col, (value, show_na) in enumerate(zip(result, filters)):
                if not show_na and str(value) == 'N/A':
                    show_row = False
                    break
            
            if show_row:
                self.results_table.insertRow(row_index)
                for col, value in enumerate(result):
                    if isinstance(value, tuple) and len(value) == 2:  # For URL buttons
                        url_button = QPushButton("View")
                        url_button.clicked.connect(lambda checked, url=value[1]: self.open_url(url))
                        self.results_table.setCellWidget(row_index, col, url_button)
                    else:
                        item = QTableWidgetItem(str(value))
                        self.results_table.setItem(row_index, col, item)
                row_index += 1
    
    def on_search_type_changed(self, search_type):
        if search_type == "Search Person":
            self.setup_person_table()
            self.search_input.setPlaceholderText("Entrez le nom d'une personne...")
        elif search_type == "Search Startup":
            self.setup_startup_table()
            self.search_input.setPlaceholderText("Entrez le nom d'une startup...")
        else:
            self.setup_fund_table()
            self.search_input.setPlaceholderText("Entrez le nom d'un fonds...")
        self.results_table.setRowCount(0)
    
    def perform_search(self):
        search_term = self.search_input.text().lower().strip()
        if not search_term:
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_table.setRowCount(0)
        
        if self.search_type.currentText() == "Search Person":
            self.search_person(search_term)
        elif self.search_type.currentText() == "Search Startup":
            self.search_startup(search_term)
        else:
            self.search_fund(search_term)
    
    def search_person(self, search_term):
        try:
            if self.data_loader.people is not None:
                self.progress_bar.setValue(20)
                
                # Find matching people
                people_matches = self.data_loader.people[
                    self.data_loader.people['first_name'].astype(str).str.lower().str.contains(search_term, na=False) |
                    self.data_loader.people['last_name'].astype(str).str.lower().str.contains(search_term, na=False)
                ]
                
                results = []
                self.progress_bar.setValue(40)
                
                # Process each matching person
                for _, person in people_matches.iterrows():
                    name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
                    company = person.get('affiliation_name', 'N/A')
                    object_id = person.get('object_id', '')
                    
                    # Get degree information
                    degree_info = "N/A"
                    university = "N/A"
                    if self.data_loader.degrees is not None and object_id:
                        person_degrees = self.data_loader.degrees[
                            self.data_loader.degrees['object_id'] == object_id
                        ]
                        if not person_degrees.empty:
                            degree = person_degrees.iloc[0]
                            degree_type = degree.get('degree_type', '')
                            subject = degree.get('subject', '')
                            degree_info = f"{degree_type} in {subject}".strip()
                            university = degree.get('institution', 'N/A')
                    
                    # Get title from relationships
                    title = "N/A"
                    if self.data_loader.relationships is not None and object_id:
                        person_relationships = self.data_loader.relationships[
                            self.data_loader.relationships['person_object_id'] == object_id
                        ]
                        if not person_relationships.empty:
                            # Get the first non-null title
                            titles = person_relationships['title'].dropna()
                            if not titles.empty:
                                title = titles.iloc[0]
                    
                    results.append([name, company, degree_info, university, title])
                
                self.progress_bar.setValue(80)
                
                # Display results
                self.results_table.setRowCount(len(results))
                for i, result in enumerate(results):
                    for j, value in enumerate(result):
                        item = QTableWidgetItem(str(value))
                        self.results_table.setItem(i, j, item)
                
                if len(results) == 0:
                    self.results_table.setRowCount(1)
                    self.results_table.setItem(0, 0, QTableWidgetItem("No results found"))
                
                self.progress_bar.setValue(100)
                
                # Store results for filtering
                self.current_results = results
                
                # Apply filters
                self.apply_filters()
        
        except Exception as e:
            print(f"Error during person search: {str(e)}")
            traceback.print_exc()
            self.results_table.setRowCount(1)
            self.results_table.setItem(0, 0, QTableWidgetItem(f"Error during search: {str(e)}"))
    
    def search_startup(self, search_term):
        try:
            if self.data_loader.objects is not None:
                self.progress_bar.setValue(20)
                
                # Find matching startups
                startup_matches = self.data_loader.objects[
                    self.data_loader.objects['name'].astype(str).str.lower().str.contains(search_term, na=False)
                ]
                
                results = []
                self.progress_bar.setValue(40)
                
                # Process each matching startup
                for _, startup in startup_matches.iterrows():
                    name = startup.get('name', '')
                    category = startup.get('category_code', 'N/A')
                    status = startup.get('status', 'N/A')
                    founded_date = startup.get('founded_at', 'N/A')
                    object_id = startup.get('id', '')  # This is the c: id
                    
                    # Get milestone information
                    milestone_url = "N/A"
                    if self.data_loader.milestones is not None and object_id:
                        startup_milestones = self.data_loader.milestones[
                            self.data_loader.milestones['object_id'] == object_id
                        ]
                        if not startup_milestones.empty:
                            milestone_url = startup_milestones.iloc[0].get('source_url', 'N/A')
                    
                    # Get funding information
                    funding_round = "N/A"
                    raised_amount = "N/A"
                    valuation = "N/A"
                    if self.data_loader.funding_rounds is not None and object_id:
                        startup_funding = self.data_loader.funding_rounds[
                            self.data_loader.funding_rounds['object_id'] == object_id
                        ]
                        if not startup_funding.empty:
                            latest_funding = startup_funding.iloc[-1]  # Get the latest funding round
                            funding_round = latest_funding.get('funding_round_code', 'N/A')
                            
                            # Format monetary values
                            raised_amount_val = latest_funding.get('raised_amount', 'N/A')
                            if raised_amount_val != 'N/A':
                                raised_amount = f"${raised_amount_val:,.2f}"
                                
                            valuation_val = latest_funding.get('pre_money_valuation_usd', 'N/A')
                            if valuation_val != 'N/A':
                                valuation = f"${valuation_val:,.2f}"
                    
                    results.append([name, category, status, founded_date, 
                                  ('View', milestone_url) if milestone_url != 'N/A' else 'N/A',
                                  funding_round, raised_amount, valuation])
                
                self.progress_bar.setValue(80)
                
                # Display results
                self.results_table.setRowCount(len(results))
                for i, result in enumerate(results):
                    for j, value in enumerate(result):
                        if j == 4 and isinstance(value, tuple) and len(value) == 2:  # Milestone column with URL
                            url_button = QPushButton("View")
                            url_button.clicked.connect(lambda checked, url=value[1]: self.open_url(url))
                            self.results_table.setCellWidget(i, j, url_button)
                        else:
                            item = QTableWidgetItem(str(value))
                            self.results_table.setItem(i, j, item)
                
                if len(results) == 0:
                    self.results_table.setRowCount(1)
                    self.results_table.setItem(0, 0, QTableWidgetItem("No results found"))
                
                self.progress_bar.setValue(100)
                
                # Store results for filtering
                self.current_results = results
                
                # Apply filters
                self.apply_filters()
        
        except Exception as e:
            print(f"Error during startup search: {str(e)}")
            traceback.print_exc()
            self.results_table.setRowCount(1)
            self.results_table.setItem(0, 0, QTableWidgetItem(f"Error during search: {str(e)}"))
        
        finally:
            self.progress_bar.setVisible(False)

    def search_fund(self, search_term):
        try:
            if self.data_loader.funds is not None:
                self.progress_bar.setValue(20)
                
                # Find matching funds
                funds_matches = self.data_loader.funds[
                    self.data_loader.funds['name'].astype(str).str.lower().str.contains(search_term, na=False)
                ]
                
                # Sort by date
                funds_matches = funds_matches.sort_values('funded_at', ascending=False)
                
                results = []
                self.progress_bar.setValue(40)
                
                # Process each matching fund
                for _, fund in funds_matches.iterrows():
                    # Fund name
                    name = str(fund['name'])
                    
                    # Date
                    date_str = str(fund['funded_at']).split()[0] if pd.notna(fund['funded_at']) else 'N/A'
                    
                    # Amount
                    amount_str = f"${fund['raised_amount']:,.2f}" if pd.notna(fund['raised_amount']) else 'N/A'
                    
                    # Source description
                    source = str(fund['source_description'])
                    
                    # URL (stored as tuple for special handling)
                    url = ('View', fund['source_url']) if pd.notna(fund['source_url']) else 'N/A'
                    
                    results.append([name, date_str, amount_str, source, url])
                
                self.progress_bar.setValue(80)
                
                # Store results for filtering
                self.current_results = results
                
                # Apply filters
                self.apply_filters()
                
                self.progress_bar.setValue(100)
            
        except Exception as e:
            print(f"Error during fund search: {str(e)}")
            traceback.print_exc()
            self.results_table.setRowCount(1)
            self.results_table.setItem(0, 0, QTableWidgetItem(f"Error during search: {str(e)}"))
        
        finally:
            self.progress_bar.setVisible(False)

    def open_url(self, url):
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            print(f"Error opening URL: {str(e)}")