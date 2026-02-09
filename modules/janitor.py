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

    def check_dns(self, domain):
        """Verifies if domain resolves (A record or MX record)."""
        if not domain: return False
        try:
            # Clean domain
            clean_dom = domain.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
            
            # Configure resolver with timeout (compatible way)
            resolver = dns.resolver.Resolver()
            resolver.timeout = 3
            resolver.lifetime = 3
            
            try:
                resolver.resolve(clean_dom, 'A')
                return True
            except:
                # Fallback to MX
                resolver.resolve(clean_dom, 'MX')
                return True
        except Exception as e:
            # print(f"DNS Error for {domain}: {e}") # Debug only
            return False

    def is_parked(self, url):
        """Checks for Parked/For Sale signatures."""
        if not url: return False
        try:
            if not url.startswith("http"): url = "https://" + url
            response = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            content = response.text.lower()
            
            signatures = [
                "domain is for sale", "buy this domain", "parked free", 
                "godaddy", "namecheap", "dan.com", "sedo", "afternic",
                "this domain is currently parked", "domain parking"
            ]
            
            if any(s in content for s in signatures):
                # Double check title
                title = re.search(r'<title>(.*?)</title>', content)
                if title and any(s in title.group(1).lower() for s in ["parked", "for sale", "available"]):
                    return True
                # Often parked pages have very little content
                if len(content) < 5000 and "buy" in content:
                    return True
                    
            return False
        except:
            return False # Treat unreachable as separate issue (DNS check handles this)

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
        self.chk_dns = ctk.CTkCheckBox(opts, text="DNS Resolution Check (Delete Dead)", variable=self.var_dns)
        self.chk_dns.pack(side="left", padx=10)

        self.var_parked = ctk.BooleanVar(value=True)
        self.chk_parked = ctk.CTkCheckBox(opts, text="Filter Parked Pages (GoDaddy/Sedo)", variable=self.var_parked)
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

        # 2. Iterative Checks (DNS & Parked)
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
                self.log("⚠️ No 'Website' column found for DNS checks.")
            else:
                total_now = len(self.df)
                processed = 0
                dead = 0
                parked = 0
                
                for idx, row in self.df.iterrows():
                    if self.logic.stop_requested: break
                    url = str(row[target_col])
                    if not url or url.lower() == "nan": continue
                    
                    is_valid = True
                    reason = ""
                    
                    # A. DNS Check
                    if self.var_dns.get():
                        if not self.logic.check_dns(url):
                            is_valid = False
                            dead += 1
                            reason = "DNS_DEAD"
                            self.log(f"   ❌ [DNS] {url} -> Unreachable")
                    
                    # B. Parked Check (Only if still valid)
                    if is_valid and self.var_parked.get():
                        if self.logic.is_parked(url):
                            is_valid = False
                            parked += 1
                            reason = "PARKED_PAGE"
                            self.log(f"   ⚠️ [PARKED] {url} -> For Sale/Parked")
                    
                    if is_valid:
                        valid_indices.append(idx)
                        self.df.at[idx, "Hygiene_Status"] = "Clean"
                    else:
                        self.df.at[idx, "Hygiene_Status"] = reason

                    processed += 1
                    if processed % 5 == 0:
                        self.log(f"   ⏳ Processed {processed}/{total_now}...")

                # Filter DataFrame
                self.df = self.df.loc[valid_indices].reset_index(drop=True)
                self.log(f"✅ Removed {dead} dead domains and {parked} parked pages.")

        self.btn_run.configure(state="normal")
        self.btn_export.configure(state="normal")
        self.log(f"🏁 Hygiene Complete. Final Count: {len(self.df)} rows.")

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            self.df.to_csv(path, index=False)
            self.log(f"💾 Saved clean list to {path}")