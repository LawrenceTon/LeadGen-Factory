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
- Solved layout overflow issue on smaller screens. The Rules Stack was pushing controls off-view. Implemented a toggle mechanism to show/hide the stack on demand.
- Fixed UI regression. The Smart Wizard frame was taking up too much space, hiding the start buttons. Added a dedicated 'Control Panel' frame anchored above the log console.