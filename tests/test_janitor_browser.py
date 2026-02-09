import sys
import os
import pandas as pd
import asyncio
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.janitor import JanitorLogic

class TestJanitorBrowser(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.logic = JanitorLogic()

    async def test_fingerprint_detection(self):
        # Mock Playwright Page
        mock_page = MagicMock()
        
        # Test 1: Dan.com Parking
        mock_page.goto = MagicMock(return_value=asyncio.Future())
        mock_page.goto.return_value.set_result(None)
        mock_page.url = "https://dan.com/buy-domain/example.com"
        mock_page.title = MagicMock(return_value=asyncio.Future())
        mock_page.title.return_value.set_result("dan.com - buy this domain")
        mock_page.locator = MagicMock()
        mock_page.locator("body").inner_text = MagicMock(return_value=asyncio.Future())
        mock_page.locator("body").inner_text.return_value.set_result("This domain is for sale on Dan.com")
        
        is_valid, reason = await self.logic.verify_domain_browser(mock_page, "example.com", print)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "SELLER_PARKED")

        # Test 2: Live Site
        mock_page.url = "https://google.com"
        mock_page.title.return_value = asyncio.Future()
        mock_page.title.return_value.set_result("Google")
        mock_page.locator("body").inner_text.return_value = asyncio.Future()
        mock_page.locator("body").inner_text.return_value.set_result("Search the world's information, including webpages, images, videos and more.")
        
        is_valid, reason = await self.logic.verify_domain_browser(mock_page, "google.com", print)
        self.assertTrue(is_valid)
        self.assertEqual(reason, "CLEAN")

if __name__ == '__main__':
    unittest.main()
