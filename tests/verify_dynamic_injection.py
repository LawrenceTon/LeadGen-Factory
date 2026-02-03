
import sys
import os
import unittest
import json
import shutil
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.harvester import HarvesterLogic

class TestDynamicInjection(unittest.TestCase):
    def setUp(self):
        self.logic = HarvesterLogic()
        self.test_recipe_dir = "recipes"
        self.test_recipe_name = "Dynamic_Test_Recipe.json"
        
        # Create a dummy recipe with placeholders
        recipe_data = {
            "name": "Dynamic_Test_Recipe",
            "columns": [
                {"col_name": "Decision Maker", "keywords": "{keyword} CEO, {keyword} Founder"}
            ]
        }
        with open(os.path.join(self.test_recipe_dir, self.test_recipe_name), 'w') as f:
            json.dump(recipe_data, f)

    def tearDown(self):
        path = os.path.join(self.test_recipe_dir, self.test_recipe_name)
        if os.path.exists(path):
            os.remove(path)

    @patch('modules.harvester.sync_playwright')
    def test_variable_substitution(self, mock_playwright):
        print("\nTesting Dynamic Variable Injection:")
        
        # Mock Playwright Setup
        mock_p = mock_playwright.return_value.__enter__.return_value
        mock_browser = mock_p.chromium.launch.return_value
        mock_page = mock_browser.new_context.return_value.new_page.return_value
        
        # Mock Discovery (so we don't actually go to LinkedIn)
        self.logic._discover_companies_via_linkedin = MagicMock(return_value=["https://spacex.com"])
        
        # Mock Page Content
        mock_page.inner_text.return_value = "Welcome to SpaceX. Elon Musk is the SpaceX CEO."
        mock_page.url = "https://spacex.com"
        self.logic._resolve_domain_dns = MagicMock(return_value=True) # Pass DNS
        
        # Capture the logic execution
        results = []
        def mock_callback(msg):
            pass # print(msg)

        # We need to hook into where row_raw is modified to see if it found the data
        # Since perform_harvest logic is inside the method, we can check self.last_dataframe after execution
        
        # RUN with keyword "SpaceX"
        self.logic.perform_harvest(
            urls=[], 
            recipe_name=self.test_recipe_name, 
            log_callback=mock_callback, 
            keyword_input="SpaceX"
        )
        
        df = self.logic.last_dataframe
        
        # We expect "Decision Maker" column to contain "Elon Musk is the SpaceX CEO" substring
        # Because the recipe was "{keyword} CEO" -> "SpaceX CEO"
        # And the text contains "SpaceX CEO".
        
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        
        row = df.iloc[0]
        extracted_text = row.get("Decision Maker")
        print(f"  Input: 'SpaceX'")
        print(f"  Template: '{{keyword}} CEO'")
        print(f"  Extracted: '{extracted_text}'")
        
        self.assertIsNotNone(extracted_text)
        self.assertIn("SpaceX CEO", extracted_text) # Verify substitution worked and matched
        print("  ✅ Injection Successful.")

if __name__ == '__main__':
    unittest.main()
