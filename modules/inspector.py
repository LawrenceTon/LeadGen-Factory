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
    def call_gemini(image_path, prompt, api_key):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            img = Image.open(image_path)
            response = model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            raise Exception(f"Gemini Error: {e}")

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
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
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

    def perform_audit(self, csv_path, rules, api_config, limits, callback):
        self.stop_event.clear()
        self.pause_event.clear()
        self.is_running = True
        
        if not os.path.exists(csv_path):
            callback(0, "Error", "CSV file not found.")
            return

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            callback(0, "Error", f"Error reading CSV: {e}")
            return

        # URL Column Discovery
        url_col = None
        for col in df.columns:
            if "url" in col.lower() or "website" in col.lower() or "link" in col.lower():
                url_col = col
                break
        
        if not url_col:
            callback(0, "Error", "Could not find a 'URL' column.")
            return

        urls = df[url_col].dropna().astype(str).tolist()
        total = len(urls)
        callback(0, "Starting", f"Found {total} URLs. Connecting to Neural Database...")

        batch_limit = limits.get('batch_rows', 0)
        time_limit_min = limits.get('batch_minutes', 0)
        start_time = time.time()
        newly_processed = 0
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            for i, url in enumerate(urls):
                url = url.strip()
                if not url: continue
                
                # --- PHOENIX PROTOCOL CHECK ---
                if self.db.record_exists(url):
                    callback((i+1)/total, "Skipping", f"Already scanned: {url}")
                    continue

                if self.stop_event.is_set():
                    callback((i/total), "Stopped", "Audit stopped by user.")
                    break
                
                while self.pause_event.is_set():
                    callback((i/total), "Paused", "Audit Paused. Waiting...")
                    time.sleep(1);
                    if self.stop_event.is_set(): break
                
                # Limits Loop
                elapsed_min = (time.time() - start_time) / 60
                if (batch_limit > 0 and newly_processed >= batch_limit) or (time_limit_min > 0 and elapsed_min >= time_limit_min):
                    self.pause_event.set()
                    newly_processed = 0
                    start_time = time.time()
                    callback((i/total), "Paused", "Auto-Pause: Limit Reached.")
                    while self.pause_event.is_set():
                         if self.stop_event.is_set(): break
                         time.sleep(1)

                newly_processed += 1
                callback((i+1)/total, "Scanning", f"Auditing ({i+1}/{total}): {url}")
                
                results_map = {}
                
                # --- GROUP RULES BY USER AGENT ---
                # Sort rules into buckets: Chrome, Edge, Mobile
                rules_by_ua = defaultdict(list)
                for r in rules:
                    ua_key = r.get('user_agent', 'Chrome')
                    rules_by_ua[ua_key].append(r)
                
                # --- THE TRUTH ENFORCER (SWITCH MASKS) ---
                for ua_name, ua_rules in rules_by_ua.items():
                    actual_ua = USER_AGENTS.get(ua_name, None)
                    
                    callback((i+1)/total, "Switching", f"🎭 Switching Mask to {ua_name}...")
                    
                    context = None
                    try:
                        # Create Fresh Context with specific UA
                        context = browser.new_context(user_agent=actual_ua)
                        page = context.new_page()
                        setup_stealth(page)

                        # Navigation
                        try:
                            response = page.goto(url, timeout=30000, wait_until="domcontentloaded")
                            nuke_popups(page)
                            status_code = response.status if response else "Error"
                            # Basic Text Extraction
                            try:
                                page_text = page.inner_text("body").lower()
                            except:
                                page_text = ""
                        except Exception:
                            status_code = "Error"
                            page_text = ""

                        # Execute Rules for this Mask
                        for rule in ua_rules:
                            r_type = rule.get('type')
                            result_val = "N/A"
                            
                            if r_type == 'status_check':
                                result_val = str(status_code)
                            elif r_type == 'keyword':
                                val = rule.get('value', '').lower()
                                result_val = str(val in page_text)
                            elif r_type == 'extract_price':
                                price_pattern = r'(\$[\d,]+(\.\d{2})?)|(\b\d{1,3}(,\d{3})*(\.\d{2})?\s*USD\b)'
                                matches = re.search(price_pattern, page_text)
                                result_val = matches.group(0) if matches else "N/A"
                            elif r_type == 'ai_analysis':
                                prompt = rule.get('prompt', 'Describe this page.')
                                temp_shot = f"temp_{i}_{ua_name}.jpg"
                                try:
                                    page.screenshot(path=temp_shot, quality=70)
                                    key = api_config.get('primary_key')
                                    if not key: raise Exception("No Primary Key")
                                    result_val = AIHandler.call_gemini(temp_shot, prompt, key)
                                except Exception as e_ai:
                                    key_bk = api_config.get('backup_key')
                                    if key_bk:
                                        try:
                                            result_val = AIHandler.call_openai(temp_shot, prompt, key_bk)
                                        except:
                                            result_val = f"AI Error: {e_ai}"
                                    else:
                                        result_val = f"AI Error: {e_ai}"
                                finally:
                                    if os.path.exists(temp_shot): os.remove(temp_shot)
                            
                            # Persistent Write
                            t_col = rule.get('target_column')
                            if t_col:
                                results_map[t_col] = result_val
                            else:
                                results_map[f"{r_type}_{ua_name}"] = result_val

                        page.close()
                        context.close()
                    except Exception as e_mask:
                        callback((i+1)/total, "Error", f"Mask {ua_name} error: {e_mask}")
                        if context: 
                            try: context.close()
                            except: pass

                # --- SAVE DATA ---
                self.db.save_audit(url, "Scanned", json.dumps(results_map))
                callback((i+1)/total, "Saved", f"Results persisted for {url}")

            browser.close()

        callback(1.0, "Complete", "Audit Finished. Data stored in leads.db (Phoenix Protocol).")
        self.is_running = False

    def export_history(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_full_history_{timestamp}.csv"
        out_path = os.path.join(self.output_dir, filename)
        
        success, msg = self.db.export_to_csv(out_path)
        return success, msg if success else f"Export Failed: {msg}", out_path
