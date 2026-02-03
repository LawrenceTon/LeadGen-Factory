
import sys
import os
import unittest
import pandas as pd
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.harvester import HarvesterLogic

class TestHarvesterExport(unittest.TestCase):
    def setUp(self):
        self.logic = HarvesterLogic()
        # Mock some data
        self.logic.last_dataframe = pd.DataFrame([
            {"URL": "example.com", "Viability Score": 80, "ExtraCol": "Value", "Notes": "Test"}
        ])
        
    def test_export_data(self):
        print("\nTesting CSV Export Engine:")
        output_path = "tests/test_export.csv"
        
        # 1. Basic Export
        success, msg = self.logic.export_data(output_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        print(f"  ✅ Basic Export: {msg}")

        # Verify encoding
        with open(output_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            self.assertTrue(len(content) > 0)
            
        # 2. Recipe Header Validation
        # recipe expects "Viability Score" and "MissingCol"
        headers = ["Viability Score", "MissingCol"] 
        success, msg = self.logic.export_data(output_path, recipe_headers=headers)
        self.assertTrue(success)
        
        df = pd.read_csv(output_path, encoding='utf-8-sig')
        self.assertIn("MissingCol", df.columns)
        self.assertEqual(df.iloc[0]["MissingCol"], "N/A") # check default fill
        print(f"  ✅ Header/Validation Export: {msg}")
        
    def tearDown(self):
        if os.path.exists("tests/test_export.csv"):
            os.remove("tests/test_export.csv")

if __name__ == '__main__':
    unittest.main()
