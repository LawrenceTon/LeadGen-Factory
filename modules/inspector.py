import pandas as pd
import time
import random
import os
import re
import uuid
import google.generativeai as genai
from datetime import datetime
import sqlite3
import ast

class InspectorLogic:
    def __init__(self, db_path="leads.db"):
        self.db_path = db_path
        self.df = None
        self.rules = []
        self.api_key = None
        self.url_col = None
        self.limit_rows = 0
        self.limit_mins = 0
        self.timeout = 30
        self.stop_requested = False  # <--- FIX: Stop Flag
        self.init_db()

    def init_db(self):
        """Create the database table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS audit_history 
                     (url TEXT PRIMARY KEY, status TEXT, timestamp TEXT)''')
        conn.commit()
        conn.close()

    def set_api_key(self, key):
        self.api_key = key

    def request_stop(self):
        """Called when user clicks STOP button"""
        print("🛑 Stop requested by user...")
        self.stop_requested = True

    def check_log(self, url):
        """Check if URL was already scanned"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT status FROM audit_history WHERE url=?", (url,))
        data = c.fetchone()
        conn.close()
        return data

    def save_log(self, url, status):
        """Save progress to DB"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO audit_history VALUES (?, ?, ?)", 
                  (url, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        print(f"[Saved] Results persisted for {url}")

    def reset_database(self):
        """Wipe the database for a fresh start"""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self.init_db()
            print("🗑️ Database Wiped. Ready for fresh scan.")
        except Exception as e:
            print(f"Error resetting DB: {e}")

    # --- TIER 1: THE SCRIPT SCOUT (Fast Regex) ---
    def extract_price_via_script(self, page):
        """Extracts prices via Regex/Scoring"""
        try:
            text_content = page.locator("body").inner_text()
            matches = re.findall(r'(\$|€|£|USD|EUR)\s?([\d,]+(?:\.\d{2})?)', text_content, re.IGNORECASE)
            
            best_price = None
            highest_score = -1000 
            
            for symbol, amount in matches:
                full_str = f"{symbol}{amount}"
                score = 0
                lower_body = text_content.lower()
                
                if "buy now" in lower_body or "price" in lower_body: score += 100
                if "lease" in lower_body or "rent" in lower_body or "/mo" in lower_body: score -= 5000 
                
                if score > highest_score:
                    highest_score = score
                    best_price = full_str
            
            if highest_score > 0:
                return best_price
        except:
            pass
        return None

    # --- TIER 2: THE AI EXPERT ---
    def perform_ai_analysis(self, prompt, screenshot_path):
        """Dynamic Model Discovery"""
        if not self.api_key: return "AI Error: No Key"

        genai.configure(api_key=self.api_key)
        try:
            myfile = genai.upload_file(screenshot_path)
        except Exception as e:
            return f"AI Upload Error: {str(e)[:50]}"

        valid_model = "models/gemini-1.5-flash"
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if 'flash' in m.name or 'pro' in m.name:
                        valid_model = m.name
                        break 
        except: pass
        
        try:
            model = genai.GenerativeModel(valid_model)
            result = model.generate_content([myfile, prompt])
            return result.text.strip()
        except Exception as e:
            return f"AI Error: {str(e)[:30]}..."

    # --- THE MASTER AUDIT FUNCTION ---
    def perform_audit(self, df=None, url_col=None, rules=None, limit_rows=0, limit_mins=0, *args):
        # 1. LOAD DATA & SANITIZE INPUTS
        self.stop_requested = False # Reset stop flag
        
        if isinstance(df, str):
            try: self.df = pd.read_csv(df)
            except: pass
        elif df is not None: 
            self.df = df
            
        if isinstance(url_col, dict):
            self.url_col = url_col.get("value", list(url_col.values())[0])
        elif url_col:
            self.url_col = str(url_col)

        # AUTO-DETECT COLUMN
        if not self.url_col or (self.df is not None and self.url_col not in self.df.columns):
            print("⚠️ No Domain column selected. Attempting Auto-Detect...")
            possible = [c for c in self.df.columns if "domain" in c.lower() or "url" in c.lower() or "website" in c.lower()]
            if possible: self.url_col = possible[0]
            else: return

        if rules: self.rules = rules
        try: self.limit_rows = int(limit_rows)
        except: self.limit_rows = 0 
        
        if not hasattr(self, 'df') or self.df is None:
            print("❌ Error: No CSV loaded.")
            return

        self.df = self.df.astype(object)
        print(f"[Starting] Found {len(self.df)} rows. Connecting to Neural Database...")
        
        from modules import utils_browser
        playwright, browser, context, page = utils_browser.launch_browser(
            headless=False, 
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        utils_browser.bypass_detection(page) 

        try:
            for index, row in self.df.iterrows():
                # STOP CHECK
                if self.stop_requested:
                    print("🛑 Audit Stopped by User.")
                    break

                # LIMIT CHECK
                if self.limit_rows > 0 and (index + 1) > self.limit_rows:
                    print(f"🛑 Limit Reached: Stopped after {self.limit_rows} rows.")
                    break
                
                target_url = str(row.get(self.url_col)).strip()
                if not target_url or target_url.lower() == "nan": continue
                if not target_url.startswith("http"): target_url = "https://" + target_url

                if self.check_log(target_url):
                     print(f"[Skipping] Already scanned: {target_url}")
                     continue

                print(f"[Scanning] Auditing ({index+1}/{len(self.df)}): {target_url}")

                try: page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                except: pass

                screenshot_path = f"temp_{index}_{uuid.uuid4().hex[:8]}.jpg"
                try:
                    response = page.goto(target_url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                    status_code = response.status if response else 0
                    if "Just a moment" in page.title() or "Security" in page.title():
                        print("🛡️ Cloudflare detected. Waiting 10s...")
                        time.sleep(10)
                    page.screenshot(path=screenshot_path)
                except:
                    status_code = 404
                    import shutil
                    if os.path.exists("modules/assets/blank.jpg"): shutil.copy("modules/assets/blank.jpg", screenshot_path)

                # EXECUTE RULES
                for rule in self.rules:
                    if isinstance(rule, str):
                        try: rule = ast.literal_eval(rule)
                        except: continue
                    
                    # Skip invalid rules (like 'primary_key')
                    if not isinstance(rule, dict) or 'type' not in rule: continue

                    result = ""
                    if rule['type'] == 'status_check':
                        result = "Yes" if 200 <= status_code < 400 else "No"
                    elif rule['type'] == 'ai_analysis':
                        if "price" in rule['prompt'].lower():
                            print("   ⚡ Running Script Scout...")
                            script_price = self.extract_price_via_script(page)
                            if script_price: 
                                print(f"   ✅ Script found: {script_price}")
                                result = script_price
                        
                        if not result and os.path.exists(screenshot_path):
                            print("   🤖 Calling AI Expert...")
                            prompt = rule['prompt'] + " Answer in 1-2 words. If Price, just number."
                            result = self.perform_ai_analysis(prompt, screenshot_path)

                    print(f"   👉 {rule['target_column']}: {result}")
                    self.df.at[index, rule['target_column']] = result
                
                if os.path.exists(screenshot_path):
                    try: os.remove(screenshot_path)
                    except: pass
                self.save_log(target_url, "Done")
                    
        finally:
            utils_browser.close_browser(context, browser, playwright)
            print("[Complete] Audit Finished.")

    # --- FIX: EXPORT HISTORY (Required by Export Button) ---
    def export_history(self):
        """Export the final results to CSV"""
        if self.df is None:
            return False, "No data to export", ""
            
        filename = f"output/audit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        os.makedirs("output", exist_ok=True)
        self.df.to_csv(filename, index=False)
        print(f"💾 Exported to: {filename}")
        return True, "Export Successful", filename