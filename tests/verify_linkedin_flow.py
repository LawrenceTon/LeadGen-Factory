
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.harvester import HarvesterLogic

class TestLinkedInDiscovery(unittest.TestCase):
    def setUp(self):
        self.logic = HarvesterLogic()

    def test_discovery_flow(self):
        print("\nTesting LinkedIn-First Discovery Flow:")
        
        # Mock Playwright Page Object
        mock_page = MagicMock()
        mock_callback = MagicMock()

        # 1. Mock Google Search Results (Locator for "div.g a")
        mock_result = MagicMock()
        mock_result.get_attribute.return_value = "https://www.linkedin.com/company/spacex"
        
        mock_page.locator.return_value.all.return_value = [mock_result]
        
        # 2. Mock LinkedIn Page Content (Extraction of Website)
        # We simulate finding an 'a' tag with "Website" text or similar
        mock_link = MagicMock()
        mock_link.get_attribute.return_value = "https://www.spacex.com/"
        mock_link.inner_text.return_value = "Visit website"
        
        # When looking for 'a' tags on the LinkedIn page
        mock_page.locator.return_value.all.side_effect = [
            [mock_result], # For Google Search
            [mock_link]    # For LinkedIn Page
        ]

        # Run Discovery
        discovered = self.logic._discover_companies_via_linkedin("SpaceX", mock_page, mock_callback)
        
        print(f"  Discovered URLs: {discovered}")
        self.assertIn("https://www.spacex.com/", discovered)
        self.assertEqual(len(discovered), 1)
        print("  ✅ LinkedIn extraction logic verified (Mocked).")

if __name__ == '__main__':
    unittest.main()
