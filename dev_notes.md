# Developer Diary - LeadGen Factory

## 2026-02-02: The Transformation to V4
Today was a massive sprint. We took the Inspector from a simple script to a robust, fault-tolerant application.

### 🚧 The "Stealth" Crisis
**Problem:** When upgrading to the Stealth Core, the app crashed immediately.
**Root Cause:** I am running Python 3.14 (pre-release), and the third-party library `playwright-stealth` hasn't been updated for it yet. It threw an `ImportError`.
**Solution:** We rewrote `utils_browser.py` to use a "Safe Import".
- It *tries* to load the library.
- If it fails, it catches the error and switches to "Manual Mode".
- **Manual Mode:** We inject JavaScript (`Object.defineProperty`) to delete the `navigator.webdriver` flag manually. The app is now crash-proof.

### 🦅 The Phoenix Protocol
**Decision:** Using CSVs for storage was too risky. If the app crashed on row 99 of 100, we lost everything.
**Implementation:** Switched to SQLite (`leads.db`).
- **Benefit:** "Immortality." The app checks the DB before scanning. If a URL exists, it skips it. This saves API credits and time.

### 🧙 The Smart Wizard
**Idea:** Configuring rules manually is tedious.
**Implementation:** Built a heuristic engine.
- If it sees "Edge" in the CSV header -> It configures the bot to use the Microsoft Edge User-Agent.
- If it sees "Price" -> It configures the AI to extract the price.
- **Result:** I can now setup a complex audit in 1 click.

### 📝 Next Steps
- Implement the "High Accuracy" verification to catch when the AI hallucinates.
- Move the Harvester to use the new `utils_browser.py` core.