import customtkinter as ctk
import threading
from tkinter import filedialog
from modules.architect import ArchitectLogic
from modules.harvester import HarvesterLogic
from modules.inspector import InspectorLogic
# Placeholder for JanitorLogic if you implement it later, 
# for now we'll just code the UI directly in main or a dummy logic class.
# from modules.janitor import JanitorLogic 
from modules.tooltip import ToolTip

class JanitorView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(self, text="Janitor Module (Coming Soon)", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_title.pack(pady=40)
        
        # Placeholder UI for visual completeness based on requests
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
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # List area expands

        # 1. Header & Recipe Name
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Architect Module", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(side="left")

        self.name_entry = ctk.CTkEntry(self.header_frame, placeholder_text="Recipe Name (e.g., Lead Gen - Tech)", width=300)
        self.name_entry.pack(side="right")
        ToolTip(self.name_entry, "Name your scraping strategy.")

        # 2. Add Column Controls
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.lbl_col_name = ctk.CTkLabel(self.controls_frame, text="New Column:")
        self.lbl_col_name.pack(side="left", padx=10, pady=10)
        
        self.col_name_entry = ctk.CTkEntry(self.controls_frame, placeholder_text="Column Name (e.g., Job Title)")
        self.col_name_entry.pack(side="left", padx=5, pady=10)
        ToolTip(self.col_name_entry, "The label for the data you want to extract.")
        
        self.col_key_entry = ctk.CTkEntry(self.controls_frame, placeholder_text="Keywords (e.g., CEO)", width=200)
        self.col_key_entry.pack(side="left", padx=5, pady=10)
        ToolTip(self.col_key_entry, "Keywords to search for in this column.")
        
        self.btn_add_col = ctk.CTkButton(self.controls_frame, text="Add Column", command=self.add_column)
        self.btn_add_col.pack(side="left", padx=10, pady=10)
        ToolTip(self.btn_add_col, "Add this column definition to the recipe.")

        # 3. Dynamic List of Columns (Scrollable)
        self.columns_scroll = ctk.CTkScrollableFrame(self, label_text="Target Columns")
        self.columns_scroll.grid(row=2, column=0, sticky="nsew")
        
        self.column_items = [] # To store references to row widgets data

        # 4. Footer & Save
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=3, column=0, sticky="ew", pady=20)

        self.status_label = ctk.CTkLabel(self.footer_frame, text="", text_color="green")
        self.status_label.pack(side="left")
        
        self.btn_save = ctk.CTkButton(self.footer_frame, text="Save Recipe", command=self.save_recipe, fg_color="green")
        self.btn_save.pack(side="right")
        ToolTip(self.btn_save, "Save this configuration as a JSON recipe.")

    def add_column(self):
        col_name = self.col_name_entry.get()
        keywords = self.col_key_entry.get()
        
        if not col_name:
            self.status_label.configure(text="Error: Column Name is required!", text_color="red")
            return

        # Visual Row
        row_frame = ctk.CTkFrame(self.columns_scroll)
        row_frame.pack(fill="x", pady=2)
        
        lbl = ctk.CTkLabel(row_frame, text=f"{col_name} : {keywords}", anchor="w")
        lbl.pack(side="left", padx=10, pady=5)
        
        # Store data for saving
        self.column_items.append({"col_name": col_name, "keywords": keywords})
        
        # Clear inputs
        self.col_name_entry.delete(0, "end")
        self.col_key_entry.delete(0, "end")
        self.status_label.configure(text="")

    def save_recipe(self):
        name = self.name_entry.get()
        if not name:
            self.status_label.configure(text="Error: Recipe Name is required!", text_color="red")
            return
            
        if not self.column_items:
            self.status_label.configure(text="Error: Add at least one column!", text_color="red")
            return

        success = self.logic.save_recipe(name, self.column_items)
        if success:
            self.status_label.configure(text="Recipe Saved Successfully!", text_color="green")
            # Clear UI if needed, but keeping for now
        else:
            self.status_label.configure(text="Error saving recipe.", text_color="red")

class HarvesterView(ctk.CTkFrame):
    def __init__(self, master, logic):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.logic = logic
        
        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # URL Area
        self.grid_rowconfigure(3, weight=1) # Console Area

        # 1. Top Bar: Recipe Selection
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.lbl_recipe = ctk.CTkLabel(self.top_frame, text="Select Recipe:", font=ctk.CTkFont(weight="bold"))
        self.lbl_recipe.pack(side="left", padx=(0, 10))

        self.recipe_options = self.logic.get_recipe_names()
        if not self.recipe_options:
            self.recipe_options = ["No Recipes Found"]

        self.option_recipe = ctk.CTkOptionMenu(self.top_frame, values=self.recipe_options)
        self.option_recipe.pack(side="left")
        ToolTip(self.option_recipe, "Select the strategy blueprint created in the Architect tab.")
        
        # Human Mode Checkbox
        self.chk_human = ctk.CTkCheckBox(self.top_frame, text="Human Mode (Show Browser)")
        self.chk_human.pack(side="left", padx=20)
        ToolTip(self.chk_human, "✅ Visible Browser (Safer)\n❌ Invisible (Faster).")

        # 2. URL Input Area
        self.lbl_urls = ctk.CTkLabel(self, text="Target URLs (One per line):", anchor="w")
        self.lbl_urls.grid(row=0, column=0, sticky="sw", pady=(40, 0)) # Hacky spacing

        self.txt_urls = ctk.CTkTextbox(self, height=150)
        self.txt_urls.grid(row=1, column=0, sticky="nsew", pady=(5, 10))
        self.txt_urls.insert("0.0", "https://example.com\n")
        ToolTip(self.txt_urls, "Paste the list of website URLs you want to scrape here.")

        # 3. Action Bar
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, sticky="ew", pady=10)

        self.btn_start = ctk.CTkButton(self.action_frame, text="Start Harvest 🚜", command=self.start_harvest_thread, height=40, font=ctk.CTkFont(size=16, weight="bold"))
        self.btn_start.pack(fill="x")
        ToolTip(self.btn_start, "Begin scraping leads.")

        # 4. Console Log
        self.lbl_console = ctk.CTkLabel(self, text="Harvest Log:", anchor="w")
        self.lbl_console.grid(row=3, column=0, sticky="nw", pady=(10, 0))

        self.txt_console = ctk.CTkTextbox(self, state="disabled") # Read-only
        self.txt_console.grid(row=4, column=0, sticky="nsew", pady=(5, 0))

    def refresh_recipes(self):
        """Update dropdown in case new recipes were added."""
        recipes = self.logic.get_recipe_names()
        if recipes:
            self.option_recipe.configure(values=recipes)
            self.option_recipe.set(recipes[0])
        else:
            self.option_recipe.configure(values=["No Recipes Found"])

    def log_message(self, msg):
        """Thread-safe logging to GUI."""
        self.txt_console.configure(state="normal")
        self.txt_console.insert("end", f"{msg}\n")
        self.txt_console.see("end")
        self.txt_console.configure(state="disabled")

    def start_harvest_thread(self):
        recipe_name = self.option_recipe.get()
        raw_urls = self.txt_urls.get("0.0", "end")
        urls = [u for u in raw_urls.split("\n") if u.strip()]
        
        # Get Human Mode State
        human_mode = bool(self.chk_human.get())

        if not urls:
            self.log_message("Error: No URLs provided.")
            return

        if recipe_name == "No Recipes Found":
             self.log_message("Error: Please create a recipe in Architect first.")
             return
        
        self.btn_start.configure(state="disabled", text="Harvesting...")
        
        # Start Thread
        t = threading.Thread(target=self.run_harvest_process, args=(urls, recipe_name, human_mode))
        t.start()

    def run_harvest_process(self, urls, recipe_name, human_mode):
        self.logic.perform_harvest(urls, recipe_name, self.log_message, human_mode=human_mode)
        # Re-enable button
        self.btn_start.configure(state="normal", text="Start Harvest 🚜")

class InspectorView(ctk.CTkFrame):
    def __init__(self, master, logic):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.logic = logic
        self.csv_path = None
        self.active_rules = []

        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1) # Log expands

        # 0. API Configuration (Step 1)
        self.step1_lbl = ctk.CTkLabel(self, text="Step 1: Connect AI Brain (Optional but Recommended)", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.step1_lbl.grid(row=0, column=0, sticky="w", pady=(10, 5))

        self.api_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.api_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        self.lbl_api = ctk.CTkLabel(self.api_frame, text="AI Settings:")
        self.lbl_api.pack(side="left", padx=10)
        
        self.entry_primary = ctk.CTkEntry(self.api_frame, placeholder_text="Primary API Key (Gemini)", width=200, show="*")
        self.entry_primary.pack(side="left", padx=5)
        ToolTip(self.entry_primary, "Paste your Gemini API Key (starts with AIza...) here to enable Vision AI.")
        
        self.entry_backup = ctk.CTkEntry(self.api_frame, placeholder_text="Backup API Key (Optional)", width=200, show="*")
        self.entry_backup.pack(side="left", padx=5)
        ToolTip(self.entry_backup, "Optional OpenAI Key for failover redundancy.")

        # 1. File Selection (Step 2)
        self.step2_lbl = ctk.CTkLabel(self, text="Step 2: Upload Targets", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.step2_lbl.grid(row=2, column=0, sticky="w", pady=(0, 5))

        self.file_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.file_frame.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        
        self.btn_select = ctk.CTkButton(self.file_frame, text="Select CSV File", command=self.select_file)
        self.btn_select.pack(side="left", padx=(0, 10))
        ToolTip(self.btn_select, "Upload a CSV file. It MUST have a column named 'URL', 'Domain', or 'Website'.")
        
        self.lbl_file = ctk.CTkLabel(self.file_frame, text="No file selected")
        self.lbl_file.pack(side="left")

        # 2. Rule Builder (Step 3)
        self.step3_lbl = ctk.CTkLabel(self, text="Step 3: Build Audit Logic", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.step3_lbl.grid(row=4, column=0, sticky="w", pady=(0, 5))

        self.rule_frame = ctk.CTkFrame(self)
        self.rule_frame.grid(row=5, column=0, sticky="ew", pady=(0, 5))
        self.rule_frame.grid_columnconfigure(1, weight=1) # input expands
        
        self.lbl_rule_type = ctk.CTkLabel(self.rule_frame, text="Add Rule:")
        self.lbl_rule_type.grid(row=0, column=0, padx=10, pady=10)
        
        self.rule_types = ['Check Status', 'Contains Keyword', 'Extract Price', 'AI Analysis']
        self.option_rule = ctk.CTkOptionMenu(self.rule_frame, values=self.rule_types, command=self.toggle_input)
        self.option_rule.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ToolTip(self.option_rule, "Choose what to check (e.g., 'Check Status' for broken links, '[AI Analysis]' for vision).")
        
        self.rule_input = ctk.CTkEntry(self.rule_frame, placeholder_text="Keyword")
        # Initially hidden
        
        self.btn_add_rule = ctk.CTkButton(self.rule_frame, text="+ Add Rule", command=self.add_rule)
        self.btn_add_rule.grid(row=0, column=3, padx=10, pady=10)
        ToolTip(self.btn_add_rule, "Push this rule into the active stack.")
        
        # 3. Active Rules List
        self.rules_scroll = ctk.CTkScrollableFrame(self, label_text="Active Rules", height=150)
        self.rules_scroll.grid(row=6, column=0, sticky="nsew", pady=(0, 20)) # using nsew to fill better
        
        # 4. Action & Log
        self.btn_run = ctk.CTkButton(self, text="Start Inspector 🕵️", command=self.start_audit_thread, height=40, font=ctk.CTkFont(size=16, weight="bold"), fg_color="purple")
        self.btn_run.grid(row=7, column=0, sticky="ew") # sticky top
        ToolTip(self.btn_run, "Launch the browser and begin the audit.")
        
        self.txt_log = ctk.CTkTextbox(self, state="disabled")
        self.txt_log.grid(row=8, column=0, sticky="nsew", pady=(10, 0))

    def select_file(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filename:
            self.csv_path = filename
            self.lbl_file.configure(text=filename)

    def toggle_input(self, choice):
        self.rule_input.grid_forget()
        if choice == 'Contains Keyword':
            self.rule_input.configure(placeholder_text="Keyword (e.g., Sold)")
            self.rule_input.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        elif choice == 'AI Analysis':
            self.rule_input.configure(placeholder_text="Prompt (e.g., Is this legit?)")
            self.rule_input.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

    def add_rule(self):
        r_type = self.option_rule.get()
        rule_def = {}
        display_text = ""
        
        if r_type == 'Check Status':
            rule_def = {'type': 'status_check'}
            display_text = "1. Check HTTP Status & Redirects"
            
        elif r_type == 'Contains Keyword':
            val = self.rule_input.get()
            if not val: return 
            rule_def = {'type': 'keyword', 'value': val}
            display_text = f"2. Check for Keyword: '{val}'"
            self.rule_input.delete(0, "end")
            
        elif r_type == 'Extract Price':
            rule_def = {'type': 'extract_price'}
            display_text = "3. Extract Prices (Regex)"

        elif r_type == 'AI Analysis':
            val = self.rule_input.get()
            if not val: return
            rule_def = {'type': 'ai_analysis', 'prompt': val}
            display_text = f"4. AI Analysis: '{val}'"
            self.rule_input.delete(0, "end")

        self.active_rules.append(rule_def)
        
        # Visual
        lbl = ctk.CTkLabel(self.rules_scroll, text=display_text, anchor="w")
        lbl.pack(fill="x", padx=5, pady=2)

    def log_message(self, msg):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f"{msg}\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def start_audit_thread(self):
        if not self.csv_path:
            self.log_message("Error: Select a CSV file first.")
            return
        
        if not self.active_rules:
            self.log_message("Error: Add at least one rule.")
            return
            
        # Get Keys
        primary_key = self.entry_primary.get()
        backup_key = self.entry_backup.get()
        
        api_config = {
            'primary_key': primary_key,
            'backup_key': backup_key
        }

        self.btn_run.configure(state="disabled", text="Inspecting...")
        
        t = threading.Thread(target=self.run_audit_process, args=(api_config,))
        t.start()

    def run_audit_process(self, api_config):
        self.logic.perform_audit(self.csv_path, self.active_rules, api_config, self.log_message)
        self.btn_run.configure(state="normal", text="Start Inspector 🕵️")


class NavigationController:
    """
    Handles navigation between different views/modules in the main content area.
    """
    def __init__(self, main_content_frame):
        self.main_content_frame = main_content_frame
        self.current_frame = None

    def switch_to_view(self, view_class, **kwargs):
        """
        Destroys the current view and instantiates the new view class.
        """
        if self.current_frame is not None:
            self.current_frame.destroy()

        self.current_frame = view_class(self.main_content_frame, **kwargs)
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Hook for refresh if exists
        if hasattr(self.current_frame, 'refresh_recipes'):
            self.current_frame.refresh_recipes()

    def show_placeholder(self, view_name, title_text):
        """
        Generic placeholder for unfinished modules.
        """
        if self.current_frame is not None:
            self.current_frame.destroy()

        self.current_frame = ctk.CTkFrame(self.main_content_frame, corner_radius=0, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(
            self.current_frame, 
            text=title_text, 
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=40, anchor="center")
        
        desc = ctk.CTkLabel(
            self.current_frame,
            text=f"This is the {view_name} view.",
            font=ctk.CTkFont(size=16)
        )
        desc.pack(pady=10)


class LeadGenApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Logic Modules
        self.architect_logic = ArchitectLogic()
        self.harvester_logic = HarvesterLogic()
        self.inspector_logic = InspectorLogic()

        # System Settings
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Window Setup
        self.title("LeadGen Factory")
        self.geometry("1100x700")

        # Layout Configuration
        self.grid_columnconfigure(1, weight=1)  # Main content takes all extra space
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Spacer at bottom

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="LeadGen\nFactory", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Navigation Buttons
        self.btn_architect = ctk.CTkButton(
            self.sidebar_frame, text="🧠 Architect", command=self.show_architect, anchor="w"
        )
        self.btn_architect.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ToolTip(self.btn_architect, text="Strategies: Define what to scrape")

        self.btn_harvester = ctk.CTkButton(
           self.sidebar_frame, text="🚜 Harvester", command=self.show_harvester, anchor="w"
        )
        self.btn_harvester.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ToolTip(self.btn_harvester, text="Harvester: Run the scraping jobs")

        self.btn_janitor = ctk.CTkButton(
            self.sidebar_frame, text="🧹 Janitor", command=self.show_janitor, anchor="w"
        )
        self.btn_janitor.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ToolTip(self.btn_janitor, text="Janitor: Clean and Format CSVs")

        self.btn_inspector = ctk.CTkButton(
            self.sidebar_frame, text="🕵️ Inspector", command=self.show_inspector, anchor="w"
        )
        self.btn_inspector.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        ToolTip(self.btn_inspector, text="Inspector: AI Audit & Vision Analysis")

        # App Guide Button
        self.btn_guide = ctk.CTkButton(
            self.sidebar_frame, text="❓ App Guide", width=100, fg_color="transparent", border_width=1
        )
        self.btn_guide.grid(row=6, column=0, padx=20, pady=20)
        
        guide_text = "DIRECTORY:\n\n1. Architect: Build Recipes\n2. Harvester: Find Leads\n3. Janitor: Clean Data\n4. Inspector: AI Analysis"
        ToolTip(self.btn_guide, text=guide_text)


        # 2. Main Content Area
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew")

        # Initialize Navigation Controller
        self.nav_controller = NavigationController(self.main_content_frame)

        # Show default view
        self.show_architect()

    def show_architect(self):
        self.nav_controller.switch_to_view(ArchitectView, logic=self.architect_logic)

    def show_harvester(self):
        self.nav_controller.switch_to_view(HarvesterView, logic=self.harvester_logic)

    def show_janitor(self):
        self.nav_controller.switch_to_view(JanitorView)

    def show_inspector(self):
        self.nav_controller.switch_to_view(InspectorView, logic=self.inspector_logic)


if __name__ == "__main__":
    app = LeadGenApp()
    app.mainloop()
