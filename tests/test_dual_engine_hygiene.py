import sys
import os
import pandas as pd
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.janitor import JanitorLogic
from modules.harvester import HarvesterLogic

class TestHygieneAndEngine(unittest.TestCase):
    def setUp(self):
        self.janitor = JanitorLogic()
        self.harvester = HarvesterLogic()

    def test_deduplication(self):
        print("\nTesting Janitor Deduplication...")
        data = {
            "Website": ["google.com", "https://google.com/", "www.google.com", "bing.com"],
            "Email": ["test@test.com", "test@test.com", "other@test.com", None]
        }
        df = pd.DataFrame(data)
        
        # Should reduce to 2 domains (google.com, bing.com)
        # But wait, logic dedupe separately?
        # Let's check logic:
        # 1. Norm Domain -> dedupe on it
        # 2. Norm Email -> dedupe on it
        
        clean_df, removed = self.janitor.remove_duplicates(df)
        print(f"Original: {len(df)}, Clean: {len(clean_df)}, Removed: {removed}")
        
        self.assertEqual(len(clean_df), 2) # google, bing
        self.assertTrue("google.com" in clean_df["Website"].values or "https://google.com/" in clean_df["Website"].values)

    def test_dns_check(self):
        print("\nTesting Janitor DNS Check...")
        valid = self.janitor.check_dns("google.com")
        print(f"DNS google.com: {valid}")
        self.assertTrue(valid)
        
        invalid = self.janitor.check_dns("this-domain-hopefully-does-not-exist-12345.com")
        print(f"DNS invalid: {invalid}")
        self.assertFalse(invalid)

    def test_config_loading(self):
        print("\nTesting Harvester Config Loading...")
        # valid/invalid key check
        # We just want to ensure no crash
        print(f"Loaded Whoxy Key: '{self.harvester.whoxy_key}'")
        self.assertIsNotNone(self.harvester.whoxy_key)

    @patch('modules.harvester.requests.get')
    def test_whoxy_fetch_mock(self, mock_get):
        print("\nTesting Whoxy Fetch (Mocked)...")
        # Start async loop
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Simulation
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "search_result": [
                {"domain_name": "example-whoxy.com"},
                {"domain_name": "test-whoxy.com"}
            ]
        }
        mock_get.return_value = mock_response
        
        # Inject fake key so it runs
        self.harvester.whoxy_key = "test_key"
        
        results = loop.run_until_complete(self.harvester._fetch_whoxy_data("test", lambda x: print(x)))
        print(f"Whoxy Results: {len(results)}")
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["Domain"], "https://example-whoxy.com")
        self.assertEqual(results[0]["Source"], "Whoxy")
        loop.close()

if __name__ == '__main__':
    with open("test_results_manual.txt", "w") as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        unittest.main(testRunner=runner, exit=False)
