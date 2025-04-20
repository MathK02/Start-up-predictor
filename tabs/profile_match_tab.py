import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import json
from PyQt5.QtCore import pyqtSignal


from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QComboBox, QTextEdit, QSlider, QHBoxLayout,QDialog, QListWidget, QListWidgetItem,QSpinBox)
from PyQt5.QtCore import Qt
import pandas as pd
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import numpy as np
import os
from data_loader import DataLoader

class ProfileMatchTab(QWidget):
    # Add signal at the class level
    profiles_updated = pyqtSignal()  # Add this at the top of the class
    
    def __init__(self):
        super().__init__()
        # Initialize data loader
        self.data_loader = DataLoader()
        self.data_loader.load_data()
        
        # Define degree mapping at initialization
        self.degree_type_mapping = {
            'BS': 1, 'BA': 1, 'BCS': 1, 'BFA': 1,  # Bachelor's
            'MS': 2, 'MA': 2, 'MBA': 2,  # Master's
            'PhD': 3,  # Doctorate
            'Foundation': 0, 'Other': 0
        }
        # Initialize attributes
        self.scaler = StandardScaler()
        self.nn_model = None
        self.processed_data = None

        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)

        # Create degrees.csv if it doesn't exist
        if not os.path.exists('data/degrees.csv'):
            # Using the data you provided
            degrees_data = """id,object_id,degree_type,subject,institution,graduated_at,created_at,updated_at
1,p:6117,MBA,,,,2008-02-19 03:17:36,2008-02-19 03:17:36
2,p:6136,BA,"English, French","Washington University, St. Louis",1990-01-01,2008-02-19 17:58:31,2008-02-25 00:23:55
3,p:6136,MS,Mass Communication,Boston University,1992-01-01,2008-02-19 17:58:31,2008-02-25 00:23:55
4,p:6005,MS,Internet Technology,University of Greenwich,2006-01-01,2008-02-19 23:40:40,2008-02-25 00:23:55
5,p:5832,BCS,"Computer Science, Psychology",Rice University,,2008-02-20 05:28:09,2008-02-20 05:28:09"""
            with open('data/degrees.csv', 'w') as f:
                f.write(degrees_data)

        self.init_ui()
        self.prepare_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Create form for input
        form = QFormLayout()

        # Profile name input (for saving)
        self.profile_name = QLineEdit()
        form.addRow("Profile Name:", self.profile_name)

        # Degree type input
        self.degree_input = QComboBox()
        self.degree_input.addItems(['BS', 'BA', 'MS', 'MA', 'MBA', 'PhD', 'Other'])
        form.addRow("Your Degree Type:", self.degree_input)

        # Graduation year input
        self.grad_year_input = QLineEdit()
        self.grad_year_input.setPlaceholderText("YYYY")
        form.addRow("Your Graduation Year:", self.grad_year_input)

        # Business creation year input
        self.creation_year_input = QLineEdit()
        self.creation_year_input.setPlaceholderText("YYYY")
        form.addRow("Your Business Creation Year:", self.creation_year_input)

        # Weight slider
        slider_layout = QHBoxLayout()
        self.weight_label = QLabel("Degree Level Weight: 50%")
        self.weight_slider = QSlider(Qt.Horizontal)
        self.weight_slider.setMinimum(0)
        self.weight_slider.setMaximum(100)
        self.weight_slider.setValue(50)
        self.weight_slider.setTickPosition(QSlider.TicksBelow)
        self.weight_slider.setTickInterval(10)
        self.weight_slider.valueChanged.connect(self.update_weight_label)
        slider_layout.addWidget(self.weight_label)
        slider_layout.addWidget(self.weight_slider)
        form.addRow("Feature Weights:", slider_layout)

        # Add number of similar profiles input
        self.neighbors_spin = QSpinBox()
        self.neighbors_spin.setMinimum(1)
        self.neighbors_spin.setMaximum(100)
        self.neighbors_spin.setValue(5)
        self.neighbors_spin.setToolTip("Number of similar profiles to find")
        form.addRow("Number of Similar Profiles:", self.neighbors_spin)

        # Save/Load buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Profile")
        load_btn = QPushButton("Load Profile")
        save_btn.clicked.connect(self.save_profile)
        load_btn.clicked.connect(self.show_load_dialog)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(load_btn)
        form.addRow(button_layout)

        # Match button
        self.match_btn = QPushButton("Find Similar Profiles")
        self.match_btn.clicked.connect(self.find_matches)

        # Results area
        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)

        # Add to layout
        layout.addLayout(form)
        layout.addWidget(self.match_btn)
        layout.addWidget(self.results_area)

    def save_profile(self):
        try:
            if not self.profile_name.text():
                self.results_area.setText("Please enter a profile name before saving")
                return

            profile_data = {
                'name': self.profile_name.text(),
                'degree_type': self.degree_input.currentText(),
                'graduation_year': self.grad_year_input.text(),
                'creation_year': self.creation_year_input.text(),
                'weight': self.weight_slider.value(),
                'num_neighbors': self.neighbors_spin.value(),  # Save number of neighbors
                'matched_profiles': []  # Initialize empty list for matched profiles
            }

            # Load existing profiles
            try:
                with open('profiles.json', 'r') as f:
                    profiles = json.load(f)
            except FileNotFoundError:
                profiles = {}

            # Add/Update profile
            profiles[profile_data['name']] = profile_data

            # Save profiles
            with open('profiles.json', 'w') as f:
                json.dump(profiles, f)

            self.results_area.setText(f"Profile '{profile_data['name']}' saved successfully!")
            self.profiles_updated.emit()  # Emit signal after saving
        except Exception as e:
            self.results_area.setText(f"Error saving profile: {str(e)}")

    def show_load_dialog(self):
        try:
            # Load profiles
            with open('profiles.json', 'r') as f:
                profiles = json.load(f)

            if not profiles:
                self.results_area.setText("No saved profiles found.")
                return

            # Create profile selection dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Select Profile")
            dialog_layout = QVBoxLayout()

            # Create list widget with profiles
            list_widget = QListWidget()
            for name, profile in profiles.items():
                # Create readable profile description
                exp_years = int(profile['creation_year']) - int(profile['graduation_year'])
                item_text = f"{name} - {profile['degree_type']}, {exp_years} years experience"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, name)  # Store profile name as data
                list_widget.addItem(item)

            dialog_layout.addWidget(list_widget)

            # Add load button
            load_btn = QPushButton("Load Selected Profile")
            load_btn.clicked.connect(lambda: self.load_profile(list_widget.currentItem().data(Qt.UserRole), profiles, dialog))
            dialog_layout.addWidget(load_btn)

            dialog.setLayout(dialog_layout)
            dialog.exec_()

        except FileNotFoundError:
            self.results_area.setText("No saved profiles found.")
        except Exception as e:
            self.results_area.setText(f"Error loading profiles: {str(e)}")

    def load_profile(self, profile_name, profiles, dialog):
        try:
            profile = profiles[profile_name]

            # Load profile data
            self.profile_name.setText(profile['name'])
            self.degree_input.setCurrentText(profile['degree_type'])
            self.grad_year_input.setText(profile['graduation_year'])
            self.creation_year_input.setText(profile['creation_year'])
            self.weight_slider.setValue(profile.get('weight', 50))  # Default to 50 if not found
            self.neighbors_spin.setValue(profile.get('num_neighbors', 5))  # Default to 5 if not found

            dialog.accept()
            self.results_area.setText(f"Profile '{profile_name}' loaded successfully!")
        except Exception as e:
            self.results_area.setText(f"Error loading profile: {str(e)}")
    
    def update_weight_label(self):
        weight = self.weight_slider.value()
        self.weight_label.setText(f"Degree Level Weight: {weight}%")

    def prepare_data(self):
        try:
            # Read education data
            df = pd.read_csv('data/degrees.csv')

            # Convert dates to datetime
            df['graduated_at'] = pd.to_datetime(df['graduated_at'])
            df['created_at'] = pd.to_datetime(df['created_at'])

            # Extract graduation year from graduated_at
            df['graduation_year'] = df['graduated_at'].dt.year

            # Calculate the time difference (experience before starting company)
            df['experience_years'] = (df['created_at'].dt.year - df['graduation_year'])

            # Map degree types to numerical values
            df['degree_level'] = df['degree_type'].map(self.degree_type_mapping)

            # Drop rows with missing values
            df = df.dropna(subset=['graduation_year', 'degree_level'])

            if len(df) == 0:
                self.results_area.setText("Error: No valid data after preprocessing")
                return False

            # Prepare feature matrix
            self.X = df[['degree_level', 'experience_years']].values

            # Store processed data
            self.processed_data = df

            # Initialize and fit scaler
            self.X_scaled = self.scaler.fit_transform(self.X)

            # Initialize and fit nearest neighbors model
            self.nn_model = NearestNeighbors(n_neighbors=min(5, len(df)), metric='euclidean')
            self.nn_model.fit(self.X_scaled)

            return True

        except Exception as e:
            self.results_area.setText(f"Error preparing data: {str(e)}")
            return False

    def find_matches(self):
        try:
            # Get input values
            degree_level = self.degree_type_mapping.get(self.degree_input.currentText(), 0)
            grad_year = int(self.grad_year_input.text())
            creation_year = int(self.creation_year_input.text())
            experience_years = creation_year - grad_year
            num_neighbors = self.neighbors_spin.value()

            # Get weights (0-1)
            degree_weight = self.weight_slider.value() / 100
            exp_weight = 1 - degree_weight

            # Calculate distances
            distances = []
            for _, profile in self.processed_data.iterrows():
                degree_diff = abs(degree_level - profile['degree_level']) * degree_weight
                exp_diff = abs(experience_years - profile['experience_years']) * exp_weight
                total_distance = degree_diff + exp_diff
                distances.append((total_distance, profile))

            # Sort by distance
            distances.sort(key=lambda x: x[0])

            # Prepare results text
            results_text = f"Most Similar Profiles (showing top {num_neighbors}):\n\n"
            results_text += f"Your Profile: {self.degree_input.currentText()}, "
            results_text += f"Experience before starting: {experience_years} years\n"
            results_text += f"Weights: Degree {degree_weight:.1%} - Experience {exp_weight:.1%}\n\n"

            # Store matched profiles
            matched_profiles = []

            # Show matches based on selected number of neighbors
            for i, (distance, profile) in enumerate(distances[:num_neighbors], 1):
                similarity = 1/distance if distance != 0 else float('inf')
                
                # Get person's name from people.csv using object_id
                person_name = "Unknown"
                if self.data_loader.people is not None:
                    person_data = self.data_loader.people[
                        self.data_loader.people['object_id'] == profile['object_id']
                    ]
                    if not person_data.empty:
                        first_name = person_data.iloc[0].get('first_name', '')
                        last_name = person_data.iloc[0].get('last_name', '')
                        person_name = f"{first_name} {last_name}".strip()

                results_text += f"Match #{i} (Distance: {distance:.2f}, Similarity: {similarity:.2f})\n"
                results_text += f"Name: {person_name}\n"
                results_text += f"Degree: {profile['degree_type']}\n"
                results_text += f"Experience before starting: {profile['experience_years']} years\n"
                results_text += "-" * 50 + "\n"

                # Add matched profile info to list
                matched_profiles.append({
                    'name': person_name,
                    'degree_type': profile['degree_type'],
                    'experience_years': int(profile['experience_years']),
                    'similarity': float(similarity),
                    'object_id': profile['object_id']
                })

            self.results_area.setText(results_text)

            # Save matched profiles to JSON if profile name exists
            if self.profile_name.text():
                try:
                    with open('profiles.json', 'r') as f:
                        profiles = json.load(f)
                    
                    profiles[self.profile_name.text()]['matched_profiles'] = matched_profiles
                    
                    with open('profiles.json', 'w') as f:
                        json.dump(profiles, f)
                    
                    self.profiles_updated.emit()  # Emit signal after updating matches
                except Exception as e:
                    self.results_area.setText(self.results_area.toPlainText() + 
                                         f"\n\nError saving matched profiles: {str(e)}")

        except ValueError as ve:
            self.results_area.setText("Error: Please enter valid years in YYYY format")
        except Exception as e:
            self.results_area.setText(f"Error finding matches: {str(e)}")