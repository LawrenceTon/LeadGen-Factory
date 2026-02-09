import customtkinter as ctk
import pandas as pd
import threading
import asyncio
import os
from tkinter import filedialog, messagebox
from playwright.async_api import async_playwright
from datetime import datetime
import unicodedata

# --- THE DEFAULT LAW BOOK (Management-Aligned) ---
class NameBrokerSOP:
    """
    Default SOP: Verification Logic.
    Used to AUDIT existing leads.
    """
    # 🔴 RED LIGHT: Reasons to REJECT a lead (Local/Small Biz)
    TOXIC_DEFAULTS = [
        "restaurant", "cafe", "bistro", "bakery", "catering", "menu", "table reservation",
        "nail", "salon", "spa", "massage", "grooming", "dog wash", "barber",
        "dentist", "dental", "clinic", "orthodontics", "chiropractor", 
        "plumbing", "repair", "hvac", "handyman", "cleaning service", "maid",
        "church", "parish", "preschool", "daycare", "local delivery", "curbside",
        "walk-ins welcome", "book appointment", "prices starting at", "family owned"
    ]

    # 🟢 GREEN LIGHT: Reasons to APPROVE a lead (Corporate/Scale)
    TARGET_DEFAULTS = [
        "investor relations", "global", "international", "careers", "press",
        "corporate", "sustainability", "innovation", "partners", "ventures",
        "group", "holdings", "limited", "inc", "offices", "worldwide",
        "leadership team", "board of directors", "solutions", "brands",
        "distributors", "wholesale", "media kit", "newsroom"
    ]

class JanitorModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.df = None
        self.file_path = None
        self.is_running = False
        
        self.setup_ui()

    def setup_ui(self):
        # --- 1. HEADER ---
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.header_frame, text="🧹 The Janitor: SOP Verification Center", 
                     font=("Arial", 18, "bold")).pack(side="left", padx=10)

        # --- 2. CONTROL PANEL ---
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Row 1: File & SOP Selection
        self.row1 = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.row1.pack(fill="x", padx=5, pady=5)

        self.btn_load = ctk.CTkButton(self.row1, text="📂 Load Target List", command=self.load_csv, width=150)
        self.btn_load.pack(side="left", padx=5)
        
        self.lbl_file = ctk.CTkLabel(self.row1, text="No file selected", text_color="gray")
        self.lbl_file.pack(side="left", padx=10)

        # SOP Dropdown
        self.sop_var = ctk.StringVar(value="NameBroker SOP (Strict)")
        self.combo_sop = ctk.CTkComboBox(self.row1, 
                                         values=["NameBroker SOP (Strict)", "Custom Verification Rules"],
                                         command=self.toggle_custom_inputs,
                                         variable=self.sop_var, width=250)
        self.combo_sop.pack(side="right", padx=5)
        ctk.CTkLabel(self.row1, text="Verification Criteria:").pack(side="right", padx=5)

        # Row 2: Custom Inputs (Hidden by default)
        self.custom_frame = ctk.CTkFrame(self.controls_frame)
        
        ctk.CTkLabel(self.custom_frame, text="🔴 Custom Rejection Keywords (Reject if found):", text_color="#FF5555").pack(anchor="w", padx=10, pady=(5,0))
        self.entry_toxic = ctk.CTkEntry(self.custom_frame, placeholder_text="e.g. 'out of business', 'landing page', 'error'")
        self.entry_toxic.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.custom_frame, text="🟢 Custom Approval Keywords (Approve if found):", text_color="#55FF55").pack(anchor="w", padx=10, pady=(5,0))
        self.entry_target = ctk.CTkEntry(self.custom_frame, placeholder_text="e.g. 'verified', 'contact us', 'headquarters'")
        self.entry_target.pack(fill="x", padx=10, pady=5)

        # Row 3: Action Buttons
        self.row3 = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.row3.pack(fill="x", padx=5, pady=10)

        self.btn_start = ctk.CTkButton(self.row3, text="▶️ Verify List Now", 
                                       command=self.start_audit_thread, state="disabled", 
                                       fg_color="#FF9800", font=("Arial", 14, "bold"), height=40)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_export = ctk.CTkButton(self.row3, text="💾 Export Verified List", 
                                        command=self.export_csv, state="disabled", 
                                        fg_color="green", height=40)
        self.btn_export.pack(side="right", padx=5)

        # --- 3. LOG CONSOLE ---
        self.log_box = ctk.CTkTextbox(self, height=400, font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.log("ℹ️ Ready. Load a CSV to begin Verification.")

    def toggle_custom_inputs(self, choice):
        if choice == "Custom Verification Rules":
            self.custom_frame.pack(fill="x", padx=10, pady=5, after=self.row1)
        else:
            self.custom_frame.pack_forget()

    def log(self, message):
        self.log_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_box.see("end")

    def _normalize_text(self, text):
        """
        Smart Transliteration for Nordic/German names (Antigravity Law #2).
        Converts 'Øvregaard' -> 'ovregaard'.
        """
        if not text: return ""
        
        # 1. Manual Transliteration Map
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

        # 2. Standard ASCII Normalization
        try:
            normalized = unicodedata.normalize('NFKD', cleaned).encode('ascii', 'ignore').decode('utf-8')
            return normalized.lower()
        except:
            return cleaned.lower()

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.file_path = file_path
            try:
                self.df = pd.read_csv(file_path)
                self.lbl_file.configure(text=os.path.basename(file_path), text_color="white")
                self.btn_start.configure(state="normal")
                self.log(f"✅ Loaded {len(self.df)} rows from {os.path.basename(file_path)}")
            except Exception as e:
                self.log(f"❌ Error loading CSV: {e}")

    def start_audit_thread(self):
        if not self.is_running:
            self.is_running = True
            self.btn_start.configure(text="⏳ Verifying...", state="disabled")
            self.btn_load.configure(state="disabled")
            threading.Thread(target=self.run_audit_process, daemon=True).start()

    def run_audit_process(self):
        asyncio.run(self.audit_logic())
        self.is_running = False
        self.btn_start.configure(text="▶️ Verify List Now", state="normal")
        self.btn_load.configure(state="normal")
        self.btn_export.configure(state="normal")
        self.log("🏁 Verification Complete. Please Export your data.")

    async def audit_logic(self):
        # 1. DETERMINE RULES
        if self.sop_var.get() == "Custom Verification Rules":
            self.log("🔧 Using CUSTOM Verification Rules...")
            toxic_list = [x.strip().lower() for x in self.entry_toxic.get().split(",") if x.strip()]
            target_list = [x.strip().lower() for x in self.entry_target.get().split(",") if x.strip()]
            if not toxic_list: toxic_list = NameBrokerSOP.TOXIC_DEFAULTS 
        else:
            self.log("📜 Using NAMEBROKER SOP (Strict)...")
            toxic_list = NameBrokerSOP.TOXIC_DEFAULTS
            target_list = NameBrokerSOP.TARGET_DEFAULTS

        # 2. IDENTIFY COLUMN
        target_col = None
        possible_cols = ["Website", "Domain", "URL", "Company Website", "Official Website"]
        for col in possible_cols:
            if col in self.df.columns:
                target_col = col
                break
        
        if not target_col:
            self.log("❌ Error: Could not find 'Website' or 'Domain' column.")
            return

        # 3. PREPARE COLUMNS (SOP_Status & SOP_Reason)
        if "SOP_Status" not in self.df.columns: self.df["SOP_Status"] = ""
        if "SOP_Reason" not in self.df.columns: self.df["SOP_Reason"] = ""

        # 4. START BROWSER
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            total = len(self.df)
            self.log(f"🚀 Verifying {total} domains...")

            for index, row in self.df.iterrows():
                # Skip already checked
                if pd.notna(row.get("SOP_Status")) and str(row["SOP_Status"]).strip() != "":
                    continue

                raw_url = str(row[target_col])
                if not raw_url or raw_url.lower() == "nan": 
                    continue

                if not raw_url.startswith("http"):
                    url = "https://" + raw_url
                else:
                    url = raw_url

                self.log(f"[{index+1}/{total}] 🔍 Checking: {url}")
                
                try:
                    # A. VISIT
                    await page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    
                    # B. WAIT (Critical Verification Step)
                    await asyncio.sleep(3.0) 
                    
                    # C. READ
                    page_title = await page.title()
                    try:
                        # CRITICAL FIX: The 'await' command is here!
                        body_text = await page.locator("body").inner_text()
                    except:
                        body_text = ""
                    
                    # NORMALIZE CONTENT (Law #2: Nordic Transformation)
                    raw_content = page_title + " " + body_text
                    full_content = self._normalize_text(raw_content)[:15000]

                    # D. JUDGE (Verify)
                    status = "APPROVED"
                    reason = "Clean / Verified"

                    # 1. Check Rejection Criteria
                    for poison in toxic_list:
                        if poison in full_content:
                            status = "REJECTED"
                            reason = f"Verification Failed: Found '{poison}'"
                            break
                    
                    # 2. Check Approval Signals (If not rejected)
                    if status == "APPROVED":
                        for gold in target_list:
                            if gold in full_content:
                                reason = f"Strong Verification: Found '{gold}'"
                                break

                    self.log(f"   👉 {status}: {reason}")
                    
                    # E. SAVE
                    self.df.at[index, "SOP_Status"] = status
                    self.df.at[index, "SOP_Reason"] = reason

                except Exception as e:
                    self.log(f"   ⚠️ Unreachable: {e}")
                    self.df.at[index, "SOP_Status"] = "FLAGGED"
                    self.df.at[index, "SOP_Reason"] = "Site Unreachable / DNS Error"

            await browser.close()

    def export_csv(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if save_path:
            self.df.to_csv(save_path, index=False)
            self.log(f"💾 Saved Verified List to: {save_path}")