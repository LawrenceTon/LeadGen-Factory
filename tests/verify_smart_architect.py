
import sys
import os
import unittest
import json
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.architect import ArchitectLogic

class TestSmartBlueprint(unittest.TestCase):
    def setUp(self):
        self.recipes_dir = "tests/test_recipes"
        if os.path.exists(self.recipes_dir):
            shutil.rmtree(self.recipes_dir)
        os.makedirs(self.recipes_dir)
        self.logic = ArchitectLogic(recipes_dir=self.recipes_dir)

    def tearDown(self):
        if os.path.exists(self.recipes_dir):
            shutil.rmtree(self.recipes_dir)

    def test_execution_tags_generation(self):
        print("\nTesting Smart Blueprint Execution Tags:")
        columns = [
            {"col_name": "Standard Col", "keywords": "foo", "logic_type": "Standard"},
            {"col_name": "Decision Maker", "keywords": "CEO", "logic_type": "Champion_Selector"},
            {"col_name": "Score", "keywords": "", "logic_type": "Viability_Score"},
            {"col_name": "DNS Info", "keywords": "", "logic_type": "Domain_Intelligence"}
        ]
        
        name = "Smart_Test_Recipe"
        success = self.logic.save_recipe(name, columns)
        self.assertTrue(success)

        # Load file
        filepath = os.path.join(self.recipes_dir, f"{name}.json")
        with open(filepath, 'r') as f:
            data = json.load(f)

        saved_cols = data['columns']
        
        # Check Standard
        col0 = saved_cols[0]
        self.assertEqual(col0['execution_tags'], ["keyword_extraction"])
        print(f"  Standard -> {col0['execution_tags']} (Pass)")

        # Check Champion_Selector
        col1 = saved_cols[1]
        self.assertEqual(col1['execution_tags'], ["extract_employee_count", "identify_role"])
        print(f"  Champion_Selector -> {col1['execution_tags']} (Pass)")

        # Check Viability_Score
        col2 = saved_cols[2]
        self.assertEqual(col2['execution_tags'], ["scoring_commercial", "keyword_match"])
        print(f"  Viability_Score -> {col2['execution_tags']} (Pass)")
        
        # Check Domain_Intelligence
        col3 = saved_cols[3]
        self.assertEqual(col3['execution_tags'], ["dns_check", "domain_age"])
        print(f"  Domain_Intelligence -> {col3['execution_tags']} (Pass)")

        print("  ✅ All execution tags mapped correctly.")

if __name__ == '__main__':
    unittest.main()
