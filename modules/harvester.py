import os
import json
import datetime
import pandas as pd
from playwright.sync_api import sync_playwright

class HarvesterLogic:
    def __init__(self, recipes_dir="recipes", output_dir="output"):
        self.recipes_dir = recipes_dir
        self.output_dir = output_dir
        self.ensure_dirs()

    def ensure_dirs(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
    def get_recipe_names(self):
        """Returns a list of available recipe names (without .json extension)"""
        try:
            files = [f.replace(".json", "") for f in os.listdir(self.recipes_dir) if f.endswith('.json')]
            return files
        except Exception:
            return []

    def perform_harvest(self, urls, recipe_name, log_callback):
        """
        Executes the scraping process.
        
        Args:
            urls: List of URL strings.
            recipe_name: Name of the recipe to use.
            log_callback: Function to send status updates (msg: str).
        """
        recipe_path = os.path.join(self.recipes_dir, f"{recipe_name}.json")
        if not os.path.exists(recipe_path):
            log_callback(f"Error: Recipe '{recipe_name}' not found.")
            return

        # Load Recipe
        try:
            with open(recipe_path, 'r') as f:
                recipe_data = json.load(f)
                columns_config = recipe_data.get("columns", [])
        except Exception as e:
            log_callback(f"Error loading recipe: {e}")
            return

        results = []
        log_callback(f"Starting harvest for {len(urls)} URLs using recipe: {recipe_name}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            
            for url in urls:
                url = url.strip()
                if not url:
                    continue
                    
                log_callback(f"Scraping: {url}...")
                
                row_data = {"URL": url, "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                
                try:
                    page = context.new_page()
                    # Timeout after 30s
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page_text = page.inner_text().lower() 
                    
                    # Universal Search Logic
                    for col_def in columns_config:
                        col_name = col_def.get("col_name", "Unknown")
                        keywords = col_def.get("keywords", "").lower()
                        
                        if keywords in page_text:
                            # Simple extraction: Grab context around keyword
                            idx = page_text.find(keywords)
                            start = max(0, idx - 50)
                            end = min(len(page_text), idx + 50 + len(keywords))
                            snippet = page_text[start:end].replace("\n", " ")
                            row_data[col_name] = f"...{snippet}..."
                        else:
                            row_data[col_name] = "N/A"
                    
                    log_callback(f"Success: {url}")
                    page.close()
                    
                except Exception as e:
                    log_callback(f"Failed: {url} - {str(e)}")
                    # Fill missing cols with Error
                    for col_def in columns_config:
                         row_data[col_def["col_name"]] = "Error"
                
                results.append(row_data)

            browser.close()

        # Save to CSV
        if results:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"harvest_{timestamp}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            try:
                df = pd.DataFrame(results)
                df.to_csv(filepath, index=False)
                log_callback(f"Harvest Complete! Saved to: {filepath}")
            except Exception as e:
                log_callback(f"Error saving CSV: {e}")
        else:
            log_callback("Harvest finished with no data collected.")
