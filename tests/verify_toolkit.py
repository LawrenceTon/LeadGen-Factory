
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.harvester import HarvesterLogic, LeadData

class TestDeveloperToolkit(unittest.TestCase):
    def setUp(self):
        self.logic = HarvesterLogic()

    @patch('dns.resolver.resolve')
    def test_dns_gatekeeper(self, mock_resolve):
        print("\n1. Testing DNS Gatekeeper:")
        # Case A: Live Site (A record found)
        mock_resolve.return_value = ['1.2.3.4']
        res = self.logic._resolve_domain_dns("http://google.com")
        print(f"  Live Site (A Record) -> {res} (Expected True)")
        self.assertTrue(res)

        # Case B: Dead Site (Exception)
        mock_resolve.side_effect = Exception("NXDOMAIN")
        res = self.logic._resolve_domain_dns("http://nxdomain-test.com")
        print(f"  Dead Site (NXDOMAIN) -> {res} (Expected False)")
        self.assertFalse(res)

    @patch('whois.whois')
    def test_whois_age(self, mock_whois):
        print("\n2. Testing Domain Age (Whois):")
        # Case A: Startup (< 3 years)
        mock_resp = MagicMock()
        mock_resp.creation_date = datetime.now() - timedelta(days=365*1) # 1 year old
        mock_whois.return_value = mock_resp
        
        age = self.logic._get_domain_age_years("http://startup.io")
        print(f"  Startup (1 year old) -> Age: {age:.1f}")
        self.assertLess(age, 3)

        # Case B: Corporate (> 10 years)
        mock_resp.creation_date = datetime.now() - timedelta(days=365*15) # 15 years old
        mock_whois.return_value = mock_resp
        
        age = self.logic._get_domain_age_years("http://corp.com")
        print(f"  Corporate (15 years old) -> Age: {age:.1f}")
        self.assertGreater(age, 10)

    def test_pydantic_validation(self):
        print("\n3. Testing Pydantic Validation:")
        # Case A: Valid Data
        valid_data = {
            "URL": "http://test.com",
            "Timestamp": "2023-01-01",
            "Match Type": "Corporate Brand",
            "Viability Score": 85,
            "Current Domain": "",
            "Target Role Strategy": "CEO",
            "Notes": "All good"
        }
        try:
            model = LeadData(**valid_data)
            print("  Valid Data -> PASS")
        except Exception as e:
            print(f"  Valid Data -> FAIL: {e}")
            self.fail(f"Valid data failed validation: {e}")

        # Case B: Invalid Data (Missing required field 'Match Type')
        invalid_data = {
            "URL": "http://bad.com",
            "Timestamp": "2023-01-01",
            # Match Type Missing
            "Viability Score": 50,
            "Target Role Strategy": "CEO",
            "Notes": "Bad"
        }
        try:
            LeadData(**invalid_data)
            print("  Invalid Data -> FAIL (Should raise error)")
            self.fail("Invalid data passed validation unexpectedly")
        except Exception as e:
            print(f"  Invalid Data -> PASS (Caught error: {str(e)[:50]}...)")


if __name__ == '__main__':
    unittest.main()
