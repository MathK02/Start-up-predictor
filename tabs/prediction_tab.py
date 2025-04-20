import json
import pandas as pd
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QComboBox,
    QLabel, QPushButton, QTextEdit)

class PredictionTab(QWidget):
    def __init__(self, profile_match_tab):
        super().__init__()
        self.profile_match_tab = profile_match_tab
        self.profile_match_tab.profiles_updated.connect(self.reload_profiles)
        self.init_ui()
        self.load_profiles()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Profile selector
        self.profile_selector = QComboBox()
        form.addRow("Select Profile:", self.profile_selector)

        # Predict button
        self.predict_button = QPushButton("Predict Success")
        self.predict_button.clicked.connect(self.predict_success)

        # Results area
        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)

        layout.addLayout(form)
        layout.addWidget(self.predict_button)
        layout.addWidget(self.results_area)

    def reload_profiles(self):
        """Reload profiles when they're updated"""
        self.load_profiles()
        # Update the combo box selection if needed
        current_profile = self.profile_selector.currentText()
        self.profile_selector.clear()
        self.profile_selector.addItems(self.profiles.keys())
        if current_profile in self.profiles:
            self.profile_selector.setCurrentText(current_profile)

    def load_profiles(self):
        try:
            with open('profiles.json', 'r') as f:
                self.profiles = json.load(f)
            self.profile_selector.clear()
            self.profile_selector.addItems(self.profiles.keys())
        except FileNotFoundError:
            self.profiles = {}
        except Exception as e:
            self.results_area.setText(f"Error loading profiles: {str(e)}")

    def predict_success(self):
        try:
            selected_profile = self.profile_selector.currentText()
            if not selected_profile:
                self.results_area.setText("Please select a profile")
                return

            matched_profiles = self.profiles[selected_profile]['matched_profiles']
            person_ids = [profile['object_id'] for profile in matched_profiles]

            # Load necessary data
            relationships_df = pd.read_csv('data/relationships.csv')
            funding_rounds_df = pd.read_csv('data/funding_rounds.csv')
            acquisitions_df = pd.read_csv('data/acquisitions.csv')
            ipos_df = pd.read_csv('data/ipos.csv')
            degrees_df = pd.read_csv('data/degrees.csv')
            
            results_text = f"Success Prediction for {selected_profile}:\n\n"
            results_text += f"Based on {len(person_ids)} similar founder profiles\n\n"

            # Education Analysis
            education_stats = {}
            for person_id in person_ids:
                person_degrees = degrees_df[degrees_df['object_id'] == person_id]
                for _, degree in person_degrees.iterrows():
                    degree_type = degree['degree_type'] or 'Unknown'
                    subject = degree['subject'] or 'Unknown'
                    education_stats[f"{degree_type} in {subject}"] = education_stats.get(f"{degree_type} in {subject}", 0) + 1

            if education_stats:
                results_text += "Common Education Patterns:\n"
                # Sort by frequency and get top 3 most common degrees
                sorted_education = sorted(education_stats.items(), key=lambda x: x[1], reverse=True)[:3]
                for edu, _ in sorted_education:
                    results_text += f"- {edu}\n"
            results_text += "\n"

            # Track success metrics
            total_funding = 0
            total_exits = 0
            successful_exits = 0
            avg_time_to_exit = []
            funding_rounds_data = []
            
            for person_id in person_ids:
                # Find companies founded by this person
                founded_companies = relationships_df[
                    (relationships_df['person_object_id'] == person_id) & 
                    (relationships_df['title'].str.contains('Founder', case=False, na=False))
                ]['relationship_object_id'].tolist()
                
                for company_id in founded_companies:
                    # Analyze funding rounds
                    company_funding = funding_rounds_df[
                        funding_rounds_df['object_id'] == company_id
                    ].sort_values('funded_at')
                    
                    if not company_funding.empty:
                        total_funding += company_funding['raised_amount_usd'].sum()
                        funding_rounds_data.append(len(company_funding))
                    
                    # Check for successful exits
                    acquisition = acquisitions_df[acquisitions_df['acquired_object_id'] == company_id]
                    ipo = ipos_df[ipos_df['object_id'] == company_id]
                    
                    if not acquisition.empty or not ipo.empty:
                        total_exits += 1
                        if not acquisition.empty and acquisition['price_amount'].iloc[0] > 10000000:  # $10M+ exit
                            successful_exits += 1
                        elif not ipo.empty and ipo['valuation_amount'].iloc[0] > 50000000:  # $50M+ IPO
                            successful_exits += 1

            # Calculate and display statistics
            if total_exits > 0:
                success_rate = (successful_exits / total_exits) * 100
                results_text += f"Exit Success Rate: {success_rate:.1f}%\n"
                results_text += f"Total Successful Exits: {successful_exits} out of {total_exits}\n\n"

            if funding_rounds_data:
                avg_rounds = sum(funding_rounds_data) / len(funding_rounds_data)
                results_text += f"Average Funding Rounds: {avg_rounds:.1f}\n"
                results_text += f"Average Total Funding: ${total_funding/len(funding_rounds_data):,.2f}\n\n"

            # Add recommendations
            results_text += "Recommendations based on similar profiles:\n"
            if education_stats:
                most_common_edu = max(education_stats.items(), key=lambda x: x[1])[0]
                results_text += f"- Consider {most_common_edu} as it's common among successful founders\n"
            
            if funding_rounds_data:
                results_text += f"- Plan for approximately {round(avg_rounds)} funding rounds\n"
                if successful_exits > 0:
                    results_text += "- Focus on building significant value for potential exit opportunities\n"

            self.results_area.setText(results_text)
                
        except Exception as e:
            self.results_area.setText(f"Error during prediction: {str(e)}")
