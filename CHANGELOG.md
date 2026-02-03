# CHANGELOG

## [1.2.0] - 2026-02-03
### Added
- **Visual-Order Execution Protocol**: Harvester now executes recipe columns strictly from top-to-bottom (Index 0 to N).
- **Dynamic Variable Injection**: Recipes now support `{keyword}` placeholders, injected at runtime from the "Ignition Box".
- **LinkedIn-First Discovery**: New strict protocol that searches LinkedIn for verified company profiles instead of guessing domains.
- **Data Serialization Engine**: Added "Export Results" button to Harvester, saving data to `utf-8-sig` CSVs.
- **Strategies Engine**: Architect now includes presets (`Champion_Search`, `Brand_Discovery`) that auto-configure Logic Types and Templates.
- **Delete Column**: Architect now supports removing columns from the recipe.

### Changed
- **Pipeline Engine**: Refactored `harvester.py` to remove hardcoded phases. It is now a programmable pipeline engine.
- **API Migration**: Switched from deprecated `google.generativeai` to `google-genai` (v1.0+) in `inspector.py`.

### Fixed
- **Startup Crash**: Fixed `AttributeError` in `main.py` caused by missing `HarvesterView` class definition.

## [1.1.0] - 2026-02-02
### Added
- **Script-First Protocol:** Inspector now prioritizes local script execution over AI. "Lander" rules check connectivity/marketplaces first; "Price" rules use regex first. AI is only called if scripts fail.
- **Dynamic Execution Engine:** Implemented `analyze_lander_script` to detect marketplaces (Atom, Sedo, etc.) and trace redirects automatically without using API credits.
- **Safety Net (Fundamental Retreat):** If AI fails (429/Quota), the system falls back to a "Nuclear" text scan to salvage "Make Offer" or "Contact Broker" statuses instead of logging errors.
- **Context-Aware Price Extraction:** Enhanced regex logic to score prices based on proximity to "Buy Now" vs "Lease", and added support for suffix currencies ("9,000 USD").
- **Cost Savings:** Zero-cost auditing for resolved marketplaces and standard pricing pages.

## [v2.0 - The Script Command Upgrade]
- **Script-First Protocol:** Inspector now prioritizes local script execution over AI. "Lander" rules check connectivity/marketplaces first; "Price" rules use regex first. AI is only called if scripts fail.
- **Dynamic Execution Engine:** Implemented `analyze_lander_script` to detect marketplaces (Atom, Sedo, etc.) and trace redirects automatically without using API credits.
- **Safety Net (Fundamental Retreat):** If AI fails (429/Quota), the system falls back to a "Nuclear" text scan to salvage "Make Offer" or "Contact Broker" statuses instead of logging errors.
- **Context-Aware Price Extraction:** Enhanced regex logic to score prices based on proximity to "Buy Now" vs "Lease", and added support for suffix currencies ("9,000 USD").
- **Cost Savings:** Zero-cost auditing for resolved marketplaces and standard pricing pages.

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