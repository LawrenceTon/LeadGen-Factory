# CHANGELOG

## [Unreleased]
- **Stealth Fix:** Implemented 'Safe Import' in utils_browser.py to prevent Python 3.14 crashes.
- **UI Critical Fix:** Re-implemented the Execution Control Panel (Start/Pause/Stop) which was missing in the V4 layout.
- **Inspector Mode:** Changed "Start Audit" button to Bright Orange (#FF9800) for better visibility.
- **Inspector Module (V4):** Implemented Phoenix Protocol (SQLite DB logic) and Truth Enforcer (User-Agent Switching).
- **Stealth Core:** Created `modules/utils_browser.py` with `setup_stealth` and `nuke_popups`.
- **Harvester Module:** Added Human Mode and thread-safe logging.
- **Project Structure:** Initialized core directories and `main.py`.