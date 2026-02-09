# CHANGELOG

## [v1.0 - The Antigravity Edition] - 2026-02-05
**"The shift from scraping to hunting."**

### 🚀 Core Engineering
*   **Vacuum Protocol**: Removed reliance on specific `div.g` selectors. The bot now ingests the entire SERP and parses links locally.
*   **Nordic Normalization**: Added `_normalize_text()` to handle international characters (`Ø`, `Å`, `Ü`) explicitly.
*   **Snippet Sniping**: Added logic to regex-scan the search result preview text (`body.inner_text`) before clicking links, catching emails hidden behind login walls.
*   **Parallel Hunting**: Enforced simultaneous checks for Corporate Domains and Personal Providers (Gmail/Outlook) for every target.

### ✨ Features
*   **Predictive Dorking**: The bot now generates likely email patterns and searches for the *string itself* rather than asking a question.
*   **Deep Dive v2**: Improved "Human Scroll" and "Internal Click" logic to mimic a real user exploring a homepage.

---

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
- **Script-First Protocol:** Inspector now prioritizes local script execution over AI.
- **Dynamic Execution Engine:** Implemented `analyze_lander_script` to detect marketplaces.
- **Safety Net**: Fallback to text scan if AI fails.
- **Context-Aware Price Extraction**: Enhanced regex logic.
- **Cost Savings**: Zero-cost auditing for resolved marketplaces.
