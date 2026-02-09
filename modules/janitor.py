import customtkinter as ctk
import pandas as pd
import threading
import asyncio
import os
import dns.resolver
import requests
import re
from tkinter import filedialog, messagebox
from datetime import datetime
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from modules.utils_browser import launch_browser, setup_stealth

class JanitorLogic:
    def __init__(self):
        self.stop_requested = False
        self.df = None

    def request_stop(self):
        self.stop_requested = True

    def remove_duplicates(self, df):
        """Deduplicates by Domain and Email."""
        initial_count = len(df)
        
        # 1. Normalize Domains
        if "Website" in df.columns:
            df["_norm_domain"] = df["Website"].apply(lambda x: str(x).lower().strip().replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0] if pd.notna(x) else "")
            df = df.drop_duplicates(subset=["_norm_domain"], keep="first")
            df = df.drop(columns=["_norm_domain"])
        
        # 2. Normalize Emails
        if "Email" in df.columns:
            df = df.drop_duplicates(subset=["Email"], keep="first")

        removed = initial_count - len(df)
        return df, removed

    async def verify_domain_browser(self, page, url, log_callback):
        """
        Physically opens the domain in the browser, waits for render, 
        and checks for 'Seller' fingerprints.
        """
        if not url: return False, "MISSING_URL"
        if not url.startswith("http"): url = "https://" + url
        
        try:
            log_callback(f"   👁️ Rendering: {url}")
            # 1. Physical Navigation
            # We use a generous timeout because redirects/render can be slow
            response = await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            
            # 2. Patience Protocol: Mandatory 5s wait for redirects/rendering
            await asyncio.sleep(5)
            
            # Re-check URL after possible redirects
            final_url = page.url.lower()
            title = (await page.title()).lower()
            body_text = (await page.locator("body").inner_text()).lower()
            
            # 3. Expanded Blacklist (Seller Fingerprints)
            seller_fingerprints = [
                "domain is for sale", "buy this domain", "parked free", 
                "godaddy", "namecheap", "dan.com", "sedo", "afternic",
                "this domain is currently parked", "domain parking",
                "huge domains", "hugedomains", "domaineasy", "atom.com",
                "premium domain", "inquire about this domain",
                "domain names for sale", "make an offer"
            ]
            
            # Check for matches in Title or Body
            for fingerprint in seller_fingerprints:
                if fingerprint in title or fingerprint in body_text:
                    log_callback(f"   ⚠️ [REJECTED] Seller Fingerprint: '{fingerprint}'")
                    return False, "SELLER_PARKED"
            
            # 4. Check for 'Empty' or 'Broken' pages
            if len(body_text) < 300 and ("403" in title or "404" in title or "error" in title):
                log_callback(f"   ❌ [REJECTED] Dead/Error Page Detected.")
                return False, "DEAD_OR_ERROR"

            return True, "CLEAN"

        except Exception as e:
            log_callback(f"   ❌ [REJECTED] Unreachable: {e}")
            return False, "UNREACHABLE"

class JanitorModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.logic = JanitorLogic()
        self.df = None
        self.setup_ui()

    def setup_ui(self):
        # Header
        head = ctk.CTkFrame(self)
        head.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(head, text="🧹 The Janitor: Validation Interface", font=("Arial", 18, "bold")).pack(side="left", padx=10)

        # Control Panel
        controls = ctk.CTkFrame(self)
        controls.pack(fill="x", padx=10, pady=5)

        # File Load
        self.btn_load = ctk.CTkButton(controls, text="📂 Load List", command=self.load_csv, width=120)
        self.btn_load.pack(side="left", padx=5, pady=10)
        self.lbl_file = ctk.CTkLabel(controls, text="No file loaded", text_color="gray")
        self.lbl_file.pack(side="left", padx=10)

        # Hygiene Options
        opts = ctk.CTkFrame(self)
        opts.pack(fill="x", padx=10, pady=5)
        
        self.var_dedupe = ctk.BooleanVar(value=True)
        self.chk_dedupe = ctk.CTkCheckBox(opts, text="Remove Duplicates", variable=self.var_dedupe)
        self.chk_dedupe.pack(side="left", padx=10, pady=5)

        self.var_dns = ctk.BooleanVar(value=True)
        self.chk_dns = ctk.CTkCheckBox(opts, text="Browser-First Verification (Render & Scan)", variable=self.var_dns)
        self.chk_dns.pack(side="left", padx=10)

        self.var_parked = ctk.BooleanVar(value=True)
        self.chk_parked = ctk.CTkCheckBox(opts, text="Filter Seller Blacklist (Atom/Dan/Sedo)", variable=self.var_parked)
        self.chk_parked.pack(side="left", padx=10)

        # Action Buttons
        actions = ctk.CTkFrame(self)
        actions.pack(fill="x", padx=10, pady=10)

        self.btn_run = ctk.CTkButton(actions, text="▶️ CLEAN LIST", command=self.start_process, 
                                     fg_color="green", font=("Arial", 14, "bold"), height=40, state="disabled")
        self.btn_run.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_stop = ctk.CTkButton(actions, text="🛑 STOP", command=self.stop_process, 
                                      fg_color="red", height=40, width=100)
        self.btn_stop.pack(side="right", padx=5)

        self.btn_export = ctk.CTkButton(actions, text="💾 Export Clean", command=self.export_csv, 
                                        fg_color="#1F6AA5", height=40, state="disabled")
        self.btn_export.pack(side="right", padx=5)

        # Log
        self.log_box = ctk.CTkTextbox(self, height=400, font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.log("ℹ️ Ready. Load a CSV to begin Hygiene Protocols.")

    def log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_box.insert("end", f"[{timestamp}] {msg}\n")
        self.log_box.see("end")

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            try:
                self.df = pd.read_csv(path)
                self.lbl_file.configure(text=os.path.basename(path), text_color="white")
                self.btn_run.configure(state="normal")
                self.log(f"✅ Loaded {len(self.df)} rows.")
            except Exception as e:
                self.log(f"❌ Error loading: {e}")

    def start_process(self):
        if self.df is None: return
        self.logic.stop_requested = False
        threading.Thread(target=self.run_process, daemon=True).start()

    def stop_process(self):
        self.logic.request_stop()
        self.log("🛑 Stop requested...")

    def run_process(self):
        asyncio.run(self.run_process_async())

    async def run_process_async(self):
        total = len(self.df)
        self.log(f"🚀 Starting Hygiene on {total} rows...")
        self.btn_run.configure(state="disabled")
        self.btn_export.configure(state="disabled")

        # 1. Deduplication
        if self.var_dedupe.get():
            self.log("DATA HYGIENE: Checking duplicates...")
            self.df, removed = self.logic.remove_duplicates(self.df)
            self.log(f"   🗑️ Removed {removed} duplicates.")
        
        if self.logic.stop_requested: return

        # 2. Iterative Checks (Browser-First Rendering)
        if self.var_dns.get() or self.var_parked.get():
            valid_indices = []
            
            # Find target column
            target_col = None
            cols = ["Website", "Domain", "URL"]
            for c in cols:
                if c in self.df.columns:
                    target_col = c
                    break
            
            if not target_col:
                self.log("⚠️ No 'Website' column found for checks.")
            else:
                total_now = len(self.df)
                processed = 0
                rejected = 0
                
                async with async_playwright() as p:
                    # Launch browser once for the whole run
                    playwright, browser, context, page = await launch_browser(headless=False, playwright_instance=p)
                    await setup_stealth(page)
                    
                    for idx, row in self.df.iterrows():
                        if self.logic.stop_requested: break
                        url = str(row[target_col])
                        if not url or url.lower() == "nan": continue
                        
                        # Physical Verification
                        is_valid, reason = await self.logic.verify_domain_browser(page, url, self.log)
                        
                        if is_valid:
                            valid_indices.append(idx)
                            self.df.at[idx, "Hygiene_Status"] = "Clean"
                        else:
                            rejected += 1
                            self.df.at[idx, "Hygiene_Status"] = reason
                        
                        processed += 1
                        if processed % 5 == 0:
                            self.log(f"   ⏳ Processed {processed}/{total_now}...")

                    try: await browser.close()
                    except: pass

                # Filter DataFrame
                self.df = self.df.loc[valid_indices].reset_index(drop=True)
                self.log(f"✅ Processed {processed} domains. Rejected {rejected} total (Dead/Seller/Broken).")

        self.btn_run.configure(state="normal")
        self.btn_export.configure(state="normal")
        self.log(f"🏁 Hygiene Complete. Final Count: {len(self.df)} rows.")

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            self.df.to_csv(path, index=False)
            self.log(f"💾 Saved clean list to {path}")