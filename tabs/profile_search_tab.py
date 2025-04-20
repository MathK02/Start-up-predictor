from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
import csv

class ProfileSearchTab(QWidget):
    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Input fields
        input_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Name")
        input_layout.addWidget(QLabel("Name:"))
        input_layout.addWidget(self.name_input)
        
        self.university_input = QLineEdit()
        self.university_input.setPlaceholderText("Enter University")
        input_layout.addWidget(QLabel("University:"))
        input_layout.addWidget(self.university_input)
        
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Enter City")
        input_layout.addWidget(QLabel("City:"))
        input_layout.addWidget(self.city_input)
        
        self.layout.addLayout(input_layout)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_profiles)
        self.layout.addWidget(self.search_button)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Name", "University", "City"])
        self.layout.addWidget(self.results_table)
    
    def search_profiles(self):
        name = self.name_input.text().strip().lower()
        university = self.university_input.text().strip().lower()
        city = self.city_input.text().strip().lower()
        
        results = []
        
        with open("people.csv", "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if (not name or name in row["name"].lower()) and \
                   (not university or university in row["university"].lower()) and \
                   (not city or city in row["city"].lower()):
                    results.append([row["name"], row["university"], row["city"]])
        
        # Display results in the table
        self.results_table.setRowCount(len(results))
        for i, result in enumerate(results):
            for j, value in enumerate(result):
                self.results_table.setItem(i, j, QTableWidgetItem(value))