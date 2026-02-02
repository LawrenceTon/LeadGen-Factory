# Silence Google/Pydantic warnings
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import pandas as pd
import os
import re
import time
import threading
import base64
import requests
import json
import uuid
from datetime import datetime
from collections import defaultdict
from playwright.sync_api import sync_playwright
import google.generativeai as genai
import openai
from PIL import Image

from modules.database import LeadDB
from modules.utils_browser import USER_AGENTS, setup_stealth, nuke_popups

class AIHandler:
    @staticmethod
    @staticmethod
    def call_gemini(image_path, prompt, api_key):
        if not api_key:
            return "AI Error: No Key"

        genai.configure(api_key=api_key)

        # 1. Upload File
        try:
            # Use upload_file as requested for better handling
            # Note: For production, we should consider lifecycle of these files, but following spec.
            myfile = genai.upload_file(image_path)
        except Exception as e:
            return f"AI Upload Error: {str(e)[:50]}"

        # 2. ASK THE SERVER: "What models do you have?"
        valid_model = None
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if 'flash' in m.name or 'pro' in m.name:
                        valid_model = m.name
                        break # Found the best one!
        except:
            pass

        # Fallback if discovery fails
        if not valid_model:
            valid_model = "models/gemini-1.5-flash"

        # 3. Generate Content
        try:
            model = genai.GenerativeModel(valid_model)
            result = model.generate_content([myfile, prompt])
            return result.text.strip()
        except Exception as e:
            # Truncate error to prevent CSV mess
            err_msg = str(e)
            if "404" in err_msg: return "AI Error: Model 404"
            if "429" in err_msg: return "AI Error: Quota Limit"
            return f"AI Error: {err_msg[:30]}..."

    @staticmethod
    def call_openai(image_path, prompt, api_key):
        try:
            client = openai.OpenAI(api_key=api_key)
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI Error: {e}")

class InspectorLogic:
    def __init__(self, output_dir="output", timeout=30000):
        self.output_dir = output_dir
        self.timeout = timeout
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.is_running = False
        self.db = LeadDB()

    def request_pause(self):
        self.pause_event.set()

    def request_resume(self):
        self.pause_event.clear()

    def request_stop(self):
        self.stop_event.set()
        self.request_resume()

    def extract_price_via_script(self, page):
        """Tier 1: The Fast Scout (Regex + Scoring from Blueprint)"""
        import re
        try:
            # 1. Grab all visible text (fast)
            text_content = page.locator("body").inner_text()
            
            # 2. Regex for Money ($2,500 | 5000 USD | etc)
            # Looks for: Symbol + Space(optional) + Numbers + Decimals(optional)
            matches = re.findall(r'(\$|€|£|USD|EUR)\s?([\d,]+(?:\.\d{2})?)', text_content, re.IGNORECASE)
            
            best_price = None
            highest_score = -1000 # Baseline
            
            for symbol, amount in matches:
                full_str = f"{symbol}{amount}"
                # Get the surrounding text (context) for scoring
                # (Simple robust check: is 'Buy' near the price?)
                score = 0
                lower_body = text_content.lower()
                
                # BLUEPRINT SCORING SYSTEM
                if "buy now" in lower_body or "price" in lower_body: score += 100
                if "lease" in lower_body or "rent" in lower_body or "/mo" in lower_body: score -= 5000 # Heavy penalty for rental prices
                
                # Logic: If it's a "Buy Now" price, it wins.
                if score > highest_score:
                    highest_score = score
                    best_price = full_str
            
            # Only return if we are confident (Positive score means likely a Buy Price)
            if highest_score > 0:
                return best_price
        except:
            pass
        return None

    def perform_audit(self, csv_arg=None, rules_arg=None, api_arg=None, limits_arg=None, cb_arg=None, *args):
        # 1. DATA LOADER & ARGUMENT UNPACKING
        # Fixes compatibility with main.py which sends: (csv_path, rules, api_config, limits, callback)
        if csv_arg and isinstance(csv_arg, str):
            try:
                if os.path.exists(csv_arg):
                    self.df = pd.read_csv(csv_arg)
                    self.df = self.df.astype(object)
            except Exception as e:
                print(f"Error loading CSV: {e}")

        if rules_arg: self.rules = rules_arg
        
        if api_arg:
             self.api_key = api_arg.get('primary_key')
             
        if limits_arg:
             self.limit_rows = int(limits_arg.get('batch_rows', 0))
             # Handle mins if needed, usually just used for breaks
             
        if limits_arg:
            self.timeout = int(limits_arg.get('timeout_ms', 30000)) / 1000

        # 2. SAFETY CHECK & URL DISCOVERY
        if not hasattr(self, 'df') or self.df is None:
            print("❌ Error: No CSV loaded. Please select a file first.")
            return

        # Discover URL Column
        self.url_col = None
        candidates = ["URL", "url", "Website", "website", "Domain", "domain", "Link", "link"]
        for cand in candidates:
            if cand in self.df.columns:
                self.url_col = cand
                break
        
        if not self.url_col and len(self.df.columns) > 0:
            self.url_col = self.df.columns[0] # Default to first

        print(f"[Starting] Found {len(self.df)} rows. Connecting to Neural Database...")
        from modules import utils_browser
        import time
        import random
        import re
        import google.generativeai as genai

        # 3. LAUNCH BROWSER (STEALTH MODE)
        playwright, browser, context, page = utils_browser.launch_browser(
            headless=False, 
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        utils_browser.bypass_detection(page) 

        try:
            for index, row in self.df.iterrows():
                # [Limit Checks]
                if self.limit_rows > 0 and (index + 1) > self.limit_rows:
                    print(f"🛑 Limit Reached: Stopped after {self.limit_rows} rows.")
                    break

                # URL Setup
                target_url = row.get(self.url_col)
                if not str(target_url).startswith("http"): target_url = "https://" + str(target_url)

                print(f"[Scanning] Auditing ({index+1}/{len(self.df)}): {target_url}")

                # Human Shake
                try: page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                except: pass

                # Navigation
                try:
                    current_timeout = getattr(self, 'timeout', 30) * 1000
                    response = page.goto(target_url, timeout=current_timeout, wait_until="domcontentloaded")
                    status_code = response.status if response else 0
                    final_url = page.url
                    # Cloudflare Bypass
                    if "Just a moment" in page.title() or "Security" in page.title() or "Verify" in page.title():
                        print("🛡️ Cloudflare detected. Waiting 10s...")
                        time.sleep(10)
                        final_url = page.url
                except:
                    status_code = 404
                    final_url = target_url

                # Rules (Waterfall)
                for rule in self.rules:
                    result = ""
                    # Yes/No Logic
                    if rule['type'] == 'status_check':
                        result = "Yes" if 200 <= status_code < 400 else "No"
                    
                    # AI/Script Logic
                    elif rule['type'] == 'ai_analysis':
                        
                        # Use self.extract_price_via_script if it exists, else skip
                        if hasattr(self, 'extract_price_via_script') and "price" in rule['prompt'].lower():
                            print("   ⚡ Running Script Scout...")
                            script_price = self.extract_price_via_script(page)
                            if script_price: 
                                print(f"   ✅ Script found: {script_price}")
                                result = script_price
                        
                        # AI Backup
                        if not result:
                            # Unique filename for screenshots
                            temp_shot = f"temp_{index}_{uuid.uuid4().hex[:8]}.jpg"
                            try:
                                page.screenshot(path=temp_shot, quality=70)
                                print("   🤖 Calling AI Expert...")
                                prompt = rule['prompt'] + " Answer in 1-2 words. If Price, just number. If Marketplace, name it."
                                result = self.perform_ai_analysis(prompt, temp_shot) # Pass path, not bytes if method expects it
                            except Exception as e:
                                result = f"AI Error: {e}"
                            finally:
                                if os.path.exists(temp_shot):
                                    try: os.remove(temp_shot)
                                    except: pass

                    print(f"   👉 {rule['target_column']}: {result}")
                    self.df.at[index, rule['target_column']] = result
                    
        finally:
            utils_browser.close_browser(context, browser, playwright)

    def export_history(self):
        if not hasattr(self, 'df') or self.df is None:
             return False, "No audit data available to export.", ""
        
        filename = "audit_results_FINAL.csv"
        out_path = os.path.join(self.output_dir, filename)
        
        try:
            self.df.to_csv(out_path, index=False)
            print(f"✅ Exported {len(self.df)} rows to 'audit_results_FINAL.csv'")
            return True, f"Exported to {filename}", out_path
        except Exception as e:
            return False, f"Export Failed: {e}", ""

    def reset_database(self):
        try:
            # Force close the connection
            if self.db and self.db.conn:
                self.db.conn.close()
            
            # Delete the file
            db_path = self.db.db_path if self.db else "leads.db"
            if os.path.exists(db_path):
                os.remove(db_path)
            
            # Re-initialize
            self.db = LeadDB()
            print("🗑️ Database Wiped. Ready for fresh scan.")
            return True
        except Exception as e:
            print(f"Reset DB Error: {e}")
            return False
