import unittest
import sys
import os

# Ajout du chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from data_loader import DataLoader  

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.data_loader = DataLoader()
    
    def test_load_data(self):
        try:
            self.data_loader.load_data()
            # Test if data is loaded
            self.assertIsNotNone(self.data_loader.people)
            self.assertIsNotNone(self.data_loader.relationships)
            self.assertIsNotNone(self.data_loader.degrees)
            self.assertIsNotNone(self.data_loader.investments)
            self.assertIsNotNone(self.data_loader.offices)
            self.assertIsNotNone(self.data_loader.funding_rounds)
            self.assertIsNotNone(self.data_loader.objects)
            self.assertIsNotNone(self.data_loader.funds)
            

        except Exception as e:
            self.fail(f"load_data() raised {type(e).__name__} unexpectedly!")
    
    def test_data_types(self):
        try:
            self.data_loader.load_data()
            # Test if loaded data is DataFrame
            self.assertIsNotNone(self.data_loader.people, pd.DataFrame)
            self.assertIsNotNone(self.data_loader.relationships, pd.DataFrame)
            self.assertIsNotNone(self.data_loader.degrees, pd.DataFrame)
            self.assertIsNotNone(self.data_loader.investments, pd.DataFrame)
            self.assertIsNotNone(self.data_loader.offices, pd.DataFrame)
            self.assertIsNotNone(self.data_loader.funding_rounds, pd.DataFrame)
            self.assertIsNotNone(self.data_loader.objects, pd.DataFrame)
            self.assertIsNotNone(self.data_loader.funds, pd.DataFrame)
            
        except Exception as e:
            self.fail(f"Data type check raised {type(e).__name__} unexpectedly!")

if __name__ == '__main__':
    unittest.main() 