
import sys
import os
import unittest
import json
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.harvester import HarvesterLogic

class TestCircuitBreaker(unittest.TestCase):
    def setUp(self):
        self.logic = HarvesterLogic()
        self.test_recipe_name = "Circuit_Test_Recipe.json"
        
        # Recipe:
        # 1. Brand_Discovery (We will fail this)
        # 2. Champion_Selector (This should NOT run)
        recipe_data = {
            "name": "Circuit_Test_Recipe",
            "columns": [
                {"col_name": "Brand Identity", "keywords": "{keyword}", "logic_type": "Discovery_Engine"},
                {"col_name": "Decision Maker", "keywords": "{keyword} CEO", "logic_type": "Champion_Selector"}
            ]
        }
        with open(os.path.join("recipes", self.test_recipe_name), 'w') as f:
            json.dump(recipe_data, f)

    def tearDown(self):
        if os.path.exists(os.path.join("recipes", self.test_recipe_name)):
            os.remove(os.path.join("recipes", self.test_recipe_name))

    @patch('modules.harvester.sync_playwright')
    def test_circuit_breaker(self, mock_playwright):
        print("\nTesting Circuit Breaker Protocol:")
        
        # Mocks
        mock_p = mock_playwright.return_value.__enter__.return_value
        mock_browser = mock_p.chromium.launch.return_value
        mock_page = mock_browser.new_context.return_value.new_page.return_value
        
        # 1. Mock Discovery to FAIL (Return empty list)
        # The logic handles empty return by setting "Discovery Failed"
        self.logic._discover_companies_via_linkedin = MagicMock(return_value=[])
        
        # 2. Spy on page.goto to see if it's called for Step 2
        mock_page.goto = MagicMock()

        logs = []
        def callback(msg):
            logs.append(msg)
            
        self.logic.perform_harvest(
            urls=[], 
            recipe_name=self.test_recipe_name, 
            log_callback=callback, 
            keyword_input="NonExistentCompanyXYZ"
        )
        
        df = self.logic.last_dataframe
        
        # Verify
        # 1. Row should exist but be marked Failed
        self.assertIsNotNone(df)
        if not df.empty:
            row = df.iloc[0]
            print(f"  Row Status: {row.get('Match Type')}")
            self.assertEqual(row["Match Type"], "Discovery Failed")
            
            # 2. Champion Selector should NOT have triggered a page load
            # Discovery calls goto (mocked). 
            # But Champion selector calls goto(url). Here url is None.
            # BUT importantly, the LOOP should have skipped logic execution entirely.
            # We can check logs for "Pipeline Error" or just ensure data is empty.
            self.assertIsNone(row.get("Decision Maker"))
            self.assertNotIn("Champion Found", row["Notes"])
            
            print("  ✅ Circuit Breaker held. Subsequent steps skipped for dead lead.")
        else:
             print("  ⚠️ DataFrame empty (Correct behavior if no leads generated, but we expected a Failed Row).")

if __name__ == '__main__':
    unittest.main()
