# LeadGen Factory - Changelog

All notable changes to the "LeadGen Factory" project will be documented in this file.

## [Unreleased]
- **High Accuracy Protocol:** Planning a verification layer to double-check AI results and detect "soft blocks" (captchas).

## [V4.0] - "The Phoenix Update" - 2026-02-02
### Added
- **Phoenix Protocol (Database):** Replaced CSV overwrite with SQLite (`leads.db`). Data is now persistent and auto-saved row-by-row.
- **Smart Wizard:** Added a "Magic Button" that reads CSV headers and auto-configures the correct Audit Rules.
- **Stealth Core:** Implemented User-Agent switching. The bot now changes masks (Chrome vs. Edge) based on the column name.
- **Browser Armory:** Created `utils_browser.py` as a shared stealth resource for both Inspector and Harvester.
- **Undo/Redo:** Added a safety net to the Rule Stack to recover deleted rules.

### Fixed
- **Python 3.14 Compatibility:** Fixed a crash caused by `playwright-stealth` library incompatibility by implementing a "Manual Stealth Fallback" (JS Injection).

## [V3.0] - "The Control Center" - 2026-02-02
### Added
- **Process Control:** Added Start, Pause, Resume, and Stop functionality to the Inspector.
- **Batch Limits:** Added auto-pause triggers (e.g., "Pause after 20 rows" or "Pause after 10 minutes").
- **Live Telemetry:** Added a real-time Progress Bar and colored Log Terminal.

## [V2.0] - "The UX Polish" - 2026-02-02
### Added
- **Deep Context Tooltips:** Added hover-over explanations for every button to guide the user.
- **App Guide:** Added a directory summary in the sidebar.
- **Step-by-Step UI:** Reorganized Inspector into clear Steps (1: AI, 2: Upload, 3: Rules, 4: Limits).