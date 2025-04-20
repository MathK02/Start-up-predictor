from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                          QSpinBox, QComboBox, QPushButton,
                          QGroupBox, QFormLayout)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import folium
from folium.plugins import MarkerCluster, HeatMap
import tempfile
import pandas as pd
from data_loader import DataLoader

class MapTab(QWidget):
  def __init__(self):
      super().__init__()
      self.layout = QVBoxLayout(self)
      self.data_loader = DataLoader()
      self.max_markers = 100  # Default max markers
      self.init_ui()
      
  def init_ui(self):
      # Create filter controls
      filter_group = QGroupBox("Filters")
      filter_layout = QFormLayout()
      
      # Number of companies filter
      self.company_count = QSpinBox()
      self.company_count.setRange(1, 10000)
      self.company_count.setValue(2000)
      self.company_count.setToolTip("Maximum number of companies to display")
      filter_layout.addRow("Max Companies:", self.company_count)
      
      # Region filter
      self.region_filter = QComboBox()
      self.region_filter.addItems([
          "All Regions",
          "SF Bay",
          "New York",
          "Los Angeles",
          "Seattle",
          "Other"
      ])
      filter_layout.addRow("Region:", self.region_filter)
      
      # Country filter
      self.country_filter = QComboBox()
      self.country_filter.addItems([
          "All Countries",
          "USA",
          "Other"
      ])
      filter_layout.addRow("Country:", self.country_filter)
      
      # Display type selector
      self.display_type = QComboBox()
      self.display_type.addItems([
          "Individual Markers",
          "Clustered Markers",
          "Heat Map"
      ])
      filter_layout.addRow("Display Type:", self.display_type)
      
      # Update button
      update_btn = QPushButton("Update Map")
      update_btn.clicked.connect(self.update_map)
      filter_layout.addRow(update_btn)
      
      filter_group.setLayout(filter_layout)
      
      # Add filters to main layout
      self.layout.addWidget(filter_group)
      
      # Create map view
      self.web_view = QWebEngineView()
      self.layout.addWidget(self.web_view)
      
      # Load initial map
      self.load_map()
      
  def filter_data(self, locations):
      """Apply filters to the location data"""
      try:
          # Get filter values
          max_companies = self.company_count.value()
          region = self.region_filter.currentText()
          country = self.country_filter.currentText()
          
          # Apply filters
          filtered = locations.copy()
          
          # Region filter
          if region != "All Regions":
              if region == "Other":
                  known_regions = ["SF Bay", "New York", "Los Angeles", "Seattle"]
                  filtered = filtered[~filtered['region'].isin(known_regions)] 
              else:
                  filtered = filtered[filtered['region'] == region]
                  
          # Country filter
          if country != "All Countries":
              if country == "Other":
                  filtered = filtered[filtered['country_code'] != "USA"]
              else:
                  filtered = filtered[filtered['country_code'] == country]
          
          # Limit number of companies
          filtered = filtered.head(max_companies)
          
          return filtered
          
      except Exception as e:
          print(f"Error in filter_data: {e}")
          # Return limited unfiltered data as fallback
          return locations.head(self.company_count.value())
      
  def load_map(self):
      # Load startup location data
      self.data_loader.load_data_map(n_rows = 10000)
      locations = self.data_loader.get_startup_locations()
      
      # Merge with objects to get company names
      if self.data_loader.objects is not None:
          locations = pd.merge(
              locations,
              self.data_loader.objects[['id', 'name']],
              left_on='object_id',
              right_on='id',
              how='left'
          )
      
      # Apply filters
      filtered_locations = self.filter_data(locations)
      
      # Create base map centered on US
      m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
      
      display_type = self.display_type.currentText()
      
      if display_type == "Clustered Markers":
          # Create marker cluster
          marker_cluster = MarkerCluster()
          
          for _, row in filtered_locations.iterrows():
              if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
                  company_name = row.get('name', 'Unknown Company')
                  #Balise HTML
                  popup_text = (
                      f"<b>Company:</b> {company_name}<br>"
                      f"City: {row.get('city', 'N/A')}<br>"
                      f"State: {row.get('state_code', 'N/A')}<br>"
                      f"Region: {row.get('region', 'N/A')}<br>"
                      f"Country: {row.get('country_code', 'N/A')}"
                  )
                  folium.Marker(
                      [row['latitude'], row['longitude']],
                      popup=popup_text
                  ).add_to(marker_cluster)
                  
          marker_cluster.add_to(m)
          
      elif display_type == "Heat Map":
          # Create heat map layer
          heat_data = [[row['latitude'], row['longitude']] for _, row in filtered_locations.iterrows() #Iterate on every row of the dataframe
                      if pd.notnull(row['latitude']) and pd.notnull(row['longitude'])]
          HeatMap(heat_data).add_to(m)
          
      else: 
          for _, row in filtered_locations.iterrows():
              if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
                  company_name = row.get('name', 'Unknown Company')
                  popup_text = (
                      f"<b>Company:</b> {company_name}<br>"
                      f"City: {row.get('city', 'N/A')}<br>"
                      f"State: {row.get('state_code', 'N/A')}<br>"
                      f"Region: {row.get('region', 'N/A')}<br>"
                      f"Country: {row.get('country_code', 'N/A')}"
                  )
                  folium.Marker(
                      [row['latitude'], row['longitude']],
                      popup=popup_text
                  ).add_to(m)
      
      # Save to temporary file and display
      temp_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
      m.save(temp_file.name)
      self.web_view.setUrl(QUrl.fromLocalFile(temp_file.name))
      
  def update_map(self):
      """Reload the map with current filter settings"""
      self.load_map()