import pandas as pd
import json
import os
import re
import requests
import dns.resolver
import whois
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from pydantic import BaseModel, Field, ConfigDict, ValidationError
from datetime import datetime
from playwright.sync_api import sync_playwright
import threading
import time

# --- Pydantic Model for Data Integrity ---
class LeadData(BaseModel):
    URL: str
    Timestamp: str
    Match_Type: str = Field(alias="Match Type")
    Current_Domain: str = Field(alias="Current Domain", default="")
    Viability_Score: int = Field(alias="Viability Score", ge=0, le=100)
    Target_Role_Strategy: str = Field(alias="Target Role Strategy", default="N/A")
    Notes: str = ""
    # Allow extra columns dynamic from recipe
    model_config = ConfigDict(extra='allow') 

class HarvesterLogic:
    NEGATIVE_KEYWORDS = ['school', 'clinic', 'church', 'university', 'non-profit', 'charity', 'foundation', 'academy']

    def __init__(self):
        self.last_dataframe = None

    def get_recipe_names(self):
        """Returns a list of JSON files in the recipes folder."""
        if not os.path.exists("recipes"):
            return []
        files = [f for f in os.listdir("recipes") if f.endswith(".json")]
        return files

    def _extract_employee_count(self, text):
        """Attempts to find employee count text like '50-100 employees'."""
        match = re.search(r'(\d+(?:,\d+)?[\-\+]\d+(?:,\d+)?|\d+(?:,\d+)?\+?)\s+employees?', text, re.IGNORECASE)
        if match:
            val_str = match.group(1).replace(',', '').replace('+', '')
            if '-' in val_str:
                try: return int(val_str.split('-')[0])
                except: return 0
            else:
                try: return int(val_str)
                except: return 0
        return 0

    def _calculate_viability(self, mode, target_roles_found, public_verification, employee_count):
        """Calculates 0-100 score based on framework rules."""
        score = 10
        if mode == 'Corporate Brand Mode':
            if target_roles_found:
                score = 100
            elif employee_count > 0:
                score = 50 
        elif mode == 'Public Figure Mode':
            if public_verification['verified']:
                score = 100
            elif public_verification['followers'] > 100000:
                score = 80
            elif public_verification['followers'] > 10000:
                score = 50
        return score

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), retry=retry_if_exception_type(Exception))
    def _resolve_domain_dns(self, url):
        """
        Resolution Gatekeeper: Uses dnspython to check for A or MX records.
        Much faster than loading a full HTTP request.
        """
        try:
            domain = url.replace("https://", "").replace("http://", "").split('/')[0]
            try:
                dns.resolver.resolve(domain, 'A')
                return True
            except:
                # Try MX if A fails (some email-only domains)
                try:
                    dns.resolver.resolve(domain, 'MX')
                    return True
                except:
                    return False
        except Exception:
            return False

    def _get_domain_age_years(self, url):
        """Returns domain age in years or None if lookup fails."""
        try:
            domain = url.replace("https://", "").replace("http://", "").split('/')[0]
            w = whois.whois(domain)
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            
            if creation_date:
                age_delta = datetime.now() - creation_date
                return age_delta.days / 365.25
            return None
        except:
            return None

    def _discover_companies_via_linkedin(self, keyword, page, log_callback):
        """
        LinkedIn-First Discovery Engine:
        1. Searches Google for LinkedIn Company pages matching the keyword.
        2. Visits each LinkedIn page ('About' section).
        3. Extracts the official 'Website' link.
        """
        discovered_urls = []
        try:
            # 1. Google Search Proxy
            search_query = f"site:linkedin.com/company/ {keyword}"
            search_url = f"https://www.google.com/search?q={search_query}"
            log_callback(f"🔎 Discovery: Searching '{keyword}' on LinkedIn via Google...")
            
            page.goto(search_url, timeout=30000)
            page.wait_for_selector("div.g", timeout=5000)
            
            # Extract LinkedIn URLs from Google Results
            linkedin_links = []
            results = page.locator("div.g a").all()
            for res in results:
                url = res.get_attribute("href")
                if url and "linkedin.com/company/" in url and "translate.google" not in url:
                    linkedin_links.append(url)
            
            linkedin_links = list(set(linkedin_links))[:3] # Limit to top 3 matches for relevance
            log_callback(f"   Found {len(linkedin_links)} potential company profiles.")

            # 2. Visit LinkedIn & Extract Website
            for li_url in linkedin_links:
                try:
                    # Visit About section directly if possible, or just the main page
                    target_li = li_url if "/about" in li_url else f"{li_url.rstrip('/')}/about/"
                    log_callback(f"   Analysing: {target_li}...")
                    
                    page.goto(target_li, timeout=30000)
                    
                    # Heuristic to find Website: Look for "Website" text or external links
                    # LinkedIn often hides it in a <dl> or section.
                    # We try to get the page content and find links.
                    
                    # Strategy A: Specific Selector (Brittle)
                    # Strategy B: Find 'Website' text and look near it (Robust)
                    
                    content = page.content()
                    # Simple regex to find the official website in the definition list or similar
                    # Often like: <dt>Website</dt><dd><a href="http://example.com"...>
                    
                    website_url = None
                    
                    # Try Playwright locator approach
                    # Look for an 'a' tag that is visually near "Website" text?
                    # Or simple extracted text links:
                    
                    # Let's try to extract all external links and pick the most likely "Home" page
                    links = page.locator("a").all()
                    for link in links:
                        href = link.get_attribute("href")
                        text = link.inner_text().lower()
                        
                        if not href or "linkedin.com" in href or "google.com" in href: continue
                        if not href.startswith("http"): continue
                        
                        # Strong signals
                        if "website" in text or "visit" in text:
                            website_url = href
                            break
                            
                        # If we have a generic link that matches the keyword somewhat, candidate it
                        # (Skipping deep logic for now to keep it fast)
                        
                    if website_url:
                        log_callback(f"   ✅ Extracted Official Site: {website_url}")
                        discovered_urls.append(website_url)
                    else:
                        # Fallback: Try a quick text scan for "Website http..."
                        pass

                except Exception as e:
                    log_callback(f"   ⚠️ Failed to extract from {li_url}: {e}")

        except Exception as e:
            log_callback(f"Discovery Error: {e}")
            
        return list(set(discovered_urls))

    def perform_harvest(self, urls, recipe_name, log_callback, human_mode=False, search_mode='Corporate Brand Mode', keyword_input=None):
        """
        Executes the scraping logic with Developer Toolkit enhancements.
        """
        self.last_dataframe = None # Reset previous session
        recipe_path = os.path.join("recipes", recipe_name)
        recipe = {}
        try:
            with open(recipe_path, "r") as f:
                recipe = json.load(f)
        except Exception as e:
            if recipe_name != "No Recipes Found":
                log_callback(f"Error loading recipe: {e}")
                return

        all_urls = []
        if urls: all_urls.extend([u.strip() for u in urls if u.strip()])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join("output", f"harvest_{timestamp}.csv")
        results = []
        mode = search_mode

        with sync_playwright() as p:
            log_callback(f"Initializing Browser (Human Mode: {human_mode})...")
            if human_mode:
                browser = p.chromium.launch(headless=False, slow_mo=1000)
            else:
                browser = p.chromium.launch(headless=True)
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            # --- PIPELINE ENGINE ---
            # Strict Visual-Order Execution: Index 0 -> Index N
            
            # Initial Seed: If we have URLs entered manually, they are our starting "Leads"
            # If we have a keyword but NO URLs, we expect the first column to be "Discovery_Engine"
            
            current_leads = []
            if all_urls:
                 # Seed leads from manual input
                 for u in all_urls:
                     current_leads.append({
                         "URL": u, 
                         "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         "Match Type": "Potential",
                         "Viability Score": 0,
                         "Notes": "Manual Entry. "
                     })
            elif keyword_input and not all_urls:
                # Seed with a placeholder to allow Discovery Engine to run
                current_leads.append({
                    "URL": None, # No URL yet
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Match Type": "Seed",
                    "Viability Score": 0,
                    "Notes": f"Seed Keyword: {keyword_input} "
                })

            log_callback(f"Starting Pipeline Execution for {len(current_leads)} seed items...")

            # 1. Pipeline Loop
            columns = recipe.get("columns", [])
            if not columns and not all_urls:
                 log_callback("Error: No recipe columns and no manual URLs. Pipeline empty.")
                 return

            for col_idx, col in enumerate(columns):
                col_name = col.get("col_name", "Unknown")
                logic_type = col.get("logic_type", "Standard")
                raw_keywords = col.get("keywords", "")
                
                # Dynamic Injection
                processed_keywords = raw_keywords
                if keyword_input:
                     processed_keywords = raw_keywords.replace("{keyword}", keyword_input)
                else:
                     processed_keywords = raw_keywords.replace("{keyword}", "")
                
                log_callback(f"Executing Step {col_idx+1}: {col_name} [{logic_type}]...")
                
                new_leads_list = [] # For Discovery phase which might expand 1 seed -> N leads
                
                for lead in current_leads:
                    # Skip dead/blocked leads unless this is a Revival step (advanced, not impl yet)
                    if lead.get("Match Type") in ["Dead Asset", "Blocked"]:
                        new_leads_list.append(lead)
                        continue

                    url = lead.get("URL")
                    
                    try:
                        # --- LOGIC HANDLERS ---
                        
                        # A. DISCOVERY ENGINE
                        if logic_type == "Discovery_Engine":
                            if url: 
                                # If we already have a URL, maybe we skip discovery or re-verify?
                                # For strictness, if this is a Discovery step, maybe we look for *related* entities?
                                # Current logic: Discovery generates URLs from Keyword.
                                new_leads_list.append(lead) # Keep original
                            elif keyword_input:
                                # Run Discovery
                                discovered = self._discover_companies_via_linkedin(keyword_input, page, log_callback)
                                for d_url in discovered:
                                    new_lead = lead.copy()
                                    new_lead["URL"] = d_url
                                    new_lead["Match Type"] = "Discovered"
                                    new_lead["Notes"] += "LinkedIn Discovery. "
                                    new_leads_list.append(new_lead)
                                if not discovered:
                                     lead["Notes"] += "Discovery Failed. "
                                     new_leads_list.append(lead)
                            else:
                                new_leads_list.append(lead)

                        # B. RESOLUTION GATEKEEPER
                        elif logic_type == "Resolution_Gatekeeper":
                            if not url: 
                                lead["Notes"] += "Skip Gatekeeper (No URL). "
                                new_leads_list.append(lead)
                                continue
                                
                            if self._resolve_domain_dns(url):
                                # Valid
                                pass 
                            else:
                                lead["Match Type"] = "Dead Asset"
                                lead["Notes"] += "DNS Failed. "
                            new_leads_list.append(lead)

                        # C. VIABILITY FILTER & SCORE
                        elif logic_type == "Viability_Filter" or logic_type == "Viability_Score":
                             if not url or lead.get("Match Type") == "Dead Asset":
                                new_leads_list.append(lead)
                                continue
                             
                             # Load Page
                             try:
                                 page.goto(url, timeout=30000)
                                 lead["Current Domain"] = page.url
                                 page_text = page.inner_text("body")
                                 
                                 # Block
                                 shield_hit = False
                                 for neg in self.NEGATIVE_KEYWORDS:
                                     if neg in page_text.lower():
                                         lead["Match Type"] = "Blocked"
                                         lead["Notes"] += f"Blocked by '{neg}'. "
                                         shield_hit = True
                                         break
                                 
                                 if not shield_hit and logic_type == "Viability_Score":
                                     # Simple scoring logic re-used
                                     emp_count = self._extract_employee_count(page_text)
                                     lead["Viability Score"] = 50 + (emp_count if emp_count else 0)
                                     
                             except Exception as e:
                                 lead["Notes"] += f"Page Load Error: {e} "
                             
                             new_leads_list.append(lead)

                        # D. CHAMPION SELECTOR
                        elif logic_type == "Champion_Selector":
                             if not url or lead.get("Match Type") in ["Dead Asset", "Blocked"]:
                                new_leads_list.append(lead)
                                continue

                             try:
                                 page.goto(url, timeout=30000)
                                 page_text = page.inner_text("body")
                                 
                                 # Look for keywords which are Roles
                                 roles = processed_keywords.split(",")
                                 found_role = None
                                 for role in roles:
                                     role = role.strip()
                                     if role and role.lower() in page_text.lower():
                                         found_role = role
                                         break
                                 
                                 if found_role:
                                     lead[col_name] = found_role
                                     lead["Target Role Strategy"] = found_role
                                     lead["Viability Score"] = 100
                                     lead["Notes"] += f"Champion Found: {found_role}. "
                                 else:
                                     lead["Notes"] += "No Champion Found. "
                                     
                             except Exception as e:
                                 lead["Notes"] += f"Error: {e} "
                             
                             new_leads_list.append(lead)

                        # E. STANDARD (Extraction)
                        else:
                             if not url or lead.get("Match Type") in ["Dead Asset", "Blocked"]:
                                new_leads_list.append(lead)
                                continue
                                
                             try:
                                 page.goto(url, timeout=30000)
                                 page_text = page.inner_text("body")
                                 
                                 kws = processed_keywords.split(",")
                                 for kw in kws:
                                     kw = kw.strip()
                                     if kw and kw.lower() in page_text.lower():
                                         idx = page_text.lower().find(kw.lower())
                                         start = max(0, idx - 50)
                                         end = min(len(page_text), idx + 50)
                                         lead[col_name] = page_text[start:end].replace("\n", " ").strip()
                                         break
                             except: pass
                             new_leads_list.append(lead)

                    except Exception as e:
                        log_callback(f"Pipeline Error on {col_name}: {e}")
                        new_leads_list.append(lead)
                
                # Update main list for next column
                current_leads = new_leads_list

            browser.close()

        # Save Results
        if current_leads:
            # Filter out seeds that never got a URL
            final_leads = [l for l in current_leads if l.get("URL")]
            
            if final_leads:
                df = pd.DataFrame(final_leads)
                self.last_dataframe = df 
                
                # Reorder
                cols = ["URL", "Match Type", "Viability Score", "Current Domain", "Target Role Strategy", "Notes"]
                existing_cols = [c for c in cols if c in df.columns]
                other_cols = [c for c in df.columns if c not in existing_cols]
                df = df[existing_cols + other_cols]
                
                df.to_csv(output_file, index=False)
                log_callback(f"Pipeline Complete! {len(final_leads)} Results Saved to: {output_file}")
            else:
                 log_callback("Pipeline finished. No valid URL-based leads generated.")
        else:
            log_callback("Pipeline finished. No results.")
