import customtkinter as ctk
import threading
import os
import pandas as pd
from tkinter import filedialog
from modules.architect import ArchitectLogic
from modules.harvester import HarvesterLogic
from modules.inspector import InspectorLogic
# Placeholder for Janitor
# from modules.janitor import JanitorLogic 
from modules.tooltip import ToolTip

class JanitorView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(self, text="Janitor Module (Coming Soon)", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_title.pack(pady=40)
        
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(pady=20, padx=20, fill="x")
        
        self.chk_duplicates = ctk.CTkCheckBox(self.options_frame, text="Remove Duplicates")
        self.chk_duplicates.pack(side="left", padx=20, pady=20)
        ToolTip(self.chk_duplicates, "Identify and remove duplicate rows based on URL or Email.")

        self.chk_split = ctk.CTkCheckBox(self.options_frame, text="Split Names")
        self.chk_split.pack(side="left", padx=20, pady=20)
        ToolTip(self.chk_split, "Split 'Full Name' into 'First Name' and 'Last Name' columns.")
        
        self.btn_clean = ctk.CTkButton(self, text="Clean Data 🧹", state="disabled")
        self.btn_clean.pack(pady=20)
        ToolTip(self.btn_clean, "Execute the cleaning process (Not yet implemented).")

class ArchitectView(ctk.CTkFrame):
    def __init__(self, master, logic):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.logic = logic
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Architect Module", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(side="left")

        self.name_entry = ctk.CTkEntry(self.header_frame, placeholder_text="Recipe Name (e.g., Lead Gen - Tech)", width=300)
        self.name_entry.pack(side="right")
        ToolTip(self.name_entry, "Name your scraping strategy.")

        # Controls
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.lbl_col_name = ctk.CTkLabel(self.controls_frame, text="New Column:")
        self.lbl_col_name.pack(side="left", padx=10, pady=10)
        
        self.col_name_entry = ctk.CTkEntry(self.controls_frame, placeholder_text="Column Name")
        self.col_name_entry.pack(side="left", padx=5, pady=10)
        
        self.col_key_entry = ctk.CTkEntry(self.controls_frame, placeholder_text="Keywords", width=200)
        self.col_key_entry.pack(side="left", padx=5, pady=10)
        
        self.btn_add_col = ctk.CTkButton(self.controls_frame, text="Add Column", command=self.add_column)
        self.btn_add_col.pack(side="left", padx=10, pady=10)

        # List
        self.columns_scroll = ctk.CTkScrollableFrame(self, label_text="Target Columns")
        self.columns_scroll.grid(row=2, column=0, sticky="nsew")
        self.column_items = []

        # Footer
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=3, column=0, sticky="ew", pady=20)

        self.status_label = ctk.CTkLabel(self.footer_frame, text="", text_color="green")
        self.status_label.pack(side="left")
        
        self.btn_save = ctk.CTkButton(self.footer_frame, text="Save Recipe", command=self.save_recipe, fg_color="green")
        self.btn_save.pack(side="right")

    def add_column(self):
        col_name = self.col_name_entry.get()
        keywords = self.col_key_entry.get()
        if not col_name: return

        row_frame = ctk.CTkFrame(self.columns_scroll)
        row_frame.pack(fill="x", pady=2)
        
        lbl = ctk.CTkLabel(row_frame, text=f"{col_name} : {keywords}", anchor="w")
        lbl.pack(side="left", padx=10, pady=5)
        
        self.column_items.append({"col_name": col_name, "keywords": keywords})
        self.col_name_entry.delete(0, "end")
        self.col_key_entry.delete(0, "end")

    def save_recipe(self):
        name = self.name_entry.get()
        if not name or not self.column_items: return
        if self.logic.save_recipe(name, self.column_items):
            self.status_label.configure(text="Recipe Saved Successfully!", text_color="green")
        else:
            self.status_label.configure(text="Error saving recipe.", text_color="red")

class HarvesterView(ctk.CTkFrame):
    def __init__(self, master, logic):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.logic = logic
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Top Bar
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.lbl_recipe = ctk.CTkLabel(self.top_frame, text="Select Recipe:", font=ctk.CTkFont(weight="bold"))
        self.lbl_recipe.pack(side="left", padx=(0, 10))

        self.recipe_options = self.logic.get_recipe_names() or ["No Recipes Found"]
        self.option_recipe = ctk.CTkOptionMenu(self.top_frame, values=self.recipe_options)
        self.option_recipe.pack(side="left")
        
        self.chk_human = ctk.CTkCheckBox(self.top_frame, text="Human Mode (Show Browser)")
        self.chk_human.pack(side="left", padx=20)

        # URL Input
        self.lbl_urls = ctk.CTkLabel(self, text="Target URLs (One per line):", anchor="w")
        self.lbl_urls.grid(row=0, column=0, sticky="sw", pady=(40, 0))

        self.txt_urls = ctk.CTkTextbox(self, height=150)
        self.txt_urls.grid(row=1, column=0, sticky="nsew", pady=(5, 10))
        self.txt_urls.insert("0.0", "https://example.com\n")

        # Action
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, sticky="ew", pady=10)

        self.btn_start = ctk.CTkButton(self.action_frame, text="Start Harvest 🚜", command=self.start_harvest_thread, height=40, font=ctk.CTkFont(size=16, weight="bold"))
        self.btn_start.pack(fill="x")

        # Console
        self.lbl_console = ctk.CTkLabel(self, text="Harvest Log:", anchor="w")
        self.lbl_console.grid(row=3, column=0, sticky="nw", pady=(10, 0))

        self.txt_console = ctk.CTkTextbox(self, state="disabled")
        self.txt_console.grid(row=4, column=0, sticky="nsew", pady=(5, 0))

    def refresh_recipes(self):
        recipes = self.logic.get_recipe_names()
        if recipes:
            self.option_recipe.configure(values=recipes)
            self.option_recipe.set(recipes[0])

    def log_message(self, msg):
        self.txt_console.configure(state="normal")
        self.txt_console.insert("end", f"{msg}\n")
        self.txt_console.see("end")
        self.txt_console.configure(state="disabled")

    def start_harvest_thread(self):
        recipe_name = self.option_recipe.get()
        urls = [u for u in self.txt_urls.get("0.0", "end").split("\n") if u.strip()]
        if not urls or recipe_name == "No Recipes Found": return
        
        self.btn_start.configure(state="disabled", text="Harvesting...")
        t = threading.Thread(target=self.logic.perform_harvest, args=(urls, recipe_name, self.log_message, bool(self.chk_human.get())))
        t.start()
        # Note: logic.perform_harvest will re-enable button manually or via callback wrapper? 
        # Actually logic doesn't re-enable. Let's fix button state in a callback wrapper if needed.
        # For now, simplistic. In production, callback should handle state.
        # But HarvesterLogic is synchronous in the thread. 
        self.monitor_harvest_thread(t)

    def monitor_harvest_thread(self, thread):
        if thread.is_alive():
            self.after(500, lambda: self.monitor_harvest_thread(thread))
        else:
            self.btn_start.configure(state="normal", text="Start Harvest 🚜")

class InspectorView(ctk.CTkFrame):
    def __init__(self, master, logic):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.logic = logic
        self.csv_path = None
        self.is_running_ui = False
        
        self.active_rules = []
        self.rule_history = []
        self.redo_stack = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(8, weight=1)

        # 0. API
        self.step1_lbl = ctk.CTkLabel(self, text="Step 1: Connect AI Brain", font=ctk.CTkFont(weight="bold"))
        self.step1_lbl.grid(row=0, column=0, sticky="w", pady=(10, 5))
        self.api_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.api_frame.grid(row=1, column=0, sticky="ew")
        
        self.entry_primary = ctk.CTkEntry(self.api_frame, placeholder_text="Primary API Key", width=200, show="*")
        self.entry_primary.pack(side="left", padx=5)
        self.entry_backup = ctk.CTkEntry(self.api_frame, placeholder_text="Backup Key (Optional)", width=200, show="*")
        self.entry_backup.pack(side="left", padx=5)

        # 1. File
        self.step2_lbl = ctk.CTkLabel(self, text="Step 2: Upload Targets", font=ctk.CTkFont(weight="bold"))
        self.step2_lbl.grid(row=2, column=0, sticky="w", pady=(10, 5))
        self.file_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.file_frame.grid(row=3, column=0, sticky="ew")
        
        self.btn_select = ctk.CTkButton(self.file_frame, text="Select CSV", command=self.select_file)
        self.btn_select.pack(side="left")
        self.lbl_file = ctk.CTkLabel(self.file_frame, text="No file selected")
        self.lbl_file.pack(side="left", padx=10)

        # 2. Rules
        self.step3_lbl = ctk.CTkLabel(self, text="Step 3: Build Logic (Smart Wizard)", font=ctk.CTkFont(weight="bold"))
        self.step3_lbl.grid(row=4, column=0, sticky="w", pady=(10, 5))
        
        self.rule_frame = ctk.CTkFrame(self)
        self.rule_frame.grid(row=5, column=0, sticky="ew")
        
        self.rule_types = ['Check Status', 'Contains Keyword', 'Extract Price', 'AI Analysis']
        self.option_rule = ctk.CTkOptionMenu(self.rule_frame, values=self.rule_types, command=self.toggle_input)
        self.option_rule.pack(side="left", padx=10, pady=10)
        
        self.rule_input = ctk.CTkEntry(self.rule_frame, placeholder_text="Config")
        # Hidden initially
        
        self.btn_add = ctk.CTkButton(self.rule_frame, text="+ Add", width=60, command=self.add_rule)
        self.btn_add.pack(side="left", padx=5)

        self.btn_wizard = ctk.CTkButton(self.rule_frame, text="✨ Smart Wizard", command=self.run_smart_wizard, fg_color="#7B32A8")
        self.btn_wizard.pack(side="left", padx=20)
        
        # 3. Stack & Limits
        self.mid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.mid_frame.grid(row=7, column=0, sticky="nsew", pady=10)
        self.mid_frame.grid_columnconfigure(1, weight=1)

        # Limits Left
        self.limits_frame = ctk.CTkFrame(self.mid_frame)
        self.limits_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        self.limit_rows = ctk.CTkEntry(self.limits_frame, placeholder_text="Limit Rows")
        self.limit_rows.pack(pady=5, padx=5)
        self.limit_mins = ctk.CTkEntry(self.limits_frame, placeholder_text="Limit Mins")
        self.limit_mins.pack(pady=5, padx=5)
        
        self.btn_export = ctk.CTkButton(self.limits_frame, text="Export History", command=self.export_history, fg_color="#3B8ED0")
        self.btn_export.pack(pady=20, padx=5)

        # Rules Right
        self.rules_frame = ctk.CTkFrame(self.mid_frame, fg_color="transparent")
        self.rules_frame.grid(row=0, column=1, sticky="nsew")
        
        self.edit_frame = ctk.CTkFrame(self.rules_frame, height=30, fg_color="transparent")
        self.edit_frame.pack(fill="x")
        self.btn_undo = ctk.CTkButton(self.edit_frame, text="Undo", width=60, command=self.undo_action, state="disabled")
        self.btn_undo.pack(side="left", padx=2)
        self.btn_redo = ctk.CTkButton(self.edit_frame, text="Redo", width=60, command=self.redo_action, state="disabled")
        self.btn_redo.pack(side="left", padx=2)
        
        self.rules_scroll = ctk.CTkScrollableFrame(self.rules_frame, label_text="Active Rules Stack")
        self.rules_scroll.pack(fill="both", expand=True)

        # 4. Control Center
        self.create_control_panel()

        # Log
        self.txt_log = ctk.CTkTextbox(self, height=100, fg_color="black", text_color="#00ff00")
        self.txt_log.grid(row=9, column=0, sticky="nsew")

    def create_control_panel(self):
        self.control_panel_frame = ctk.CTkFrame(self, border_color="gray", border_width=2)
        self.control_panel_frame.grid(row=8, column=0, sticky="ew", pady=10)
        # Assuming the instruction implies using pack *inside* a container or just packing the frame itself if it wasn't grid?
        # The prompt says: "Create a CTkFrame named self.control_panel_frame. Pack it: fill="x", pady=10, padx=10"
        # However, the outer structure uses grid(). I should probably stick to grid() for the frame placement to avoid geometry manager conflict 
        # with siblings, OR check if I can switch to pack. siblings use grid. So I must use grid for self.control_panel_frame.
        # BUT the prompt explicitly says "Pack it". 
        # Let's look at __init__ layout strategy. It uses grid for everything (row 0 to 9). 
        # If I use pack() for the frame, it will conflict with grid(). 
        # I will use grid() but name it self.control_panel_frame and follow internal packing instructions.
        # Wait, if I change the logic to call this method, I can't easily change the geometry manager of the whole class.
        # I will use grid for the frame, but use pack for the contents as requested.
        
        # Actually, looking at the previous step, I used grid for the frame. 
        # I will stick to grid for the frame placement in the parent, but use the specific button layout requested.
        
        # Status/Progress Section (Preserving this as it ensures UI completeness though not explicitly detailed in this specific prompt, 
        # but likely needed). The prompt only details the BUTTONS.
        # I'll include the status frame above or aside? Prompt says "Button 1... Position: ... centered".
        # I will add the buttons as requested.
        
        self.status_frame = ctk.CTkFrame(self.control_panel_frame, fg_color="transparent")
        self.status_frame.pack(fill="x", padx=5, pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        self.progress_bar.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Status: Ready")
        self.lbl_status.pack(side="left", padx=5)

        self.btn_start = ctk.CTkButton(self.control_panel_frame, text="▶ START AUDIT", command=self.start_audit_thread, 
                                       fg_color="#2ecc71", width=140)
        self.btn_start.pack(side="left", padx=5, expand=True)
        
        self.btn_pause = ctk.CTkButton(self.control_panel_frame, text="⏸ PAUSE", command=self.toggle_pause, 
                                       fg_color="#f1c40f", width=100)
        self.btn_pause.pack(side="left", padx=5, expand=True)
        
        self.btn_stop = ctk.CTkButton(self.control_panel_frame, text="⏹ STOP", command=self.stop_audit, 
                                      fg_color="#e74c3c", width=100)
        self.btn_stop.pack(side="left", padx=5, expand=True)

    def select_file(self):
        f = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if f:
            self.csv_path = f
            self.lbl_file.configure(text=os.path.basename(f))

    def toggle_input(self, choice):
        self.rule_input.pack_forget()
        if choice in ['Contains Keyword', 'AI Analysis']:
            self.rule_input.pack(side="left", padx=5)

    def refresh_rule_list(self):
        for w in self.rules_scroll.winfo_children(): w.destroy()
        
        for idx, rule in enumerate(self.active_rules):
            f = ctk.CTkFrame(self.rules_scroll)
            f.pack(fill="x", pady=2)
            
            txt = f"{rule['type']} [UA: {rule.get('user_agent', 'Chrome')}] -> {rule.get('target_column', 'Auto')}"
            if rule.get('prompt'): txt += f" | Prompt: {rule['prompt'][:15]}..."
            elif rule.get('value'): txt += f" | Val: {rule['value']}"
            
            ctk.CTkLabel(f, text=txt).pack(side="left", padx=10)
            ctk.CTkButton(f, text="X", width=30, fg_color="red", command=lambda i=idx: self.delete_rule(i)).pack(side="right", padx=5)
            
        self.btn_undo.configure(state="normal" if self.rule_history else "disabled")
        self.btn_redo.configure(state="normal" if self.redo_stack else "disabled")

    def add_rule(self):
        # Manual Add
        r_type = self.option_rule.get()
        new_rule = {'user_agent': 'Chrome'} # Default check
        
        if r_type == 'Check Status':
            new_rule['type'] = 'status_check'
        elif r_type == 'Contains Keyword':
            val = self.rule_input.get()
            if not val: return
            new_rule['type'] = 'keyword'; new_rule['value'] = val
        elif r_type == 'Extract Price':
            new_rule['type'] = 'extract_price'
        elif r_type == 'AI Analysis':
            val = self.rule_input.get()
            if not val: return
            new_rule['type'] = 'ai_analysis'; new_rule['prompt'] = val

        self.rule_history.append(list(self.active_rules))
        self.redo_stack.clear()
        self.active_rules.append(new_rule)
        self.refresh_rule_list()

    def delete_rule(self, idx):
        self.rule_history.append(list(self.active_rules))
        self.redo_stack.clear()
        del self.active_rules[idx]
        self.refresh_rule_list()

    def undo_action(self):
        if self.rule_history:
            self.redo_stack.append(list(self.active_rules))
            self.active_rules = self.rule_history.pop()
            self.refresh_rule_list()

    def redo_action(self):
        if self.redo_stack:
            self.rule_history.append(list(self.active_rules))
            self.active_rules = self.redo_stack.pop()
            self.refresh_rule_list()

    def run_smart_wizard(self):
        if not self.csv_path: return
        try:
            df = pd.read_csv(self.csv_path, nrows=1)
            headers = df.columns.tolist()
            
            self.rule_history.append(list(self.active_rules))
            self.redo_stack.clear()
            
            cnt = 0
            for h in headers:
                hl = h.lower()
                ua = "Chrome"
                if "edge" in hl or "microsoft" in hl: ua = "Edge"
                if "mobile" in hl or "iphone" in hl: ua = "Mobile"
                
                rule = None
                if any(x in hl for x in ["status", "resolve", "alive", "check"]):
                    rule = {'type': 'status_check', 'user_agent': ua, 'target_column': h}
                elif "price" in hl or "cost" in hl:
                    rule = {'type': 'ai_analysis', 'prompt': f"Extract Price for {h}", 'user_agent': ua, 'target_column': h}
                elif "company" in hl or "name" in hl:
                    rule = {'type': 'ai_analysis', 'prompt': f"Extract Company Name for {h}", 'user_agent': ua, 'target_column': h}
                elif "who" in hl or "email" in hl:
                    rule = {'type': 'ai_analysis', 'prompt': f"Extract Contact for {h}", 'user_agent': ua, 'target_column': h}
                
                if rule:
                    self.active_rules.append(rule)
                    cnt += 1
            
            self.refresh_rule_list()
            self.log_msg(f"Wizard: Auto-generated {cnt} rules.")
        except Exception as e:
            self.log_msg(f"Wizard Error: {e}")

    def log_msg(self, msg):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f"{msg}\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def update_ui_hook(self, progress, status, msg):
        self.progress_bar.set(progress)
        self.lbl_status.configure(text=f"{status}: {int(progress*100)}%")
        self.log_msg(f"[{status}] {msg}")
        
        if status in ["Stopped", "Complete"]:
            self.is_running_ui = False
            self.btn_start.configure(state="normal")
            self.btn_pause.configure(state="normal", text="⏸ PAUSE")
            self.btn_stop.configure(state="disabled")
            
        elif status == "Paused":
            self.btn_pause.configure(text="▶ RESUME")

    def start_audit_thread(self):
        if self.is_running_ui: return
        
        if not self.csv_path or not self.active_rules:
            self.log_msg("Error: Missing File or Rules")
            return
        
        limits = {}
        if self.limit_rows.get(): limits['batch_rows'] = int(self.limit_rows.get())
        if self.limit_mins.get(): limits['batch_minutes'] = float(self.limit_mins.get())
        
        api_config = {'primary_key': self.entry_primary.get(), 'backup_key': self.entry_backup.get()}
        
        self.is_running_ui = True
        self.btn_start.configure(state="disabled")
        self.btn_pause.configure(state="normal", text="⏸ PAUSE")
        self.btn_stop.configure(state="normal")
        
        t = threading.Thread(target=self.logic.perform_audit, args=(self.csv_path, self.active_rules, api_config, limits, self.update_ui_hook))
        t.start()

    def toggle_pause(self):
        if not self.is_running_ui: return
        
        if "PAUSE" in self.btn_pause.cget("text"):
            self.logic.request_pause()
            self.btn_pause.configure(text="▶ RESUME")
        else:
            self.logic.request_resume()
            self.btn_pause.configure(text="⏸ PAUSE")

    def stop_audit(self):
        self.logic.request_stop()
        self.btn_stop.configure(state="disabled")

    def export_history(self):
        success, msg, path = self.logic.export_history()
        self.log_msg(f"Export: {msg}")
        if success: os.startfile(os.path.dirname(path))


class LeadGenApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        self.title("LeadGen Factory")
        self.geometry("1100x700")

        self.architect = ArchitectLogic()
        self.harvester = HarvesterLogic()
        self.inspector = InspectorLogic()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="LeadGen\nFactory", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        ctk.CTkButton(self.sidebar, text="🧠 Architect", command=lambda: self.switch(ArchitectView, self.architect)).pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(self.sidebar, text="🚜 Harvester", command=lambda: self.switch(HarvesterView, self.harvester)).pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(self.sidebar, text="🧹 Janitor", command=lambda: self.switch(JanitorView)).pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(self.sidebar, text="🕵️ Inspector", command=lambda: self.switch(InspectorView, self.inspector)).pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(self.sidebar, text="❓ App Guide", fg_color="transparent", border_width=1).pack(side="bottom", pady=20)

        # Content
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew")
        self.curr_view = None
        
        self.switch(ArchitectView, self.architect)

    def switch(self, view_class, logic=None):
        if self.curr_view: self.curr_view.destroy()
        if logic: self.curr_view = view_class(self.main, logic)
        else: self.curr_view = view_class(self.main)
        self.curr_view.pack(fill="both", expand=True, padx=20, pady=20)

if __name__ == "__main__":
    app = LeadGenApp()
    app.mainloop()
