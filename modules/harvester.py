import pandas as pd
import json
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
import threading
import time

class HarvesterLogic:
    def get_recipe_names(self):
        """Returns a list of JSON files in the recipes folder."""
        if not os.path.exists("recipes"):
            return []
        files = [f for f in os.listdir("recipes") if f.endswith(".json")]
        return files

    def perform_harvest(self, urls, recipe_name, log_callback, human_mode=False):
        """
        Executes the scraping logic.
        urls: List of URL strings.
        recipe_name: The filename of the recipe (e.g., 'CEO Search.json').
        log_callback: Function to send text updates to the GUI.
        human_mode: Boolean. If True, shows browser and slows down.
        """
        recipe_path = os.path.join("recipes", recipe_name)
        
        # Load Recipe
        try:
            with open(recipe_path, "r") as f:
                recipe = json.load(f)
        except Exception as e:
            log_callback(f"Error loading recipe: {e}")
            return

        # Prepare Output CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join("output", f"harvest_{timestamp}.csv")
        results = []

        log_callback(f"Starting harvest ({'HUMAN MODE (Visible)' if human_mode else 'Headless'}) for {len(urls)} URLs using recipe: {recipe.get('name', 'Unknown')}")

        with sync_playwright() as p:
            # LAUNCH BROWSER (Human vs Robot)
            if human_mode:
                browser = p.chromium.launch(headless=False, slow_mo=1000) # 1s delay
            else:
                browser = p.chromium.launch(headless=True)
                
            context = browser.new_context()
            page = context.new_page()

            for url in urls:
                url = url.strip()
                if not url: 
                    continue
                
                log_callback(f"Scraping: {url}...")
                row = {"URL": url, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                
                try:
                    page.goto(url, timeout=30000) # 30s timeout
                    
                    # --- THE CRITICAL FIX IS HERE ---
                    # We MUST use "body" as the selector
                    page_text = page.inner_text("body") 
                    # --------------------------------

                    # Search for Columns
                    for col in recipe.get("columns", []):
                        col_name = col.get("col_name", "Unknown")
                        keywords = col.get("keywords", "").split(",")
                        
                        found_val = "N/A"
                        for kw in keywords:
                            kw = kw.strip()
                            if kw and kw.lower() in page_text.lower():
                                # Simple extraction: 50 chars context
                                idx = page_text.lower().find(kw.lower())
                                start = max(0, idx - 50)
                                end = min(len(page_text), idx + 50)
                                found_val = page_text[start:end].replace("\n", " ")
                                break # Stop after first keyword match
                        
                        row[col_name] = found_val

                    log_callback(f"Success: {url}")

                except Exception as e:
                    log_callback(f"Failed: {url} - {str(e)}")
                    row["Error"] = str(e)
                
                results.append(row)

            browser.close()

        # Save to CSV
        if results:
            df = pd.DataFrame(results)
            df.to_csv(output_file, index=False)
            log_callback(f"Harvest Complete! Saved to: {output_file}")
        else:
            log_callback("Harvest finished with no data.")
