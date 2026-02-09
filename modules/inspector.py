import customtkinter as ctk
import pandas as pd
import threading
import asyncio
import os
import requests
import hashlib
import dns.resolver
from datetime import datetime

class InspectorLogic:
    def __init__(self):
        self.last_dataframe = None
        self.stop_requested = False

    def request_stop(self):
        self.stop_requested = True

    # --- 1. SAFE DNS CHECK (The "Map" Check) ---
    def verify_email_dns(self, email):
        """
        Checks if the domain exists and is configured to receive email.
        Uses Google DNS (8.8.8.8) to bypass local ISP issues.
        Risk Level: ZERO (Standard Internet Traffic)
        """
        if "@" not in email:
            return "Invalid", "❌ Format Error"

        try:
            domain = email.split('@')[1]
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['8.8.8.8', '8.8.4.4'] 
            resolver.timeout = 3.0
            resolver.lifetime = 3.0

            try:
                mx_records = resolver.resolve(domain, 'MX')
                return "Valid Domain", f"✅ Domain Active (MX Found)"
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                return "Invalid Domain", f"❌ Domain Invalid (No MX)"
            except:
                return "Error", "⚠️ DNS Timeout"
        except:
            return "Error", "⚠️ Parse Error"

    # --- 2. SOCIAL CHECK (The "Human" Check) ---
    def check_gravatar(self, email):
        """
        Checks if the email has a public Gravatar profile image.
        Risk Level: ZERO (Standard Web Request)
        """
        try:
            # 1. Clean and Hash the email (MD5)
            clean_email = email.strip().lower()
            email_hash = hashlib.md5(clean_email.encode('utf-8')).hexdigest()
            
            # 2. Check Gravatar API
            # d=404 tells Gravatar to return a 404 error if no image exists
            url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                return True
            return False
        except:
            return False

    # --- MAIN EXECUTION SWITCH ---
    def execute_task(self, input_data, task_type, manual_input, log_callback):
        self.stop_requested = False
        
        # MODE 1: EMAIL VERIFICATION
        if task_type == "Verify Email":
            if not manual_input:
                log_callback("⚠️ No emails entered.")
                return
            
            email_list = [e.strip() for e in manual_input.split(',') if e.strip()]
            log_callback(f"🚀 Verifying {len(email_list)} emails (Safe Mode)...")
            
            results = []
            for email in email_list:
                if self.stop_requested: break
                
                log_callback(f"   🔎 Checking: {email}...")
                
                # Step 1: Check Domain (DNS)
                dns_status, dns_msg = self.verify_email_dns(email)
                
                # Step 2: Check Social (Gravatar)
                # We check this even if DNS fails, just in case of weird server setups
                has_profile = self.check_gravatar(email)
                
                # Final Status Logic
                final_status = dns_status
                final_msg = dns_msg
                
                if has_profile:
                    final_status = "✅ Verified User"
                    final_msg = "✅ VALID: Social Profile Found (Real Human)"
                    log_callback(f"      📸 SOCIAL HIT: Found Profile Picture!")
                elif "Valid" in dns_status:
                    final_status = "⚠️ Valid Domain"
                    final_msg = "✅ Domain OK (User Unverified)"
                    log_callback(f"      {final_msg}")
                else:
                    log_callback(f"      {final_msg}")

                results.append({
                    "Input": email, 
                    "Type": "Email", 
                    "Status": final_status, 
                    "Details": final_msg,
                    "Has Profile": "Yes" if has_profile else "No"
                })
            
            self.last_dataframe = pd.DataFrame(results)
            log_callback(f"✅ Safe Verification Complete.")

        # MODE 2: DOMAIN ANALYSIS
        elif task_type == "Analyze Domain":
            if not manual_input:
                log_callback("⚠️ No domain entered.")
                return

            domain_list = [d.strip() for d in manual_input.split(',') if d.strip()]
            log_callback(f"🚀 Analyzing {len(domain_list)} domains...")
            
            results = []
            for dom in domain_list:
                if self.stop_requested: break
                # Treat domain as email check for MX logic
                test_email = f"test@{dom.replace('https://','').replace('http://','').split('/')[0]}"
                
                log_callback(f"   🌐 Scanning: {dom}...")
                status, msg = self.verify_email_dns(test_email)
                
                if "Valid" in status:
                    final_status = "Healthy"
                    final_msg = "✅ MX Records Active"
                else:
                    final_status = "Unhealthy"
                    final_msg = msg

                log_callback(f"      {final_status}: {final_msg}")
                results.append({"Input": dom, "Type": "Domain", "Status": final_status, "Details": final_msg})
            
            self.last_dataframe = pd.DataFrame(results)
            log_callback(f"✅ Domain Analysis Complete.")

        # MODE 3: CSV AUDIT
        elif task_type == "Audit CSV (Vision)":
            log_callback("ℹ️ Vision Audit: Please load a CSV first.")

    def export_data(self, filename):
        if self.last_dataframe is not None:
            self.last_dataframe.to_csv(filename, index=False)
            return True, "Saved."
        return False, "No data."

# --- UI MODULE ---
class InspectorModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.logic = InspectorLogic()
        self.setup_ui()

    def setup_ui(self):
        head = ctk.CTkFrame(self)
        head.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(head, text="🕵️ The Inspector: Safe Verification", font=("Arial", 18, "bold")).pack(side="left", padx=10)

        # INPUT ROW
        row_input = ctk.CTkFrame(self)
        row_input.pack(fill="x", padx=10, pady=5)
        
        self.btn_load = ctk.CTkButton(row_input, text="📂 Load CSV", command=self.load_csv, fg_color="#1F6AA5", width=100)
        self.btn_load.pack(side="left", padx=5)
        
        self.lbl_file = ctk.CTkLabel(row_input, text="No file selected", text_color="gray")
        self.lbl_file.pack(side="left", padx=5)

        # DYNAMIC MANUAL BOX
        row_manual = ctk.CTkFrame(self)
        row_manual.pack(fill="x", padx=10, pady=5)
        
        self.lbl_manual = ctk.CTkLabel(row_manual, text="Enter Emails (comma separated):")
        self.lbl_manual.pack(side="left", padx=5)
        
        self.entry_manual = ctk.CTkEntry(row_manual, placeholder_text="ceo@test.com, info@domain.com...", width=400)
        self.entry_manual.pack(side="left", padx=5, fill="x", expand=True)

        # CONTROLS ROW
        row_ctrl = ctk.CTkFrame(self)
        row_ctrl.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(row_ctrl, text="Task:").pack(side="left", padx=5)
        
        self.task_var = ctk.StringVar(value="Verify Email")
        self.combo_task = ctk.CTkComboBox(
            row_ctrl, 
            values=["Verify Email", "Analyze Domain", "Audit CSV (Vision)"], 
            variable=self.task_var, 
            width=180,
            command=self.update_ui_state
        )
        self.combo_task.pack(side="left", padx=5)

        self.btn_start = ctk.CTkButton(row_ctrl, text="▶️ Run Inspector", command=self.run_process, fg_color="#FF9800")
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = ctk.CTkButton(row_ctrl, text="🛑 Stop", command=self.stop_process, fg_color="red", width=80)
        self.btn_stop.pack(side="left", padx=5)
        
        self.btn_export = ctk.CTkButton(row_ctrl, text="💾 Export", command=self.export_csv, fg_color="green", width=80)
        self.btn_export.pack(side="right", padx=10)

        # LOG BOX
        self.log_box = ctk.CTkTextbox(self, height=350, font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

    def update_ui_state(self, choice):
        if choice == "Verify Email":
            self.lbl_manual.configure(text="Enter Emails (comma separated):")
            self.entry_manual.configure(placeholder_text="ceo@test.com, info@domain.com...")
            self.entry_manual.configure(state="normal")
        elif choice == "Analyze Domain":
            self.lbl_manual.configure(text="Enter Domains (comma separated):")
            self.entry_manual.configure(placeholder_text="ideadex.me, google.com...")
            self.entry_manual.configure(state="normal")
        elif choice == "Audit CSV (Vision)":
            self.lbl_manual.configure(text="Manual Input Disabled:")
            self.entry_manual.configure(placeholder_text="(Load a CSV file to audit)")
            self.entry_manual.configure(state="disabled")

    def log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_box.insert("end", f"[{timestamp}] {msg}\n")
        self.log_box.see("end")

    def load_csv(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                self.logic.last_dataframe = pd.read_csv(file_path)
                self.lbl_file.configure(text=os.path.basename(file_path), text_color="white")
                self.log(f"✅ Loaded {len(self.logic.last_dataframe)} rows.")
            except Exception as e: self.log(f"❌ Error: {e}")

    def run_process(self):
        task = self.task_var.get()
        manual_data = self.entry_manual.get()
        threading.Thread(target=self.logic.execute_task, args=(self.logic.last_dataframe, task, manual_data, self.log), daemon=True).start()

    def stop_process(self):
        self.logic.request_stop()
        self.log("🛑 Stop Signal Sent.")

    def export_csv(self):
        path = ctk.filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            success, msg = self.logic.export_data(path)
            self.log(msg)