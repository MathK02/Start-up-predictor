from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import pandas as pd
import numpy as np
from data_loader import DataLoader

class NetworkTab(QWidget):
    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()
        self.data_loader.load_data_network(n_rows=10000)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Add description label
        self.desc_label = QLabel("Network visualization showing connections between people and institutions")
        layout.addWidget(self.desc_label)
        
        # Create matplotlib figure and canvas
        self.figure = plt.figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        
        # Add the matplotlib toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Add toolbar and canvas to layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Create and display network
        self.create_network()
        
    def create_network(self):
        if self.data_loader.degrees is not None and self.data_loader.people is not None:
            # Clear the figure
            self.figure.clear()
            
            # Prepare the data
            df = self.data_loader.degrees.copy()
            
            # Join with people data to get full names and affiliations
            people_df = self.data_loader.people.copy()
            people_df['full_name'] = people_df['first_name'].fillna('') + ' ' + people_df['last_name'].fillna('')
            people_df['full_name'] = people_df['full_name'].str.strip()
            
            df = df.merge(people_df[['object_id', 'full_name', 'affiliation_name']], 
                         left_on='object_id', 
                         right_on='object_id', 
                         how='left')
            
            # Clean the data
            df = df.dropna(subset=['full_name', 'institution'])
            df['institution'] = df['institution'].fillna('Unknown Institution')
            df['affiliation_name'] = df['affiliation_name'].fillna('Unknown Company')
            
            # Standardize institution names
            def standardize_institution(name):
                name = str(name).strip()
                if pd.isna(name) or name == '':
                    return 'Unknown Institution'
                # Add common variations of university names
                if 'MIT' in name or 'Massachusetts Institute of Technology' in name:
                    return 'MIT'
                if 'Stanford' in name:
                    return 'Stanford University'
                if 'Harvard' in name:
                    return 'Harvard University'
                if 'Berkeley' in name:
                    return 'UC Berkeley'
                return name
            
            df['institution'] = df['institution'].apply(standardize_institution)
            
            # Create the graph
            G = nx.Graph()
            
            # Add edges from the dataframe
            G = nx.from_pandas_edgelist(df, source='full_name', target='institution',
                                      edge_attr=['degree_type', 'subject'])
            
            # Add company attributes
            nx.set_node_attributes(G, pd.Series(df['affiliation_name'].values, 
                                              index=df['full_name']).to_dict(), 'company')
            nx.set_node_attributes(G, pd.Series(np.nan, 
                                              index=df['institution']).to_dict(), 'company')
            
            # Get the largest connected component
            components = list(nx.connected_components(G))
            largest_component = max(components, key=len)
            subgraph = G.subgraph(largest_component)
            
            # Calculate network metrics
            try:
                n_components = len(components)
                component_sizes = [len(c) for c in components]
                
                self.desc_label.setText(
                    f"Network Statistics:\n"
                    f"Total number of nodes: {G.number_of_nodes()}\n"
                    f"Total number of edges: {G.number_of_edges()}\n"
                    f"Number of components: {n_components}\n"
                    f"Largest component size: {len(largest_component)}\n"
                    f"Average component size: {np.mean(component_sizes):.2f}"
                )
            except nx.NetworkXError as e:
                self.desc_label.setText(f"Network metrics calculation error: {str(e)}")
            
            # Create a new axes object
            ax = self.figure.add_subplot(111)
            
            # Calculate node sizes based on degree centrality
            centrality = nx.degree_centrality(subgraph)
            node_sizes = [centrality[node] * 3000 for node in subgraph.nodes()]  # Reduced multiplier
            
            # Create node colors based on type (person, institution)
            node_colors = ['lightblue' if node in df['full_name'].values 
                          else 'lightgreen' for node in subgraph.nodes()]
            
            # Draw the network with adjusted parameters
            pos = nx.spring_layout(subgraph, k=2/np.sqrt(len(subgraph.nodes())), iterations=50) #Fruchterman-Reingold
            nx.draw(subgraph, pos,
                   node_size=node_sizes,
                   node_color=node_colors,
                   with_labels=True,
                   font_size=6,
                   font_weight='bold',
                   edge_color='gray',
                   alpha=0.7,
                   ax=ax)
            
            # Add a title
            ax.set_title(f"Education Network: Largest Component of {len(largest_component)} Nodes", pad=20)
            
            # Add legend
            ax.plot([], [], 'o', color='lightblue', label='People')
            ax.plot([], [], 'o', color='lightgreen', label='Institutions')
            ax.legend()
            
            # Adjust layout and draw
            self.figure.tight_layout()
            self.canvas.draw()
