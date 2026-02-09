
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

sys.path.append(os.getcwd())

async def test():
    print("--- Starting Manual Async Verification ---")
    try:
        from modules.harvester import HarvesterLogic
        
        # MOCKING
        # We need to mock Harvester methods that use IO
        logic = HarvesterLogic()
        
        # Mock Discovery
        logic._discover_companies_via_linkedin = AsyncMock(return_value=["https://google.com"])
        
        # We need to mock things inside perform_harvest_async
        # But we can't easily patch inside a script without `patch` context managers or careful override
        # BUT we can just run it and let it fail on browser launch if we don't patch utils?
        # Actually, we rely on utils_browser.launch_browser.
        # Let's simple-mock the methods we control.
        
        # To avoid valid browser launch, we MUST mock launch_browser import?
        # Or mock `async_playwright`?
        
        # Let's used unittest.mock.patch manually
        from unittest.mock import patch
        
        p1 = patch('modules.harvester.async_playwright')
        mock_ap = p1.start()
        
        p2 = patch('modules.harvester.setup_stealth', new_callable=AsyncMock)
        mock_stealth = p2.start()
        
        # Setup Playwright Mocks
        mock_p = AsyncMock()
        mock_ap.return_value.__aenter__.return_value = mock_p
        mock_browser = AsyncMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        
        mock_page.inner_text.return_value = "Sundar Pichai is Key Person."
        mock_page.url = "https://google.com"

        recipe_name = "Manual_Test.json"
        import json
        with open(f"recipes/{recipe_name}", "w") as f:
            json.dump({
                "name": "ManTest",
                "columns": [
                    {"col_name": "Discovery", "logic_type": "Discovery_Engine", "keywords": "{keyword}"}
                ]
            }, f)

        print("--- Executing perform_harvest_async ---")
        await logic.perform_harvest_async(
            urls=[],
            recipe_name=recipe_name,
            log_callback=lambda msg: print(f"LOG: {msg}"),
            keyword_input="Google"
        )
        
        p1.stop()
        p2.stop()
        
        df = logic.last_dataframe
        if df is not None and not df.empty:
            print(f"--- SUCCESS: Generated {len(df)} rows ---")
            print(df.head())
        else:
            print("--- FAILURE: No DataFrame produced ---")

    except Exception as e:
        print(f"--- CRITICAL EXCEPTION: {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test())
