
import sys
import os
import unittest
import json
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.harvester import HarvesterLogic

class TestChainedContext(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.logic = HarvesterLogic()
        self.test_recipe_name = "Chained_Test_Recipe.json"
        
        recipe_data = {
            "name": "Chained_Test_Recipe",
            "columns": [
                {"col_name": "Brand Identity", "keywords": "{keyword}", "logic_type": "Discovery_Engine"},
                {"col_name": "Official Website", "keywords": "", "logic_type": "Domain_Recon"},
                {"col_name": "Decision Maker", "keywords": "{keyword} CEO", "logic_type": "Champion_Selector"}
            ]
        }
        with open(os.path.join("recipes", self.test_recipe_name), 'w') as f:
            json.dump(recipe_data, f)

    def tearDown(self):
        if os.path.exists(os.path.join("recipes", self.test_recipe_name)):
            os.remove(os.path.join("recipes", self.test_recipe_name))

    @patch('modules.harvester.async_playwright')
    @patch('modules.harvester.setup_stealth', new_callable=AsyncMock)
    async def test_chained_execution(self, mock_setup_stealth, mock_playwright):

        print("\nTesting Chained Context Protocol (Async):")
        
        # Async Mocks
        mock_p = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value = mock_p
        
        mock_browser = AsyncMock()
        mock_p.chromium.launch.return_value = mock_browser
        
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        
        # Mocking utils_browser.launch_browser behavior in Harvester
        # Since Harvester calls await launch_browser(...), we can mock the actual function or allow the mocks above to flow
        # But Harvester imports launch_browser. We should probably patch `modules.harvester.launch_browser`
        
        # Let's simple-patch the logic method mocking
        self.logic._discover_companies_via_linkedin = AsyncMock(return_value=["https://google.com"])
        self.logic._resolve_domain_dns = MagicMock(return_value=True) # This stayed sync

        mock_page.inner_text.return_value = "Sundar Pichai is the Google CEO. We have 1000 employees."
        mock_page.url = "https://google.com"

        logs = []
        def callback(msg):
            logs.append(msg)
            
        # We call the ASYNC method directly to test logic, bypassing the asyncio.run wrapper 
        # because we are already in an async test loop
        try:
            await self.logic.perform_harvest_async(
                urls=[], 
                recipe_name=self.test_recipe_name, 
                log_callback=callback, 
                keyword_input="Google"
            )
        except Exception as e:
            print(f"EXCEPTION in perform_harvest_async: {e}")
            for l in logs: print(f"LOG: {l}")
            raise
        
        df = self.logic.last_dataframe
        
        if df is None or df.empty:
            print("FAILURE: DataFrame is Empty/None.")
            for l in logs: print(f"LOG: {l}")

        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        row = df.iloc[0]
        
        self.assertEqual(row["URL"], "https://google.com")
        self.assertIn("Recon found https://google.com", row["Notes"])
        
        print("  ✅ Chained Context logic verified (Async).")

if __name__ == '__main__':
    unittest.main()

