import pandas as pd
import time
import random
import os
import re
import uuid
import google.generativeai as genai
from datetime import datetime
import sqlite3

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
        self.init_db()

    def init_db(self):
        """Create the database table if it doesn't exist (Phoenix Protocol)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS audit_history 
                     (url TEXT PRIMARY KEY, status TEXT, timestamp TEXT)''')
        conn.commit()
        conn.close()

    def set_api_key(self, key):
        self.api_key = key

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
        """Extracts prices via Regex/Scoring to avoid using AI credits"""
        try:
            # 1. Grab all visible text (fast)
            text_content = page.locator("body").inner_text()
            
            # 2. Regex for Money ($2,500 | 5000 USD | etc)
            matches = re.findall(r'(\$|€|£|USD|EUR)\s?([\d,]+(?:\.\d{2})?)', text_content, re.IGNORECASE)
            
            best_price = None
            highest_score = -1000 # Baseline
            
            for symbol, amount in matches:
                full_str = f"{symbol}{amount}"
                score = 0
                lower_body = text_content.lower()
                
                # SCORING SYSTEM
                if "buy now" in lower_body or "price" in lower_body: score += 100
                if "lease" in lower_body or "rent" in lower_body or "/mo" in lower_body: score -= 5000 
                
                if score > highest_score:
                    highest_score = score
                    best_price = full_str
            
            # Only return if positive confidence
            if highest_score > 0:
                return best_price
        except:
            pass
        return None

    # --- TIER 2: THE AI EXPERT (Gemini) ---
    def perform_ai_analysis(self, prompt, screenshot_path):
        """Dynamic Model Discovery to prevent 404 Errors"""
        if not self.api_key:
            return "AI Error: No Key"

        genai.configure(api_key=self.api_key)
        
        # 1. Upload File
        try:
            myfile = genai.upload_file(screenshot_path)
        except Exception as e:
            return f"AI Upload Error: {str(e)[:50]}"

        # 2. AUTO-DETECT MODEL
        valid_model = "models/gemini-1.5-flash" # Default fallback
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if 'flash' in m.name or 'pro' in m.name:
                        valid_model = m.name
                        break 
        except: pass
        
        # 3. Generate Content
        try:
            model = genai.GenerativeModel(valid_model)
            result = model.generate_content([myfile, prompt])
            return result.text.strip()
        except Exception as e:
            err_msg = str(e)
            if "404" in err_msg: return "AI Error: Model 404"
            if "429" in err_msg: return "AI Error: Quota Limit"
            return f"AI Error: {err_msg[:30]}..."

    # --- THE MASTER AUDIT FUNCTION ---
    def perform_audit(self, df=None, url_col=None, rules=None, limit_rows=0, limit_mins=0, *args):
        import pandas as pd # Ensure pandas is available here

        # 1. LOAD DATA ADAPTER (Smart Fix)
        # CASE A: Input is a Filename (String) -> Load it!
        if isinstance(df, str):
            try:
                self.df = pd.read_csv(df)
            except Exception as e:
                print(f"❌ Error loading CSV: {e}")
                return
        # CASE B: Input is already a DataFrame -> Use it!
        elif df is not None: 
            self.df = df
        if url_col: self.url_col = url_col
        if rules: self.rules = rules
        
        # 2. SANITIZE LIMITS (The Fix)
        # We use try/except to safely handle cases where main.py passes a Dict/List by mistake
        try:
            self.limit_rows = int(limit_rows)
        except (ValueError, TypeError):
            self.limit_rows = 0 # Default to 0 if bad data received
            
        try:
            self.limit_mins = int(limit_mins)
        except (ValueError, TypeError):
            self.limit_mins = 0 # Default to 0 if bad data received

        if not hasattr(self, 'df') or self.df is None:
            print("❌ Error: No CSV loaded.")
            return

        # Force all columns to object to prevent float64 crash
        self.df = self.df.astype(object)

        print(f"[Starting] Found {len(self.df)} rows. Connecting to Neural Database...")
        from modules import utils_browser
        
        # 2. LAUNCH STEALTH BROWSER
        playwright, browser, context, page = utils_browser.launch_browser(
            headless=False, 
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        utils_browser.bypass_detection(page) 

        start_time = time.time()

        try:
            for index, row in self.df.iterrows():
                # LIMIT CHECKS
                if self.limit_rows > 0 and (index + 1) > self.limit_rows:
                    print(f"🛑 Limit Reached: Stopped after {self.limit_rows} rows.")
                    break
                
                # Check Database (Phoenix Protocol)
                target_url = row.get(self.url_col)
                if not str(target_url).startswith("http"): target_url = "https://" + str(target_url)

                if self.check_log(target_url):
                     print(f"[Skipping] Already scanned: {target_url}")
                     continue

                print(f"[Scanning] Auditing ({index+1}/{len(self.df)}): {target_url}")

                # HUMAN SHAKE
                try: 
                    page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                except: pass

                # NAVIGATION & CLOUDFLARE WAIT
                screenshot_path = f"temp_{index}_{uuid.uuid4().hex[:8]}.jpg"
                try:
                    response = page.goto(target_url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                    status_code = response.status if response else 0
                    
                    # *** CLOUDFLARE WAIT ***
                    if "Just a moment" in page.title() or "Security" in page.title() or "Verify" in page.title():
                        print("🛡️ Cloudflare detected. Waiting 10s...")
                        time.sleep(10)

                    final_url = page.url
                    page.screenshot(path=screenshot_path)
                        
                except Exception:
                    status_code = 404
                    final_url = target_url
                    # Create blank dummy screenshot to prevent AI crash
                    import shutil
                    shutil.copy("modules/assets/blank.jpg", screenshot_path) if os.path.exists("modules/assets/blank.jpg") else None

                # EXECUTE RULES (WATERFALL)
                for rule in self.rules:
                    result = ""
                    
                    # LOGIC A: YES/NO
                    if rule['type'] == 'status_check':
                        result = "Yes" if 200 <= status_code < 400 else "No"
                    
                    # LOGIC B: AI + SCRIPT
                    elif rule['type'] == 'ai_analysis':
                        
                        # Step 1: Script Scout (Price Only)
                        if "price" in rule['prompt'].lower():
                            print("   ⚡ Running Script Scout...")
                            script_price = self.extract_price_via_script(page)
                            if script_price: 
                                print(f"   ✅ Script found: {script_price}")
                                result = script_price
                        
                        # Step 2: AI Expert (Backup)
                        if not result and os.path.exists(screenshot_path):
                            print("   🤖 Calling AI Expert...")
                            prompt = rule['prompt'] + " Answer in 1-2 words. If Price, just number. If Marketplace, name it. If generic, say 'Developed'."
                            result = self.perform_ai_analysis(prompt, screenshot_path)

                    print(f"   👉 {rule['target_column']}: {result}")
                    self.df.at[index, rule['target_column']] = result
                
                # Cleanup Screenshot
                if os.path.exists(screenshot_path):
                    try: os.remove(screenshot_path)
                    except: pass
                
                # Save to DB
                self.save_log(target_url, "Done")
                    
        finally:
            utils_browser.close_browser(context, browser, playwright)
            print("[Complete] Audit Finished.")

    def export_results(self):
        filename = "output/audit_results_FINAL.csv"
        os.makedirs("output", exist_ok=True)
        self.df.to_csv(filename, index=False)
        return filename