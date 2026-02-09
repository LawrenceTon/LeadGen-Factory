import os
import datetime
import subprocess

# Content Definitions
ANTIGRAVITY_LOGIC = """# 📜 THE ANTIGRAVITY CONSTITUTION (Immutable Laws)

This document establishes the verified protocols for the LeadGen Factory. Failure to adhere to these 5 rules is a critical system failure.

## 1. THE VACUUM PROTOCOL (Selector Agnosticism)
**"Grab everything, filter later."**
*   Never rely on specific CSS selectors (like `div.g` or `span.email`).
*   **Action:** Always fetch **ALL** links (`a[href]`) and **ALL** body text, then filter locally using Python logic.

## 2. THE NORDIC TRANSFORMATION (Data Sanitization)
**"Computers struggle with international characters; we do not."**
*   **Action:** Before any matching logic, strictly normalize inputs using a custom transliteration map (e.g., `Ø` → `o`, `Å` → `a`, `Ü` → `u`).

## 3. PREDICTIVE DORKING (Answer-Based Search)
**"Do not ask questions. Search for answers."**
*   Do not query: "Who is the CEO of Company X?"
*   **Action:** Calculate the likely answer first (e.g., `covregaard@gmail.com` or `"John Doe" @company.com`) and search for that specific string to bypass privacy filters.

## 4. PARALLEL HUNTING (Dual-Track Architecture)
**"A target has two lives: Corporate and Personal."**
*   **Action:** Always execute simultaneous searches for `@{company_domain}` and `@gmail` / `@outlook`. Finding one does **NOT** stop the hunt for the other.

## 5. SNIPPET SNIPING (Pre-Click Analysis)
**"The truth is often in the preview."**
*   Data is often visible in the search preview but hidden behind login walls on the site.
*   **Action:** Always regex-scan the raw HTML of the search results page (`res.inner_text()`) **before** navigating away.
"""

README_UPDATE = """🏭 LeadGen Factory: Antigravity Edition

**"Human-Grade Intuition. Machine-Grade Speed."**

LeadGen Factory is a modular, desktop-based automation suite designed for high-performance lead generation, data harvesting, list cleaning, and quality assurance. It does not just scrape; it *hunts* using the "Antigravity" protocols—Vacuuming data, normalizing inputs, and sniping snippets before they disappear.

## 🚀 Key Features (v1.0 Antigravity)

### 1. The Vacuum Protocol
We stopped playing "Whack-a-Mole" with Google's CSS selectors. The bot now grabs **ALL** links and **ALL** text from the DOM and filters them locally. It is immune to minor layout changes.

### 2. Nordic Normalization
Built for the global market. `Øvregaard` becomes `ovregaard` automatically. We never miss a lead because of an accent mark.

### 3. Predictive Dorking
We don't ask "Who is the CEO?". We calculate the email (`ceo@company.com`) and search for *that*. It bypasses privacy filters by finding the answer, not the question.

### 4. Parallel Hunting
Every target is hunted on two tracks simultaneously:
*   **Corporate:** `name@company.com`
*   **Personal:** `name@gmail.com` / `name@outlook.com`

---

## 📂 The Modules

| Module | Role | Function |
| :--- | :--- | :--- |
| **The Architect** | 🧠 Strategy | Visual recipe builder. Define "CEO" or "Marketing Director" and let the bot figure out the queries. |
| **The Harvester** | 🚜 Execution | The core engine. Runs the "Antigravity" protocols to find emails, socials, and phone numbers. |
| **The Janitor** | 🧹 Hygiene | Cleans lists, splits names, and removes toxic keywords (e.g., "LLC", "Inc"). |
| **The Inspector** | 🕵️ Audit | Validates emails and checks if websites are alive (200 OK) before you export. |

---

## 🛠️ How to Use

1.  **Launch** the application (`main.py`).
2.  **Harvester Tab**:
    *   **Genesis Mode**: Enter a keyword (e.g., "Solar Installers Texas") to find companies.
    *   **Sniper Mode**: Enter a specific person and company to hunt their details.
    *   **Bulk Mode**: Load a CSV and select a strategy ("Find CEO", "Find Email").
3.  **Janitor Tab**: Load your results to clean up formatting.
4.  **Export**: Save your "Gold Standard" list to CSV.

---

## 📜 The 5 Laws (Antigravity Constitution)
See `ANTIGRAVITY_LOGIC.md` for the core engineering principles governing this software.

*Property of Lawrence Anthony Juntilla*
"""

CHANGELOG_UPDATE = """# CHANGELOG

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
"""

def sync():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("1. Writing ANTIGRAVITY_LOGIC.md...")
    with open("ANTIGRAVITY_LOGIC.md", "w", encoding="utf-8") as f:
        f.write(ANTIGRAVITY_LOGIC)
        
    print("2. Writing README.md...")
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(README_UPDATE)
        
    print("3. Writing CHANGELOG.md...")
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(CHANGELOG_UPDATE)
        
    print("4. Executing Git Operations...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        commit_msg = f"Core Update: v1.0 Antigravity Edition [{timestamp}]"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ SUCCESS: Operation Cloud Sync Complete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git Error: {e}")

if __name__ == "__main__":
    sync()
