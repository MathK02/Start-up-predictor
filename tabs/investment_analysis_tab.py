from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                          QPushButton, QLabel, QTableWidget, QTableWidgetItem)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from data_loader import DataLoader
from PyQt5.QtCore import Qt
import webbrowser
import numpy as np

class InvestmentAnalysisTab(QWidget):
  def __init__(self):
      super().__init__()
      self.data_loader = DataLoader()
      self.data_loader.load_data_analysis(n_rows=50000)
      self.init_ui()
      
  def init_ui(self):
      layout = QVBoxLayout(self)
      
      # Controls layout
      controls_layout = QHBoxLayout()
      
      # Visualization type selector
      self.viz_selector = QComboBox()
      self.viz_selector.addItems([
          "Degree Distribution Over Time",
          "University Analysis",
          "Sector Analysis",
          "Funds Analysis",
          "IPO Analysis"
      ])
      controls_layout.addWidget(QLabel("Visualization:"))
      controls_layout.addWidget(self.viz_selector)
      
      # Update button
      update_btn = QPushButton("Update")
      update_btn.clicked.connect(self.update_plot)
      controls_layout.addWidget(update_btn)
      
      controls_layout.addStretch()
      layout.addLayout(controls_layout)
      
      # Create matplotlib figure
      self.figure, self.ax = plt.subplots(figsize=(12, 7))
      self.canvas = FigureCanvas(self.figure)
      
      # Add the matplotlib toolbar
      self.toolbar = NavigationToolbar(self.canvas, self)
      
      # Add toolbar and canvas to layout
      layout.addWidget(self.toolbar)
      layout.addWidget(self.canvas)
      
      # Initial plot
      self.update_plot()
      
  def update_plot(self):
      # Hide funds table by default
      if hasattr(self, 'funds_table'):
          self.funds_table.setVisible(False)
      
      selected_viz = self.viz_selector.currentText()
      self.figure.clear()
      
      if selected_viz == "Investment Growth Rate":
          self.ax = self.figure.add_subplot(111)
          self.plot_growth_rate()
      elif selected_viz == "Startup Categories Distribution":
          self.ax = self.figure.add_subplot(111)
          self.plot_category_distribution()
      elif selected_viz == "Degree Distribution Over Time":
          self.plot_degree_distribution()
      elif selected_viz == "University Analysis":
          self.plot_university_analysis()
      elif selected_viz == "Sector Analysis":
          self.plot_sector_analysis()
      elif selected_viz == "Funds Analysis":
          self.plot_funds_analysis()
      elif selected_viz == "IPO Analysis":
          self.plot_ipo_analysis()
          
      self.canvas.draw()

  def plot_degree_distribution(self):
      if self.data_loader.degrees is not None:
          # Create two subplots
          ax1 = self.figure.add_subplot(121)
          ax2 = self.figure.add_subplot(122)
          
          # Clean and prepare the data
          df = self.data_loader.degrees.copy()
          df['graduated_at'] = pd.to_datetime(df['graduated_at'])
          df['decade'] = (df['graduated_at'].dt.year // 10) * 10
          
          # Filter out decades after 2000
          df = df[df['decade'] <= 2000]
          
          # Standardize degree types
          df['degree_type'] = df['degree_type'].fillna('Unknown')
          df['degree_type'] = df['degree_type'].str.upper()
          
          # Group common degrees
          degree_mapping = {
              'BS': 'Bachelor',
              'BA': 'Bachelor',
              'BSC': 'Bachelor',
              'BACHELOR': 'Bachelor',
              'MS': 'Master',
              'MSC': 'Master',
              'MASTER': 'Master',
              'MBA': 'MBA',
              'PHD': 'PhD',
              'DOCTORATE': 'PhD'
          }
          
          df['degree_category'] = df['degree_type'].apply(
              lambda x: next((v for k, v in degree_mapping.items() if k in str(x)), 'Other')
          )
          
          # Plot 1: Top 10 Degree Types
          degree_counts = df['degree_category'].value_counts().head(10)
          colors = sns.color_palette("husl", n_colors=len(degree_counts))
          bars = ax1.bar(range(len(degree_counts)), degree_counts.values, color=colors)
          ax1.set_title('Top 10 Degree Types')
          ax1.set_xlabel('Degree Type')
          ax1.set_ylabel('Count')
          plt.xticks(range(len(degree_counts)), degree_counts.index, rotation=45, ha='right')
          
          # Add value labels on top of bars
          for bar in bars:
              height = bar.get_height()
              ax1.text(bar.get_x() + bar.get_width()/2., height,
                      f'{int(height):,}',
                      ha='center', va='bottom')
          
          # Plot 2: Evolution of Degree Types Over Time
          decade_degree = pd.crosstab(df['decade'], df['degree_category'])
          decade_degree = decade_degree.loc[decade_degree.index.dropna()]
          
          # Plot stacked area chart
          decade_degree.plot(kind='area', stacked=True, ax=ax2, 
                           color=colors[:len(decade_degree.columns)])
          
          # Format x-axis to show decades clearly
          ax2.set_xticks(decade_degree.index)
          ax2.set_xticklabels([f'{int(year)}s' for year in decade_degree.index], rotation=45)
          
          ax2.set_title('Evolution of Degrees Over Time')
          ax2.set_xlabel('Decade')
          ax2.set_ylabel('Number of Degrees')
          ax2.legend(title='Degree Type', bbox_to_anchor=(1.05, 1), loc='upper left')
          
          plt.tight_layout()

  def plot_growth_rate(self):
      df = self.data_loader.funding_rounds
      if df is not None:
          df['funded_at'] = pd.to_datetime(df['funded_at'])
          df = df.set_index('funded_at')
          
          # Changed 'Y' to 'YE' for year-end frequency
          yearly_investments = df['raised_amount_usd'].resample('YE').sum()
          growth_rate = yearly_investments.pct_change() * 100
          
          # Plot
          self.ax.plot(growth_rate.index.year, growth_rate.values)
          self.ax.set_title('Year-over-Year Investment Growth Rate')
          self.ax.set_xlabel('Year')
          self.ax.set_ylabel('Growth Rate (%)')
          plt.xticks(rotation=45)

  def plot_university_analysis(self):
      if self.data_loader.degrees is not None:
          # Create subplot
          ax = self.figure.add_subplot(111)
          
          # Clean and prepare the data
          df = self.data_loader.degrees.copy()
          
          # Clean institution names
          df['institution'] = df['institution'].fillna('Unknown')
          
          # Standardize common university names
          def standardize_university(name):
              name = str(name).strip()
              if 'MIT' in name or 'Massachusetts Institute of Technology' in name:
                  return 'MIT'
              elif 'Stanford' in name:
                  return 'Stanford University'
              elif 'Harvard' in name:
                  return 'Harvard University'
              elif 'Berkeley' in name:
                  return 'UC Berkeley'
              elif 'UCLA' in name or 'University of California, Los Angeles' in name:
                  return 'UCLA'
              return name
          
          df['institution'] = df['institution'].apply(standardize_university)
          
          # Get top 10 universities
          top_universities = df['institution'].value_counts().head(10)
          
          # Create bar plot
          colors = sns.color_palette("husl", n_colors=len(top_universities))
          bars = ax.bar(range(len(top_universities)), top_universities.values, color=colors)
          
          # Customize the plot
          ax.set_title('Top 10 Universities by Number of Degrees', pad=20)
          ax.set_xlabel('University')
          ax.set_ylabel('Number of Degrees')
          
          # Rotate x-axis labels for better readability
          plt.xticks(range(len(top_universities)), 
                    top_universities.index, 
                    rotation=45, 
                    ha='right')
          
          # Add value labels on top of bars
          for bar in bars:
              height = bar.get_height()
              ax.text(bar.get_x() + bar.get_width()/2., height,
                     f'{int(height):,}',
                     ha='center', va='bottom')
          
          # Adjust layout to prevent label cutoff
          plt.tight_layout()

  def plot_sector_analysis(self):
      if self.data_loader.objects is not None:
          # Clear the current figure
          self.figure.clear()
          
          # Create two subplots using the class's figure
          ax1 = self.figure.add_subplot(211)  # 2 rows, 1 column, first plot
          ax2 = self.figure.add_subplot(212)  # 2 rows, 1 column, second plot
          
          # Get data
          df = self.data_loader.objects.copy()
          
          # First subplot - Original bar chart
          sector_counts = df['category_code'].value_counts().head(15)
          sector_counts = sector_counts.dropna()
          sector_counts = sector_counts[sector_counts.index != '']
          
          colors = sns.color_palette("husl", n_colors=len(sector_counts))
          bars = ax1.bar(range(len(sector_counts)), sector_counts.values, color=colors)
          
          ax1.set_title('Top 15 Business Categories', pad=20)
          ax1.set_xlabel('Category')
          ax1.set_ylabel('Number of Companies')
          
          # Set x-ticks for first subplot
          ax1.set_xticks(range(len(sector_counts)))
          ax1.set_xticklabels(sector_counts.index, rotation=45, ha='right')
          
          # Add value labels on bars
          for bar in bars:
              height = bar.get_height()
              ax1.text(bar.get_x() + bar.get_width()/2., height,
                      f'{int(height):,}',
                      ha='center', va='bottom')
              
          # Add percentage labels
          total = sector_counts.sum()
          for i, bar in enumerate(bars):
              height = bar.get_height()
              percentage = (height / total) * 100
              ax1.text(bar.get_x() + bar.get_width()/2., height/2,
                      f'{percentage:.1f}%',
                      ha='center', va='center',
                      color='white', fontweight='bold')
          
          # Second subplot - Categories over time
          # Define category groups
          category_groups = {
              'leisure': ['games_video', 'photo_video', 'social', 'hospitality', 'sports', 
                         'fashion', 'messaging', 'music'],
              'bizsupport': ['network_hosting', 'advertising', 'enterprise', 'consulting', 
                            'analytics', 'public_relations', 'security', 'legal'],
              'building': ['cleantech', 'manufacturing', 'semiconductor', 'automotive', 
                          'real_estate', 'nanotech'],
              'petcare': ['pets'],
              'travel': ['travel', 'transportation'],
              'health': ['health', 'medical', 'biotech'],
              'other': ['web', 'other', 'mobile', 'software', 'finance', 'education', 
                       'ecommerce', 'search', 'hardware', 'news', 'government', 'nonprofit', 'local']
          }
          
          # Convert founded_at to datetime
          df['founded_at'] = pd.to_datetime(df['founded_at'])
          df['founding_year'] = df['founded_at'].dt.year
          
          # Create category_group column
          def get_category_group(category):
              for group, categories in category_groups.items():
                  if category in categories:
                      return group
              return 'other'
              
          df['category_group'] = df['category_code'].apply(get_category_group)
          
          # Group by year and category_group
          yearly_categories = df.groupby(['founding_year', 'category_group']).size().unstack(fill_value=0)
          
          # Filter data from 1960 onwards before plotting
          yearly_categories = yearly_categories[yearly_categories.index >= 1960]
          
          # Plot lines for each category
          for category in yearly_categories.columns:
              ax2.plot(yearly_categories.index, yearly_categories[category], label=category)
          
          ax2.set_title('Category of Companies per Year')
          ax2.set_xlabel('Founding Year')
          ax2.set_ylabel('Number of Companies')
          ax2.legend(title='category_group')
          
          # Set x-axis limits from 1960 to 2010
          ax2.set_xlim(1960, 2010)
          
          # Adjust layout
          self.figure.tight_layout()

  def plot_funds_analysis(self):
      if self.data_loader.funds is not None:
          self.figure.clear()
          
          ax1 = self.figure.add_subplot(211)  
          ax2 = self.figure.add_subplot(212)  
          
          # Convert funded_at to datetime if not already
          self.data_loader.funds['funded_at'] = pd.to_datetime(self.data_loader.funds['funded_at'])
          
          # Group by year and count number of funds
          yearly_funds = self.data_loader.funds.groupby(
              self.data_loader.funds['funded_at'].dt.year
          ).size().reset_index()
          yearly_funds.columns = ['year', 'count']
          
          # Group by year and sum raised amounts
          yearly_amounts = self.data_loader.funds.groupby(
              self.data_loader.funds['funded_at'].dt.year
          )['raised_amount'].sum().reset_index()
          yearly_amounts.columns = ['year', 'amount']
          
          # Plot 1: Number of funds
          bars1 = ax1.bar(yearly_funds['year'], yearly_funds['count'], color='skyblue')
          ax1.set_title('Number of Funds Created per Year', fontsize=12)
          ax1.set_xlabel('Year', fontsize=10)
          ax1.set_ylabel('Number of Funds', fontsize=10)
          ax1.tick_params(axis='x', rotation=45)
          ax1.grid(True, linestyle='--', alpha=0.7)
          
          # Add value labels on top of each bar
          for bar in bars1:
              height = bar.get_height()
              ax1.text(bar.get_x() + bar.get_width()/2., height,
                      f'{int(height)}',
                      ha='center', va='bottom')
          
          # Plot 2: Raised amounts
          bars2 = ax2.bar(yearly_amounts['year'], yearly_amounts['amount']/1e9, color='lightgreen')
          ax2.set_title('Total Funds Raised per Year', fontsize=12)
          ax2.set_xlabel('Year', fontsize=10)
          ax2.set_ylabel('Amount Raised (Billion USD)', fontsize=10)
          ax2.tick_params(axis='x', rotation=45)
          ax2.grid(True, linestyle='--', alpha=0.7)
          
          # Add value labels on top of each bar
          for bar in bars2:
              height = bar.get_height()
              ax2.text(bar.get_x() + bar.get_width()/2., height,
                      f'${height:.1f}B',
                      ha='center', va='bottom')
          
          # Adjust layout
          self.figure.tight_layout()
    
          
          # Refresh canvas
          self.canvas.draw()

  def plot_ipo_analysis(self):
      if self.data_loader.objects is not None:
          # Clear the current figure
          self.figure.clear()
          
          # Create subplot
          ax = self.figure.add_subplot(111)
          
          # Get IPO data
          df = self.data_loader.objects.copy()
          
          # Print columns to debug
          print("Available columns:", df.columns.tolist())
          
          # Check for IPO status in 'status' column
          ipo_data = df[df['status'] == 'ipo']
          
          # Convert founded_at to datetime and extract year
          ipo_data['year'] = pd.to_datetime(ipo_data['founded_at']).dt.year
          
          # Count IPOs by year
          ipo_by_year = ipo_data.groupby('year').size().reset_index()
          ipo_by_year.columns = ['year', 'count']
          
          # Sort by year
          ipo_by_year = ipo_by_year.sort_values('year')
          
          # Create bar plot
          bars = ax.bar(ipo_by_year['year'], ipo_by_year['count'], 
                       color='skyblue', alpha=0.7)
          
          # Customize the plot
          ax.set_title('Number of IPOs per Year', pad=20)
          ax.set_xlabel('Year')
          ax.set_ylabel('Number of IPOs')
          
          # Rotate x-axis labels
          plt.xticks(rotation=45)
          
          # Add grid
          ax.grid(True, linestyle='--', alpha=0.7)
          
          # Add value labels on top of bars
          for bar in bars:
              height = bar.get_height()
              ax.text(bar.get_x() + bar.get_width()/2., height,
                     f'{int(height)}',
                     ha='center', va='bottom')
          
          # Adjust layout
          plt.tight_layout()
          
          # Refresh canvas
          self.canvas.draw()

  def open_url(self, url):
      try:
          webbrowser.open(url)
      except Exception as e:
          print(f"Error opening URL: {str(e)}")