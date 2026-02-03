
import sys
import os
import unittest
import json
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.harvester import HarvesterLogic

class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.logic = HarvesterLogic()
        self.test_recipe_name = "Pipeline_Test_Recipe.json"
        
        # Define a sequential recipe:
        # 1. Discovery (Finds 'spacex.com')
        # 2. Gatekeeper (Checks DNS)
        # 3. Champion (Finds CEO)
        recipe_data = {
            "name": "Pipeline_Test_Recipe",
            "columns": [
                {"col_name": "Search Phase", "keywords": "{keyword}", "logic_type": "Discovery_Engine"},
                {"col_name": "Gatekeeper", "keywords": "", "logic_type": "Resolution_Gatekeeper"},
                {"col_name": "Champion", "keywords": "{keyword} CEO", "logic_type": "Champion_Selector"}
            ]
        }
        with open(os.path.join("recipes", self.test_recipe_name), 'w') as f:
            json.dump(recipe_data, f)

    def tearDown(self):
        if os.path.exists(os.path.join("recipes", self.test_recipe_name)):
            os.remove(os.path.join("recipes", self.test_recipe_name))

    @patch('modules.harvester.sync_playwright')
    def test_pipeline_execution(self, mock_playwright):
        print("\nTesting Pipeline Engine:")
        
        # Mocks
        mock_p = mock_playwright.return_value.__enter__.return_value
        mock_browser = mock_p.chromium.launch.return_value
        mock_page = mock_browser.new_context.return_value.new_page.return_value
        
        # 1. Mock Discovery
        self.logic._discover_companies_via_linkedin = MagicMock(return_value=["https://spacex.com"])
        
        # 2. Mock DNS
        self.logic._resolve_domain_dns = MagicMock(return_value=True)
        
        # 3. Mock Page Content (Champion)
        mock_page.inner_text.return_value = "Elon Musk is the SpaceX CEO."
        mock_page.url = "https://spacex.com"
        
        # LOGS
        logs = []
        def callback(msg):
            logs.append(msg)
            
        # RUN
        self.logic.perform_harvest(
            urls=[], 
            recipe_name=self.test_recipe_name, 
            log_callback=callback, 
            keyword_input="SpaceX"
        )
        
        df = self.logic.last_dataframe
        print(f"  Logs: {logs[:5]}...") # Verify steps
        
        # Verify Results
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        row = df.iloc[0]
        
        # Verify Sequential Success
        self.assertEqual(row["URL"], "https://spacex.com")
        self.assertIn("SpaceX CEO", row["Champion"]) # Column 3 populated
        # Verify Discovery worked
        self.assertEqual(row["Match Type"], "Discovered")
        
        # Verify Flow Steps in Logs
        step_logs = [l for l in logs if "Executing Step" in l]
        self.assertEqual(len(step_logs), 3) # 3 columns
        self.assertIn("Step 1: Search Phase [Discovery_Engine]", step_logs[0])
        self.assertIn("Step 2: Gatekeeper [Resolution_Gatekeeper]", step_logs[1])
        self.assertIn("Step 3: Champion [Champion_Selector]", step_logs[2])
        
        print("  ✅ Pipeline execution strict ordered confirmed.")

if __name__ == '__main__':
    unittest.main()
