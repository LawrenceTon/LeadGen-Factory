import customtkinter as ctk
import pandas as pd
import json
import os
import re
import requests
import dns.resolver
import whois
import random
import io
import unicodedata
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from datetime import datetime
import threading
import time
import asyncio
from playwright.async_api import async_playwright
from modules.utils_browser import launch_browser, setup_stealth, perform_manual_intervention, check_active_session, human_click

# Try to import image libraries (Safe Fallback)
try:
    from PIL import Image
    import imagehash
    IMAGE_LIB_AVAILABLE = True
except ImportError:
    IMAGE_LIB_AVAILABLE = False

class HarvesterLogic:
    def __init__(self):
        self.last_dataframe = None
        self.stop_requested = False
        self._load_config()

    def _load_config(self):
        # We no longer need the Whoxy API Key, but we'll keep the method for future settings
        pass

    def request_stop(self):
        self.stop_requested = True

    def _clean_to_root_domain(self, url):
        if not url: return None
        try:
            if not url.startswith("http"): url = "https://" + url
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
        except: return url

    def _normalize_text(self, text):
        if not text: return ""
        replacements = {
            "ø": "o", "Ø": "o",
            "æ": "ae", "Æ": "ae",
            "å": "a", "Å": "a",
            "ü": "u", "Ü": "u",
            "ö": "o", "Ö": "o",
            "ä": "a", "Ä": "a",
            "ß": "ss",
            "é": "e", "è": "e"
        }
        cleaned = text
        for char, rep in replacements.items():
            cleaned = cleaned.replace(char, rep)
        try:
            normalized = unicodedata.normalize('NFKD', cleaned).encode('ascii', 'ignore').decode('utf-8')
            return normalized.lower()
        except:
            return cleaned.lower()

    def _distill_google_url(self, raw_url):
        if not raw_url: return None
        # 1. Check for Google Redirect
        if "/url?q=" in raw_url:
            try:
                clean = raw_url.split("/url?q=")[1].split("&")[0]
                from urllib.parse import unquote
                return unquote(clean)
            except: pass
            
        # 2. Filter out internal Google junk
        if "google.com" in raw_url or "googleusercontent" in raw_url:
            return None

        # 3. Return as is if it looks valid
        if raw_url.startswith("http"):
            return raw_url
            
        return None

    async def _deep_dive_scan(self, page, url, log_callback, context_tag):
        scraped_content = ""
        try:
            log_callback(f"         👉 Deep Dive ({context_tag}): Opening {url[:40]}...")
            await page.goto(url, timeout=35000, wait_until="domcontentloaded")
            for i in range(3): 
                await page.evaluate(f"window.scrollBy(0, {random.randint(400, 800)})")
                await asyncio.sleep(0.5)
            content = await page.locator("body").inner_text()
            scraped_content += content
            if "@" not in content:
                contact_links = page.locator("a[href*='contact'], a[href*='about'], a[href*='team']")
                if await contact_links.count() > 0:
                    try:
                        await contact_links.first.click(timeout=3000)
                        await page.wait_for_load_state("domcontentloaded", timeout=5000)
                        scraped_content += " " + await page.locator("body").inner_text()
                    except: pass
            mailtos = await page.evaluate("""() => { return Array.from(document.querySelectorAll('a[href^="mailto:"]')).map(a => a.href); }""")
            scraped_content += " " + " ".join(mailtos)
            return scraped_content
        except Exception as e: return scraped_content

    async def _scrape_whoxy_browser(self, keyword, page, log_callback):
        """
        Directly navigates to Whoxy.com/keyword/{keyword} and vacuums domain matches.
        No API key required.
        """
        log_callback(f"   🦄 Whoxy Engine Active (Scraping): https://www.whoxy.com/keyword/{keyword}")
        candidates = []
        
        try:
            # 1. Navigate
            url = f"https://www.whoxy.com/keyword/{keyword}"
            await page.goto(url, timeout=60000)
            
            # Wait for content or CAPTCHA check
            await asyncio.sleep(2)
            if "captcha" in page.url.lower():
                await perform_manual_intervention(page, "Whoxy CAPTCHA detected. Please solve.", style=0x30)
            
            # 2. Vacuum Protocol (Grab all links)
            links = await page.locator("a[href]").all()
            log_callback(f"      🔎 Vacuuming {len(links)} elements on Whoxy...")
            
            seen_domains = set()
            for link in links:
                try:
                    text_content = await link.inner_text()
                    href = await link.get_attribute("href")
                    
                    # We are looking for domains in the search result table
                    # Usually Whoxy links results to their own whois pages e.g. /domain-name.com
                    # or displays them as text.
                    domain = None
                    if href and href.startswith("/") and len(href) > 5 and "." in href:
                        domain = href.strip("/")
                    elif text_content and "." in text_content and len(text_content.split(".")) >= 2:
                        # Fallback to text match if it looks like a domain
                        domain = text_content.strip()
                    
                    if domain and "whoxy.com" not in domain.lower() and "." in domain:
                         if domain not in seen_domains:
                             seen_domains.add(domain)
                             candidates.append({
                                 "Domain": f"https://{domain}",
                                 "Page Title": f"Whoxy Result: {domain}",
                                 "Source": "Whoxy (Scraped)"
                             })
                             # log_callback(f"         ✅ Whoxy Match: {domain}")
                except: continue

            log_callback(f"      🦄 Whoxy found {len(candidates)} potential domains via Vacuum.")

        except Exception as e:
            log_callback(f"   ⚠️ Whoxy Scraping Error: {e}")
            
        return candidates

    async def _scrape_google_serp_active(self, keyword, page, log_callback):
        self.stop_requested = False
        base_query = f"\"{keyword}\" \"contact us\" -site:linkedin.com -site:facebook.com -site:instagram.com"
        
        # Safe Query Encoding
        from urllib.parse import quote_plus
        encoded_query = quote_plus(base_query)
        
        log_callback(f"   🛑 Google Engine Active: '{base_query}'")
        
        candidates = []
        seen_urls = set()
        
        # Explicit Iteration (Max 10 Pages)
        # We construct URLs directly to avoid "Next" button failures
        max_pages = 10
        
        for page_num in range(1, max_pages + 1):
            if self.stop_requested: break
            
            # Google Logic: start=0 (Page 1), start=10 (Page 2), etc.
            start_index = (page_num - 1) * 10
            url = f"https://www.google.com/search?q={encoded_query}&start={start_index}"
            
            log_callback(f"   🕷️ Scraping Page {page_num}...")
            
            try:
                # 1. Navigate
                await page.goto(url, timeout=60000)
                if page_num == 1:
                    await perform_manual_intervention(page, "Solve CAPTCHA if needed.", style=0x30)
                
                # 2. Human Scroll (Trigger lazy loads)
                for _ in range(3):
                    await page.evaluate(f"window.scrollBy(0, {random.randint(500, 900)})")
                    await asyncio.sleep(random.uniform(0.8, 1.2))
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1.5)

                # 3. Check End of Results
                body_text = await page.locator("body").inner_text()
                if "did not match any documents" in body_text:
                    log_callback("   🛑 End of results (Google limit).")
                    break

                # 4. Extract & Filter (Container-based for Context)
                # We target multiple common Google result containers to be robust
                result_containers = await page.locator("div.g, div.MjjYud, div.tF2Cxc").all()
                if not result_containers:
                     # Fallback 1
                     result_containers = await page.locator("div[data-header-feature]").all()
                
                log_callback(f"      🔎 Analyzing {len(result_containers)} structured results...")

                # FALLBACK MODE: If structured containers fail, use raw links
                use_fallback = len(result_containers) == 0
                if use_fallback:
                     log_callback("      ⚠️ Structured scraping failed. Switching to RAW LINK MODE.")
                     # Grab all links in the main search area
                     result_containers = await page.locator("#search a[href]").all()

                found_on_page = 0
                for container in result_containers:
                    try:
                        # Extract Data based on Mode
                        if use_fallback:
                            link_el = container
                            text_content = await container.inner_text() 
                            title = text_content.strip() if text_content else "Raw Link Result"
                        else:
                            text_content = await container.inner_text()
                            link_el = container.locator("a[href]").first
                            if await link_el.count() == 0: continue
                            title_el = container.locator("h3").first
                            title = await title_el.inner_text() if await title_el.count() > 0 else "Scraped Result"

                        raw_href = await link_el.get_attribute("href")
                        clean_href = self._distill_google_url(raw_href)
                        if not clean_href: continue
                        
                        # Define ROOT here before using it
                        root = self._clean_to_root_domain(clean_href)
                        if not root: continue

                        # RELEVANCE CHECK (Strict Domain/Name Match)
                        
                        # 1. Cleaner Keyword Parsing
                        try:
                            clean_keyword = keyword.strip().strip("'").strip('"').lower()
                            fuzzy_keyword = clean_keyword.replace(" ", "").replace("-", "")
                        except:
                            clean_keyword = str(keyword).lower()
                            fuzzy_keyword = clean_keyword

                        root_lower = root.lower()
                        
                        full_domain_str = root_lower.split("//")[-1].split("/")[0]
                        clean_domain_str = full_domain_str.replace("-", "").replace(".", "")

                        is_match = False
                        if clean_keyword in full_domain_str:
                            is_match = True
                        elif fuzzy_keyword in clean_domain_str:
                            is_match = True
                        
                        # DEBUG: Explicitly log the first few comparisons to see WHY it failed
                        # if found_on_page < 3 and not is_match:
                        #      log_callback(f"DEBUG: '{clean_keyword}' vs '{full_domain_str}' -> {is_match}")
                        
                        if not is_match:
                            continue

                        # Add Valid Candidate
                        if root and root not in seen_urls:
                            seen_urls.add(root)
                            candidates.append({"Domain": root, "Page Title": title, "Source": "Google"})
                            found_on_page += 1
                            log_callback(f"         ✅ Accepted: {root} (MATCH: {full_domain_str})")

                    except Exception as e:
                        log_callback(f"Error parsing container: {e}")
                        continue

                if found_on_page > 0:
                    log_callback(f"      ✅ Found {found_on_page} matches.")
                else:
                    log_callback(f"      ⚠️ No matches on Page {page_num} (Strict Domain Filter).")

            except Exception as e:
                log_callback(f"   ⚠️ Page Error: {e}")
            
            # Pause before next page
            await asyncio.sleep(random.uniform(2, 4))
        
        log_callback("   🛑 Scraper Finished. Closing browser...")
        await asyncio.sleep(3) 
        return candidates

    async def find_ceo(self, current_leads, page, log_callback):
        self.stop_requested = False
        log_callback(f"   🕵️ Starting CEO Hunt (Fundamentals Applied)...")
        
        # 📚 BATCH CACHE (Redundancy Killer)
        # Stores results for (Company, Domain) pairs to prevent re-scanning the same target 50 times.
        search_cache = {}

        for idx, lead in enumerate(current_leads):
            if self.stop_requested: break
            company = lead.get("Company Name")
            domain = lead.get("Website")
            
            # Normalize keys for cache lookups
            cache_key = (company.lower() if company else None, domain.lower() if domain else None)

            # Skip if we already have a person
            if lead.get("Decision Maker") and lead.get("Decision Maker") != "Unknown":
                continue

            # 🛑 SAFETY CHECK (Garbage In, Garbage Out)
            # We strictly cannot hunt a CEO if we don't know the Company OR the Domain.
            # Searching generic "CEO" results in hallucinations (e.g. "Scott").
            if not company and not domain:
                log_callback(f"      ⚠️ [{idx+1}] Skipping: Missing Company Name & Domain. Cannot hunt.")
                lead["Decision Maker"] = "Missing Target Info"
                continue

            # 🚀 CACHE CHECK
            if cache_key in search_cache:
                cached = search_cache[cache_key]
                lead["Decision Maker"] = cached["Decision Maker"]
                lead["LinkedIn Profile"] = cached["LinkedIn Profile"]
                log_callback(f"      ⚡ [{idx+1}] Instant Fill (Cached): {cached['Decision Maker']}")
                continue

            # Query 1: LinkedIn Role Dorking
            query = f'site:linkedin.com/in/ ("CEO" OR "Founder" OR "Owner" OR "Principal") '
            if company: query += f'"{company}"'
            elif domain: query += f'"{domain}"'
            
            # Query 2: Broad "Team" Search (Fallback)
            query_broad = f'"{company}" ("CEO" OR "Founder" OR "Owner")'

            found = False
            
            # Try Queries
            for q_active in [query, query_broad]:
                if found: break
                
                try:
                    log_callback(f"      🕸️ Scanning for Boss ({idx+1}): {q_active[:50]}...")
                    await page.goto(f"https://www.google.com/search?q={q_active}", timeout=40000)
                    
                    try:
                        await page.wait_for_selector("div#search", timeout=5000)
                    except:
                        pass
                    
                    # VACUUM + DISTILL (Strict Filtering)
                    links = await page.locator("a[href]").all()
                    
                    for link in links:
                        raw_href = await link.get_attribute("href")
                        
                        # CRITICAL FIX: Distill BEFORE checking
                        clean_href = self._distill_google_url(raw_href)
                        if not clean_href: continue
                        
                        # Match Logic: Only accept valid LinkedIn Profiles
                        if "linkedin.com/in/" in clean_href:
                            try:
                                # 🧹 CLEANING PROTOCOL: Remove fragments/queries
                                base_url = clean_href.split("?")[0].split("#")[0]
                                
                                # Extract Name from URL Slug
                                slug = base_url.split("/in/")[1].split("/")[0]
                                slug_parts = slug.split("-")
                                
                                # Filter out garbage (hex codes, numbers)
                                name_parts = [
                                    p.capitalize() for p in slug_parts 
                                    if not re.match(r'^[\d\w]{10,}$', p) and not p.isdigit() 
                                    and p.lower() not in ["ceo", "founder", "owner", "profile"]
                                ]
                                
                                if len(name_parts) >= 1:
                                    guessed_name = " ".join(name_parts)
                                    # NORDIC TRANSFORMATION (Normalization)
                                    # Ensure we return clean, standard text
                                    guessed_name = self._normalize_text(guessed_name).title()
                                    
                                    lead["Decision Maker"] = guessed_name
                                    lead["LinkedIn Profile"] = base_url
                                    
                                    # SAVE TO CACHE
                                    search_cache[cache_key] = {"Decision Maker": guessed_name, "LinkedIn Profile": base_url}

                                    log_callback(f"      ✅ CEO Identified: {guessed_name}")
                                    log_callback(f"         🔗 Profile: {base_url}")
                                    found = True
                                    break
                            except: pass
                except Exception as e:
                    log_callback(f"Error: {e}")
                
                await asyncio.sleep(1.5)
            
            if not found:
                log_callback("      ❌ No clear CEO profile found.")
                lead["Decision Maker"] = "Unknown"
                # Cache the failure too, so we don't retry impossible searches
                search_cache[cache_key] = {"Decision Maker": "Unknown", "LinkedIn Profile": None}

    async def find_company_name(self, current_leads, page, log_callback):
        self.stop_requested = False
        for idx, lead in enumerate(current_leads):
            if self.stop_requested: break
            # Skip if we already have info
            if lead.get("Company Name") and lead.get("Website"): continue

            raw_url = lead.get("Website")
            if not raw_url: continue
            if not str(raw_url).startswith("http"): raw_url = "https://" + str(raw_url)
            
            log_callback(f"   [{idx+1}] 🕵️ Visiting: {raw_url}")
            try:
                await page.goto(raw_url, timeout=45000)
                title = await page.title()
                lead["Company Name"] = title.split("|")[0].strip()
                log_callback(f"      ✅ Identified: {lead['Company Name']}")
            except: lead["Company Name"] = "Unknown"

    async def find_email_address(self, current_leads, page, log_callback):
        self.stop_requested = False
        EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        log_callback(f"   📧 Starting Pattern-Smart Email Hunt...")

        for idx, lead in enumerate(current_leads):
            if self.stop_requested: break
            # Skip if verified email exists
            if lead.get("Email") and "Unverified" not in str(lead.get("Email")) and "Not Found" not in str(lead.get("Email")):
                continue

            ceo_name = lead.get("Decision Maker") or lead.get("Person Name")
            company = lead.get("Company Name")
            domain = lead.get("Website")

            # 🛑 SAFETY CHECK: strict skip for missing names or placeholders
            if not ceo_name or ceo_name in ["Unknown", "Missing Target Info"]:
                log_callback(f"   [{idx+1}] ⚠️ Skipping: No valid Person Name ({ceo_name}).")
                continue

            clean_name = re.sub(r'[\(\[].*?[\)\]]', '', ceo_name) 
            clean_name = clean_name.replace("CEO", "").replace("Founder", "").strip()
            norm_name = self._normalize_text(clean_name)
            log_callback(f"   [{idx+1}] 🧅 Target: {clean_name} @ {company or 'Unknown'}")

            if (not domain or str(domain).lower() == "nan") and company:
                try:
                    await page.goto(f"https://www.google.com/search?q={company} official site", timeout=30000)
                    
                    try: 
                        await page.wait_for_selector("div#search", timeout=5000)
                    except: 
                        pass
                    
                    links = await page.locator("a[href]").all()
                    for link in links:
                        href = await link.get_attribute("href")
                        clean_href = self._distill_google_url(href)
                        if clean_href and "http" in clean_href and "google" not in clean_href and "linkedin" not in clean_href:
                            domain = self._clean_to_root_domain(clean_href)
                            lead["Website"] = domain
                            break
                except: pass

            clean_dom = ""
            if domain:
                clean_dom = domain.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

            guesses = []
            found_emails = [] 
            if clean_dom:
                parts = norm_name.split(" ")
                parts = [p for p in parts if len(p) > 1]
                if len(parts) >= 1:
                    f = parts[0]
                    l = parts[-1] if len(parts) > 1 else ""
                    guesses = [
                        f"{f}@{clean_dom}", f"{f}.{l}@{clean_dom}", f"{f}{l}@{clean_dom}",
                        f"{f[0]}{l}@{clean_dom}", f"{l}@{clean_dom}"
                    ]
            
            strategies = []
            if guesses: strategies.append((f'"{guesses[0]}" OR "{guesses[1]}"', "Corporate (Predictive)"))
            strategies.append((f'"{clean_name}" ("@gmail.com" OR "@outlook.com")', "Personal (Predictive)"))
            if company: strategies.append((f'"{clean_name}" "{company}" email', "Broad (Context)"))

            for q, label in strategies:
                if self.stop_requested: break
                try:
                    log_callback(f"      🕸️ Scanning ({label}): {q[:40]}...")
                    await page.goto(f"https://www.google.com/search?q={q}", timeout=40000)
                    
                    try:
                        await page.wait_for_selector("div#search", timeout=5000)
                    except:
                        pass
                    
                    body_text = await page.locator("body").inner_text()
                    snippet_emails = re.findall(EMAIL_REGEX, body_text)
                    for e in snippet_emails:
                        if self._validate_email_match(e, norm_name, clean_dom, company):
                            if e not in found_emails:
                                found_emails.append(f"{e} (Snippet)")
                                log_callback(f"      ✅ FOUND (Snippet): {e}")

                    links_to_visit = []
                    raw_links = await page.locator("a[href]").all()
                    for link in raw_links:
                        try:
                            href = await link.get_attribute("href")
                            clean_href = self._distill_google_url(href)
                            if clean_href and "http" in clean_href and "google" not in clean_href:
                                if any(x in clean_href.lower() for x in [norm_name.replace(" ", ""), "email", "contact", "profile", "rocketreach", "proff"]):
                                    links_to_visit.append(clean_href)
                        except: pass
                        if len(links_to_visit) >= 5: break

                    for link in links_to_visit:
                        content = await self._deep_dive_scan(page, link, log_callback, "Deep Scan")
                        found = re.findall(EMAIL_REGEX, content)
                        for e in found:
                            if self._validate_email_match(e, norm_name, clean_dom, company):
                                if e not in found_emails:
                                    found_emails.append(f"{e} (Deep Dive)")
                                    log_callback(f"      ✅ FOUND (Page): {e}")
                except: pass
                await asyncio.sleep(1)

            if found_emails:
                unique_emails = list(set(found_emails))
                lead["Email"] = ", ".join(unique_emails)
                lead["Email Source"] = "Smart Hunt"
            else:
                if guesses:
                    best = ", ".join(guesses[:3])
                    lead["Email"] = f"Unverified Guesses: {best}"
                else:
                    lead["Email"] = "Not Found"
            await asyncio.sleep(2)

    def _validate_email_match(self, email, norm_name, domain, company):
        e_lower = email.lower()
        if domain and domain in e_lower: return True
        is_personal = any(x in e_lower for x in ["gmail", "outlook", "yahoo", "hotmail", "icloud", "proton"])
        if is_personal:
            parts = norm_name.split()
            first = parts[0]
            last = parts[-1] if len(parts) > 1 else ""
            if first in e_lower: return True
            if len(first) > 0 and (first[0] + last) in e_lower: return True 
            if last in e_lower and first[0] in e_lower: return True 
        return False

    async def find_social_media(self, current_leads, page, log_callback, platforms=None):
        self.stop_requested = False
        if platforms is None: platforms = ["LinkedIn", "Facebook", "Instagram"]
        if "LinkedIn" in platforms:
            platforms.remove("LinkedIn")
            platforms.insert(0, "LinkedIn")
        
        platform_dorks = { "LinkedIn": "site:linkedin.com/in/", "Facebook": "site:facebook.com", "Instagram": "site:instagram.com" }
        patterns = {
            "LinkedIn": r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/([\w\-%]+)",
            "Facebook": r"https?://(?:www\.)?facebook\.com/(?:[a-zA-Z0-9\.]+|profile\.php\?id=[0-9]+)",
            "Instagram": r"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_\.]+)"
        }

        for idx, lead in enumerate(current_leads):
            if self.stop_requested: break
            name = lead.get("Decision Maker") or lead.get("Person Name")
            company = lead.get("Company Name")

            # 🛑 SAFETY CHECK: strict skip for missing names or placeholders
            if not name or name in ["Unknown", "Missing Target Info"]:
                continue

            # Skip if all requested platforms found
            all_found = True
            for p in platforms:
                if not lead.get(f"{p} Profile"): all_found = False
            if all_found: continue

            log_callback(f"   [{idx+1}] 🕸️ Hunting Socials for: {name}...")
            extracted_handle = None

            for platform in platforms:
                # Skip if already found
                if lead.get(f"{platform} Profile"): continue

                dork = platform_dorks.get(platform)
                strategies = []
                if extracted_handle and platform != "LinkedIn":
                    strategies.append((f"{dork} \"{extracted_handle}\"", "Pivot (Handle)"))
                if company:
                    strategies.append((f"{dork} \"{name}\" \"{company}\"", "Strict (Name+Company)"))
                strategies.append((f"{dork} \"{name}\"", "Broad (Name Only)"))

                found_for_platform = False
                for query, label in strategies:
                    if found_for_platform: break
                    if self.stop_requested: break
                    try:
                        await page.goto(f"https://www.google.com/search?q={query}", timeout=45000)
                        
                        # FIXED: Multi-line try/except
                        try:
                            await page.wait_for_selector("div#search", timeout=5000)
                        except:
                            pass
                        
                        links = await page.locator("a[href]").all()
                        for link in links:
                            raw_href = await link.get_attribute("href")
                            clean_href = self._distill_google_url(raw_href)
                            if not clean_href: continue
                            match = re.search(patterns.get(platform), clean_href)
                            if match:
                                final_url = match.group(0)
                                if platform == "LinkedIn":
                                    if "/in/" not in final_url or len(final_url) < 30: continue
                                    extracted_handle = match.group(1) 
                                    log_callback(f"      💡 Handle Detected: {extracted_handle} (Pivoting...)")
                                if platform == "Facebook" and ("public" in final_url or "pages" in final_url): continue
                                lead[f"{platform} Profile"] = final_url
                                log_callback(f"      ✅ {platform}: {final_url}")
                                found_for_platform = True
                                break
                    except: pass
                    await asyncio.sleep(1)

    async def execute_strategy_async(self, input_data, strategy_name, log_callback, keyword=None, target_platform=None):
        self.last_dataframe = None
        self.stop_requested = False
        current_leads = []
        
        if strategy_name == "Find_Companies":
            log_callback(f"🚀 Executing Genesis: {keyword}...")
        else:
            if input_data is None or input_data.empty: 
                log_callback("⚠️ No data loaded.")
                return
            current_leads = input_data.to_dict('records')
            log_callback(f"🚀 Executing Enrichment ({strategy_name}) on {len(current_leads)} rows...")

        async with async_playwright() as p:
            playwright, browser, context, page = await launch_browser(headless=False, playwright_instance=p)
            await setup_stealth(page)

            if strategy_name == "Find_Companies":
                 # DUAL-ENGINE (Browser Based): Run Google and Whoxy in parallel on separate pages
                 log_callback("🚀 Launching Dual-Page Parallel Engines...")
                 
                 # Create a second page for Whoxy
                 whoxy_page = await context.new_page()
                 await setup_stealth(whoxy_page)
                 
                 # Define tasks
                 google_task = self._scrape_google_serp_active(keyword, page, log_callback)
                 whoxy_task = self._scrape_whoxy_browser(keyword, whoxy_page, log_callback)
                 
                 # Run concurrently
                 results_tuple = await asyncio.gather(google_task, whoxy_task)
                 google_results = results_tuple[0]
                 whoxy_results = results_tuple[1]
                 
                 # Clean up second page
                 await whoxy_page.close()
                 
                 # MERGE & DEDUPE
                 all_results = google_results + whoxy_results
                 seen_domains = set()
                 unique_results = []
                 
                 for item in all_results:
                     dom = item.get("Domain")
                     if dom:
                         # Normalize to root domain for deduping
                         root = self._clean_to_root_domain(dom)
                         if root and root not in seen_domains:
                             seen_domains.add(root)
                             unique_results.append(item)
                 
                 log_callback(f"📊 Dual-Engine Complete. Merged {len(google_results)} (Google) + {len(whoxy_results)} (Whoxy) -> {len(unique_results)} Unique Domains.")

                 if unique_results:
                     for item in unique_results:
                         current_leads.append(item)
            
            elif strategy_name == "Sniper_Mode":
                log_callback(f"🎯 TRIGGERED: Sniper Scan -> Target: {target_platform}")
                if target_platform == "Find CEO":
                    await self.find_ceo(current_leads, page, log_callback)
                else:
                    if not current_leads[0].get("Decision Maker") and not current_leads[0].get("Person Name"):
                         log_callback("⚠️ Missing Person Name. Cannot hunt Email/Socials.")
                    else:
                        if target_platform == "Email":
                             await self.find_email_address(current_leads, page, log_callback)
                        elif target_platform == "Full Profile (All)":
                            await self.find_email_address(current_leads, page, log_callback)
                            await self.find_social_media(current_leads, page, log_callback, ["LinkedIn", "Facebook", "Instagram"])
                        elif target_platform == "LinkedIn Profile":
                             await self.find_social_media(current_leads, page, log_callback, ["LinkedIn"])

            elif strategy_name == "Find_Email": 
                await self.find_email_address(current_leads, page, log_callback)
            
            # --- NEW AUTO-FILL GAP ANALYSIS ---
            elif strategy_name == "Auto_Fill_Missing":
                log_callback("🧩 Strategy: Auto-Fill Missing Data (Intelligent Gap Analysis)...")
                
                # 1. Company/Website Gaps
                missing_company = [l for l in current_leads if not l.get("Company Name") or not l.get("Website")]
                if missing_company:
                    log_callback(f"   📉 Found {len(missing_company)} rows missing Company Info. Hunting...")
                    await self.find_company_name(missing_company, page, log_callback)

                # 2. CEO Gaps
                missing_ceo = [l for l in current_leads if not l.get("Decision Maker") or l.get("Decision Maker") == "Unknown"]
                if missing_ceo:
                    log_callback(f"   📉 Found {len(missing_ceo)} rows missing CEO. Hunting...")
                    await self.find_ceo(missing_ceo, page, log_callback)

                # 3. Email Gaps (Requires Decision Maker to work best)
                missing_email = [l for l in current_leads if (l.get("Decision Maker") and l.get("Decision Maker") != "Unknown") and (not l.get("Email") or "Unverified" in str(l.get("Email")))]
                if missing_email:
                    log_callback(f"   📉 Found {len(missing_email)} rows missing Email. Hunting...")
                    await self.find_email_address(missing_email, page, log_callback)

                # 4. Social Gaps (Requires Decision Maker)
                missing_social = [l for l in current_leads if (l.get("Decision Maker") and l.get("Decision Maker") != "Unknown") and not l.get("LinkedIn Profile")]
                if missing_social:
                    log_callback(f"   📉 Found {len(missing_social)} rows missing Socials. Hunting...")
                    await self.find_social_media(missing_social, page, log_callback)

            try: await browser.close()
            except: pass
            
            if current_leads:
                self.last_dataframe = pd.DataFrame(current_leads)
                if strategy_name == "Sniper_Mode":
                    log_callback("\n" + "="*30)
                    log_callback("   🎯 SNIPER REPORT SUMMARY")
                    log_callback("="*30)
                    res = current_leads[0]
                    if res.get("Decision Maker"): log_callback(f"👤 Name: {res.get('Decision Maker')}")
                    if res.get("Website"): log_callback(f"🌐 Website: {res.get('Website')}")
                    if res.get("Email"): log_callback(f"📧 Email: {res.get('Email')}")
                    if res.get("LinkedIn Profile"): log_callback(f"🔗 LinkedIn: {res.get('LinkedIn Profile')}")
                    log_callback("="*30 + "\n")
                else:
                    log_callback(f"✅ Process Complete. Results ready in memory.")

    def execute_strategy(self, input_data, strategy_name, log_callback, keyword=None, target_platform=None):
        asyncio.run(self.execute_strategy_async(input_data, strategy_name, log_callback, keyword, target_platform))

    def export_data(self, filename):
        if self.last_dataframe is not None:
            self.last_dataframe.to_csv(filename, index=False)
            return True, "Saved."
        return False, "No data."

# --- UI MODULE ---
class HarvesterModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.logic = HarvesterLogic()
        self.setup_ui()

    def setup_ui(self):
        head = ctk.CTkFrame(self)
        head.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(head, text="🚜 The Harvester: Lead Factory (SOP Enhanced)", font=("Arial", 18, "bold")).pack(side="left", padx=10)

        # GENESIS ROW
        row_gen = ctk.CTkFrame(self)
        row_gen.pack(fill="x", padx=10, pady=5)
        self.entry_keyword = ctk.CTkEntry(row_gen, placeholder_text="Enter Brand Keyword", width=300)
        self.entry_keyword.pack(side="left", padx=10, pady=10)
        self.btn_find = ctk.CTkButton(row_gen, text="🔍 Find Companies", command=self.run_genesis, fg_color="#FF9800")
        self.btn_find.pack(side="left", padx=5)

        # INDIVIDUAL SNIPER ROW
        self.row_sniper = ctk.CTkFrame(self)
        self.row_sniper.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.row_sniper, text="Individual Sniper:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        
        self.entry_company = ctk.CTkEntry(self.row_sniper, placeholder_text="Company Name", width=200)
        self.entry_company.pack(side="left", padx=5)
        
        self.entry_domain = ctk.CTkEntry(self.row_sniper, placeholder_text="Domain (Optional)", width=150)
        self.entry_domain.pack(side="left", padx=5)

        self.entry_person = ctk.CTkEntry(self.row_sniper, placeholder_text="Person Name (Required)", width=200)
        self.entry_person.pack(side="left", padx=5)
        
        # Updated Values: Added "Find CEO"
        self.sniper_target = ctk.CTkComboBox(self.row_sniper, values=["Full Profile (All)", "Email", "LinkedIn Profile", "Find CEO"], width=160, command=self.update_sniper_ui)
        self.sniper_target.set("Full Profile (All)")
        self.sniper_target.pack(side="left", padx=5)
        
        self.btn_sniper = ctk.CTkButton(self.row_sniper, text="🎯 Search", command=self.run_sniper_scan, fg_color="#8E44AD", width=80)
        self.btn_sniper.pack(side="left", padx=5)

        # BULK ENRICHMENT ROW
        row_enrich = ctk.CTkFrame(self)
        row_enrich.pack(fill="x", padx=10, pady=5)
        self.btn_load = ctk.CTkButton(row_enrich, text="📂 Load CSV", command=self.load_csv, fg_color="#1F6AA5", width=120)
        self.btn_load.pack(side="left", padx=5)
        
        ctk.CTkLabel(row_enrich, text="Strategy:").pack(side="left", padx=(10, 5))
        # UPDATED COMBOBOX: Added "Auto-Fill Missing Data"
        self.strategy_var = ctk.StringVar(value="Auto-Fill Missing Data")
        self.combo_strategy = ctk.CTkComboBox(row_enrich, values=["Auto-Fill Missing Data", "Find CEO", "Find Email", "Find Company Name"], variable=self.strategy_var, width=180)
        self.combo_strategy.pack(side="left", padx=5)
        
        self.btn_run_enrich = ctk.CTkButton(row_enrich, text="▶️ Run Bulk", command=self.run_enrichment_strategy, fg_color="#2B7A0B", width=80)
        self.btn_run_enrich.pack(side="left", padx=5)
        
        # CONTROLS ROW
        row_ctrl = ctk.CTkFrame(self)
        row_ctrl.pack(fill="x", padx=10, pady=5)
        self.btn_stop = ctk.CTkButton(row_ctrl, text="🛑 STOP", command=self.stop_process, fg_color="red", width=100)
        self.btn_stop.pack(side="left", padx=5)
        self.btn_restart = ctk.CTkButton(row_ctrl, text="🔄 Restart / Clear", command=self.restart_app, fg_color="gray", width=120)
        self.btn_restart.pack(side="left", padx=5)
        self.btn_export = ctk.CTkButton(row_ctrl, text="💾 Export Data", command=self.export_csv, fg_color="green", width=120)
        self.btn_export.pack(side="right", padx=10)
        
        self.log_box = ctk.CTkTextbox(self, height=400, font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

    def update_sniper_ui(self, choice):
        # Repack UI based on selection
        self.entry_person.pack_forget()
        self.sniper_target.pack_forget()
        self.btn_sniper.pack_forget()
        
        if choice != "Find CEO":
            self.entry_person.pack(side="left", padx=5)
        
        self.sniper_target.pack(side="left", padx=5)
        self.btn_sniper.pack(side="left", padx=5)

    def log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_box.insert("end", f"[{timestamp}] {msg}\n")
        self.log_box.see("end")

    def run_genesis(self):
        kw = self.entry_keyword.get()
        if not kw: self.log("⚠️ Enter a keyword first."); return
        threading.Thread(target=self.logic.execute_strategy, args=(None, "Find_Companies", self.log, kw), daemon=True).start()

    def run_sniper_scan(self):
        company = self.entry_company.get()
        domain = self.entry_domain.get()
        person = self.entry_person.get()
        target = self.sniper_target.get()
        
        if target == "Find CEO":
            if not company and not domain:
                self.log("⚠️ For 'Find CEO', you must provide a Company Name or Domain.")
                return
        else:
            if not person:
                self.log("⚠️ Person Name is required for this Sniper Mode.")
                return

        data = [{'Company Name': company, 'Website': domain, 'Decision Maker': person}]
        df = pd.DataFrame(data)
        
        self.log(f"🎯 Sniper Sequence: {person if person else 'Hunting CEO'} @ {company or 'Unknown'} -> {target}")
        threading.Thread(target=self.logic.execute_strategy, args=(df, "Sniper_Mode", self.log, None, target), daemon=True).start()

    def load_csv(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                self.logic.last_dataframe = pd.read_csv(file_path)
                self.log(f"✅ Loaded {len(self.logic.last_dataframe)} rows.")
            except Exception as e: self.log(f"❌ Error loading CSV: {e}")

    def run_enrichment_strategy(self):
        if self.logic.last_dataframe is None: self.log("⚠️ No data loaded."); return
        selection = self.strategy_var.get()
        
        # KEY MAPPING FOR THE NEW FEATURE
        strategy_map = {
            "Auto-Fill Missing Data": "Auto_Fill_Missing",
            "Find CEO": "Find_Decision_Maker", 
            "Find Email": "Find_Email", 
            "Find Company Name": "Find_Company_Name"
        }
        
        if selection == "Find CEO": internal_strat = "Sniper_Mode" 
        elif selection == "Auto-Fill Missing Data": internal_strat = "Auto_Fill_Missing"
        else: internal_strat = strategy_map.get(selection, "Find_Decision_Maker")
        
        threading.Thread(target=self.logic.execute_strategy, args=(self.logic.last_dataframe, internal_strat, self.log, None, "Find CEO" if selection == "Find CEO" else None), daemon=True).start()

    def stop_process(self):
        self.logic.request_stop()
        self.log("🛑 Stop Signal Sent.")

    def restart_app(self):
        self.logic.last_dataframe = None
        self.log_box.delete("1.0", "end")
        self.log("🔄 System Reset. Ready.")

    def export_csv(self):
        path = ctk.filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            success, msg = self.logic.export_data(path)
            self.log(msg)