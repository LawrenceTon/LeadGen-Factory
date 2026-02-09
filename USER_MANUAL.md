# 🏭 LeadGen Factory: Ultimate User Manual

**LeadGen Factory** is a modular desktop application designed to automate the entire lead generation pipeline. It is not just a scraper; it is an AI-powered data factory.

---

# 🚜 MODULE 2: THE HARVESTER (The Lead Finder)
*The engine that discovers new leads.*

1.  **Dual-Engine Logic**: Now simultaneously searches **Google** and **Whoxy.com** to maximize discovery.
2.  **Configuration**: Ensure your `config.json` contains a valid Whoxy API key.
3.  **Human Mode (Stealth):**
    * **✅ Checked:** Opens a visible browser. You can manually solve Captchas. Safe.
    * **❌ Unchecked:** Runs invisible (Headless). Fast.
4.  **Start**: Extracts data to CSV based on your recipe and keywords.

---

# 🧹 MODULE 3: THE JANITOR (The Cleaner)
*Advanced Validation & Hygiene Dashboard.*

* **Load List**: Import any CSV for sanitization.
* **Remove Duplicates**: Deletes repeated Domains and Emails from your set.
* **DNS Check**: Detects and deletes "dead" domains that no longer resolve.
* **Parked Page Filter**: Automatically rejects "For Sale" pages or domains parked on GoDaddy/Sedo.
* **Export Clean**: Saves your high-purity lead list to a new CSV.

---

# 🕵️ MODULE 4: THE INSPECTOR (The AI Vision Engine)
*This is the most advanced module in the system. Unlike standard bots that just read text, the Inspector uses Computer Vision AI to "see" websites like a human analyst.*

## 1. 🧠 AI Setup (Crucial)
To enable the "Super Brain," you must configure your API keys in the Inspector tab.
* **Primary API Key (Gemini):** This connects to Google's Gemini 1.5 Flash model.
* **Backup API Key (Failover):** Automatically switches to this backup if limits are reached.

## 2. 🤖 How to Use "[AI Analysis]"
* **Legitimacy Check**: "Does it look like a real, trustworthy business?"
* **Lead Extraction**: "Find the CEO's name, support email, and address."

---

# 🧠 MODULE 1: THE ARCHITECT (The Strategist)
*Design your scraping blueprints.*
* Define **Targets** (e.g., "Job Title", "Email", "Phone").
* You create a recipe once, and the Harvester uses it forever.

---

## 🚀 Quick Start
**1. Install Dependencies**
```bash
pip install -r requirements.txt
playwright install
```
**2. Configure API Keys**
Add your `WHOXY_API_KEY` to `config.json`.

**3. Run**
```bash
python main.py
```