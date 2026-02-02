import os

# PART 1: Introduction
header = """# 🏭 LeadGen Factory: Ultimate User Manual

**LeadGen Factory** is a modular desktop application designed to automate the entire lead generation pipeline. It is not just a scraper; it is an AI-powered data factory.

---
"""

# PART 2: THE INSPECTOR (The Special Section)
inspector_section = """
# 🕵️ MODULE 4: THE INSPECTOR (The AI Vision Engine)
*This is the most advanced module in the system. Unlike standard bots that just read text, the Inspector uses Computer Vision AI to "see" websites like a human analyst.*

## 1. 🧠 AI Setup (Crucial)
To enable the "Super Brain," you must configure your API keys in the Inspector tab.
* **Primary API Key (Gemini):** This connects to Google's Gemini 1.5 Flash model. It is fast, free (up to 15 req/min), and handles complex vision tasks.
* **Backup API Key (Failover):** If Google limits your usage, the system **automatically switches** to this backup key (OpenAI or Secondary Gemini) so your audit never stops.

## 2. 🛠️ The Rule Builder
The Inspector works by stacking "Rules." You can mix and match these checks for every website:

| Rule Type | Function | Use Case |
| :--- | :--- | :--- |
| **Check Status** | Pings the site (200 OK, 404 Dead). | Cleaning lists & finding broken links. |
| **Contains Keyword** | Scans visible text for words. | Filtering (e.g., "Out of Stock", "Hiring"). |
| **Extract Price** | Auto-detects currency ($/£/€). | Competitor pricing analysis. |
| **[AI Analysis]** | **Vision AI Integration.** | Asking complex questions about the site's image. |

## 3. 🤖 How to Use "[AI Analysis]"
This is the special feature. When selected, the bot takes a high-res screenshot of the site and sends it to the AI.

**You can ask the AI anything. Copy these "Pro Prompts":**

* **Legitimacy Check:**
    > "Analyze this page. Does it look like a real, trustworthy business or a scam/low-quality site? Answer LEGIT or SUSPICIOUS and explain why."

* **Lead Extraction (Advanced):**
    > "Find the CEO's name, the support email, and the physical address. If not found, look for a 'Contact Us' link context. Return format: Name | Email | Address."

* **Business Model Classifier:**
    > "What is the primary way this website makes money? (e.g., Dropshipping, SaaS, Agency, Blog). One word answer."

* **Design Audit:**
    > "Rate the visual design of this landing page on a scale of 1-10. List 3 improvements."

---
"""

# PART 3: The Other Modules
other_modules = """
# 🚜 MODULE 2: THE HARVESTER (The Lead Finder)
*The engine that discovers new leads.*
1.  **Select Recipe:** Choose a strategy created in the Architect.
2.  **Human Mode (Stealth):**
    * **✅ Checked:** Opens a visible browser. You can manually solve Captchas. Safe.
    * **❌ Unchecked:** Runs invisible (Headless). Fast.
3.  **Start:** Extracts data to CSV based on your recipe.

---

# 🧠 MODULE 1: THE ARCHITECT (The Strategist)
*Design your scraping blueprints.*
* Define **Targets** (e.g., "Job Title", "Email", "Phone").
* You create a recipe once, and the Harvester uses it forever.

---

# 🧹 MODULE 3: THE JANITOR (The Cleaner)
*Polishes your raw data.*
* **Remove Duplicates:** deletes repeated rows.
* **Split Names:** "Lawrence Anthony" -> "Lawrence", "Anthony".
* **Format:** Prepares files for CRM/Email tools.

---

## 🚀 Quick Start
**1. Install Dependencies**
```bash
pip install -r requirements.txt
playwright install