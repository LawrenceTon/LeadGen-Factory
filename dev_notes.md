# Developer Notes

## User-Agent Switching Strategy
We implemented a "Truth Enforcer" logic in `inspector.py`. Instead of creating a new browser instance for every request, we group rules by their required User-Agent. 
- **Chrome Group:** Runs first using default context.
- **Edge Group:** Closes Chrome context, opens Edge context, visits URL again.
- **Mobile Group:** Closes Edge context, opens Mobile context, visits URL again.

This ensures that we don't have conflicting headers in the same session, but it does mean multiple visits per URL if different masks are required.

## Phoenix Protocol (Database)
- The database is `leads.db`. 
- `check_record(url)` is the first step in `perform_audit`. If true, we skip.
- `save_audit` uses `INSERT OR REPLACE` logic.
- `ai_result` column stores the full JSON map of answers, which is then parsed during CSV export.

## Stealth Core
- `playwright-stealth` is great but can be flaky on some Python versions or specific setups.
- We added a `try-except` block in `utils_browser.py` to blindly accept failure and fall back to manual JS injection (`navigator.webdriver` deletion) so the app never crashes on import.

## Bug Fixes
- Fixed persistent 404. API versioning was rejecting hardcoded strings. Logic now iterates through genai.list_models() to find a compatible endpoint dynamically.
- Fixed GH001 Error. Excluded 'dist/' and 'build/' folders from version control to prevent file size limit rejection.
- Fixed API version mismatch. Added database purge utility for user convenience.
- Fixed race condition where the bot tried to overwrite a screenshot that was still locked by the previous process. Added random UUIDs to filenames.
- Fixed the 'dtype float64' crash. Pandas was inferring numeric types for columns, causing exceptions when writing status codes or text. Cast entire DF to object.
- Refactored Inspector to handle raw domains. Fixed the 'AI Error' by ensuring the API key is passed from UI to Logic. Added user control for page timeouts.
- Solved the 'Error' loop. The bot was failing to navigate because input data lacked protocol prefixes. Also refactored the save logic to keep the user's CSV clean.
- Fixed critical bug where Inspector failed on valid CSVs because the header was 'Domain' instead of 'URL'. Implemented an alias lookup and column-zero fallback.
- Solved layout overflow issue on smaller screens. The Rules Stack was pushing controls off-view. Implemented a toggle mechanism to show/hide the stack on demand.
- Fixed UI regression. The Smart Wizard frame was taking up too much space, hiding the start buttons. Added a dedicated 'Control Panel' frame anchored above the log console.