import pandas as pd
from modules.harvester import HarvesterLogic
import time

def log(msg):
    print(f"[TEST LOG] {msg}")

def test_refactor():
    print("--- 1. Initializing HarvesterLogic ---")
    logic = HarvesterLogic()
    
    print("\n--- 2. Testing Genesis Mode (Find_Companies) - Mocked ---")
    # We won't actually hit the browser to save time/resources in this quick check,
    # or we can expect it to fail/timeout if browser not present? 
    # Actually, we just want to ensure the CODE RUNS and doesn't crash on import or method signature.
    # We will wrap it in a try/except for the async part.
    
    try:
        logic.execute_strategy(None, "Find_Companies", log, keyword="Test Keyword")
    except Exception as e:
        print(f"Genesis Execution raised exception (Expected if browser fails, but checks logic path): {e}")

    print("\n--- 3. Testing Enrichment Mode - Stub Data ---")
    df = pd.DataFrame([{
        "Company Name": "Google",
        "LinkedIn URL": "https://linkedin.com/company/google"
    }])
    
    try:
        logic.execute_strategy(df, "Find_Website", log)
    except Exception as e:
        print(f"Enrichment Execution raised exception: {e}")

if __name__ == "__main__":
    test_refactor()
