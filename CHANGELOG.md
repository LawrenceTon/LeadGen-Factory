# CHANGELOG

## [Unreleased]
- **Stealth Fix:** Implemented 'Safe Import' in utils_browser.py to prevent Python 3.14 crashes.
- **AI Core Upgrade:** Implemented 'Dynamic Model Discovery'. The bot now queries the Google API for available models instead of guessing, preventing 404 errors.
- **AI Fix:** Updated Gemini model to 'gemini-1.5-flash-001' with auto-fallback to 'gemini-pro' to resolve API 404 errors.
- **Feature:** Added 'Reset DB' button to allow users to clear scan history and force a re-scan.
- **Stability Fix:** Implemented UUID-based filenames for screenshots to prevent WinError 32 (File in Use) errors during high-speed scanning.
- **Crash Fix:** Forced DataFrame columns to 'object' type to prevent float64/string type mismatch errors.
- **Feature:** Added "Timeout Control" input for user-defined wait times.
- **Critical Fix:** Implemented URL Sanitizer (auto-add https://) to fix "Error" loops.
- **Data Integrity:** Fixed CSV Export to write results in-place (no duplicate columns).
- **Inspector Upgrade:** Added "Smart Column Detection". The bot now accepts "Domain", "Website", or the first column as valid targets, fixing the 'URL not found' error.
- **UI/UX Upgrade:** Added "Collapsible Rule Stack" feature. Users can now hide the rules list to free up screen space for execution controls.
- **UI Critical Fix:** Re-implemented the Execution Control Panel (Start/Pause/Stop) which was missing in the V4 layout.
- **Inspector Mode:** Changed "Start Audit" button to Bright Orange (#FF9800) for better visibility.
- **Inspector Module (V4):** Implemented Phoenix Protocol (SQLite DB logic) and Truth Enforcer (User-Agent Switching).
- **Stealth Core:** Created `modules/utils_browser.py` with `setup_stealth` and `nuke_popups`.
- **Harvester Module:** Added Human Mode and thread-safe logging.
- **Project Structure:** Initialized core directories and `main.py`.