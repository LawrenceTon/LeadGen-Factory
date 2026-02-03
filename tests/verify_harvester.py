
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.harvester import HarvesterLogic

def test_harvester_logic():
    logic = HarvesterLogic()
    print("--- Testing Harvester Logic ---")

    # 1. Test Employee Count Extraction
    print("\n1. Testing Employee Count Extraction:")
    texts = [
        ("We have 50-100 employees in our NY office.", 50),
        ("Over 500+ employees worldwide.", 500),
        ("A small team of 10 employees.", 10),
        ("No mention of count here.", 0)
    ]
    for text, expected in texts:
        res = logic._extract_employee_count(text)
        status = "PASS" if res == expected else f"FAIL (Got {res})"
        print(f"  Input: '{text[:30]}...' -> Expected: {expected} -> {status}")

    # 2. Test Viability Score (Corporate)
    print("\n2. Testing Viability Score (Corporate):")
    score = logic._calculate_viability('Corporate Brand Mode', target_roles_found=True, public_verification=None, employee_count=50)
    print(f"  Role Found -> Score: {score} (Expected 100) -> {'PASS' if score == 100 else 'FAIL'}")

    score = logic._calculate_viability('Corporate Brand Mode', target_roles_found=False, public_verification=None, employee_count=50)
    print(f"  No Role, Has Employees -> Score: {score} (Expected 50) -> {'PASS' if score == 50 else 'FAIL'}")
    
    # 3. Test Viability Score (Public Figure)
    print("\n3. Testing Viability Score (Public Figure):")
    score = logic._calculate_viability('Public Figure Mode', False, {'verified': True, 'followers': 500}, 0)
    print(f"  Verified -> Score: {score} (Expected 100) -> {'PASS' if score == 100 else 'FAIL'}")
    
    score = logic._calculate_viability('Public Figure Mode', False, {'verified': False, 'followers': 150000}, 0)
    print(f"  >100k Followers -> Score: {score} (Expected 80) -> {'PASS' if score == 80 else 'FAIL'}")

    # 4. Test Negative Keywords
    print("\n4. Testing Negative Keyword Shield List:")
    if 'school' in logic.NEGATIVE_KEYWORDS and 'charity' in logic.NEGATIVE_KEYWORDS:
        print("  Shield integrity: PASS")
    else:
        print("  Shield integrity: FAIL")

    # 5. Test Live Site Verification (Mocked)
    print("\n5. Testing Live Site Verification (Gatekeeper):")
    
    with patch('requests.head') as mock_head, patch('requests.get') as mock_get:
        # Case A: Live Site (200 OK)
        mock_head.return_value.status_code = 200
        res = logic._verify_live_site("http://live-site.com")
        print(f"  Live Site (200) -> Result: {res} (Expected True) -> {'PASS' if res else 'FAIL'}")
        
        # Case B: Dead Site (Example: Connection Error)
        mock_head.side_effect = Exception("Connection Refused")
        mock_get.side_effect = Exception("Connection Refused")
        res = logic._verify_live_site("http://dead-site.com")
        print(f"  Dead Site (Conn Error) -> Result: {res} (Expected False) -> {'PASS' if not res else 'FAIL'}")

        # Case C: 404 Not Found
        mock_head.side_effect = None
        mock_head.return_value.status_code = 404
        mock_get.return_value.status_code = 404
        res = logic._verify_live_site("http://404-site.com")
        print(f"  Dead Site (404) -> Result: {res} (Expected False) -> {'PASS' if not res else 'FAIL'}")

    # 6. Test Smart Domain Generation
    print("\n6. Testing Smart Domain Generation:")
    keyword = "jackfruit"
    domains = logic._generate_domains(keyword)
    print(f"  Input: '{keyword}' -> Generated {len(domains)} domains.")
    
    expected_patterns = [f"https://{keyword}.com", f"https://get{keyword}.com"]
    passed = True
    for pat in expected_patterns:
        if pat not in domains:
            print(f"  Missing expected pattern: {pat}")
            passed = False
    
    print(f"  Contains expected patterns? -> {'PASS' if passed else 'FAIL'}")
    print(f"  First 3 generated: {domains[:3]}")


if __name__ == "__main__":
    test_harvester_logic()
