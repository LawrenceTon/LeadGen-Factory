import pandas as pd
import os
import re
import time
import base64
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright
import google.generativeai as genai
import openai
from PIL import Image

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

    def perform_audit(self, csv_path, rules, api_config, log_callback):
        """
        Executes audit with AI capabilities.
        api_config: {'primary_key': str, 'backup_key': str}
        """
        if not os.path.exists(csv_path):
            log_callback("Error: CSV file not found.")
            return

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            log_callback(f"Error reading CSV: {e}")
            return

        # Find URL column
        url_col = None
        for col in df.columns:
            if "url" in col.lower() or "website" in col.lower() or "link" in col.lower():
                url_col = col
                break
        
        if not url_col:
            log_callback("Error: Could not find a 'URL' column.")
            return

        urls = df[url_col].dropna().astype(str).tolist()
        log_callback(f"Starting audit on {len(urls)} URLs...")

        results = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            
            for url in urls:
                url = url.strip()
                if not url: continue

                log_callback(f"Auditing: {url}...")
                row_data = {"Original_URL": url}
                
                try:
                    page = context.new_page()
                    response = page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    
                    status = response.status if response else "Error"
                    final_url = page.url
                    page_text = page.inner_text("body").lower()

                    for rule in rules:
                        r_type = rule.get('type')
                        
                        if r_type == 'status_check':
                            row_data['Status_Code'] = status
                            row_data['Final_URL'] = final_url
                            
                        elif r_type == 'keyword':
                            val = rule.get('value', '').lower()
                            col_name = f"Has_{rule['value']}"
                            row_data[col_name] = str(val in page_text)
                                
                        elif r_type == 'extract_price':
                            price_pattern = r'(\$[\d,]+(\.\d{2})?)|(\b\d{1,3}(,\d{3})*(\.\d{2})?\s*USD\b)'
                            matches = re.search(price_pattern, page_text)
                            row_data['Detected_Price'] = matches.group(0) if matches else "N/A"
                            
                        elif r_type == 'ai_analysis':
                            prompt = rule.get('prompt', 'Describe this page.')
                            col_name = f"AI_{prompt[:10].replace(' ', '_')}"
                            
                            # Take Screenshot
                            temp_shot = "temp_screenshot.jpg"
                            page.screenshot(path=temp_shot, quality=70) # optimize size
                            
                            ai_response = "Error"
                            
                            # Attempt Primary (Gemini assumed default for now as requested)
                            try:
                                key = api_config.get('primary_key')
                                if not key: raise Exception("No Primary Key")
                                log_callback("  > Asking Gemini...")
                                ai_response = AIHandler.call_gemini(temp_shot, prompt, key)
                            except Exception as e_primary:
                                log_callback(f"  > Primary AI Failed: {e_primary}")
                                
                                # Failover
                                key_backup = api_config.get('backup_key')
                                if key_backup:
                                    log_callback("  > Switching to Backup (OpenAI/Gemini)...")
                                    try:
                                        # Simple logic: If backup provided, try OpenAI as secondary?
                                        # Or just try Gemini again with different key? 
                                        # User request implies Provider switching.
                                        # We will assume Backup is OpenAI for this implementation based on requirements.
                                        ai_response = AIHandler.call_openai(temp_shot, prompt, key_backup)
                                    except Exception as e_backup:
                                       ai_response = f"Backup Failed: {e_backup}"
                                else:
                                    ai_response = f"Failed: {e_primary}"
                            
                            row_data[col_name] = ai_response
                            
                            # Clean up
                            if os.path.exists(temp_shot):
                                os.remove(temp_shot)

                    page.close()
                    log_callback(f"Success: {url}")

                except Exception as e:
                    log_callback(f"Failed: {url} - {e}")
                    row_data['Error'] = str(e)
                
                results.append(row_data)

            browser.close()

        if results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_{timestamp}.csv"
            out_path = os.path.join(self.output_dir, filename)
            
            result_df = pd.DataFrame(results)
            result_df.to_csv(out_path, index=False)
            log_callback(f"Audit Complete! Saved to: {out_path}")
        else:
             log_callback("Audit finished with no results.")
