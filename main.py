import customtkinter as ctk
import threading
from modules.architect import ArchitectLogic
from modules.harvester import HarvesterLogic

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

        # 2. Add Column Controls
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.lbl_col_name = ctk.CTkLabel(self.controls_frame, text="New Column:")
        self.lbl_col_name.pack(side="left", padx=10, pady=10)
        
        self.col_name_entry = ctk.CTkEntry(self.controls_frame, placeholder_text="Column Name (e.g., Job Title)")
        self.col_name_entry.pack(side="left", padx=5, pady=10)
        
        self.col_key_entry = ctk.CTkEntry(self.controls_frame, placeholder_text="Keywords (e.g., CEO)", width=200)
        self.col_key_entry.pack(side="left", padx=5, pady=10)
        
        self.btn_add_col = ctk.CTkButton(self.controls_frame, text="Add Column", command=self.add_column)
        self.btn_add_col.pack(side="left", padx=10, pady=10)

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

        # 2. URL Input Area
        self.lbl_urls = ctk.CTkLabel(self, text="Target URLs (One per line):", anchor="w")
        self.lbl_urls.grid(row=0, column=0, sticky="sw", pady=(40, 0)) # Hacky spacing

        self.txt_urls = ctk.CTkTextbox(self, height=150)
        self.txt_urls.grid(row=1, column=0, sticky="nsew", pady=(5, 10))
        self.txt_urls.insert("0.0", "https://example.com\n")

        # 3. Action Bar
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, sticky="ew", pady=10)

        self.btn_start = ctk.CTkButton(self.action_frame, text="Start Harvest 🚜", command=self.start_harvest_thread, height=40, font=ctk.CTkFont(size=16, weight="bold"))
        self.btn_start.pack(fill="x")

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

        if not urls:
            self.log_message("Error: No URLs provided.")
            return

        if recipe_name == "No Recipes Found":
             self.log_message("Error: Please create a recipe in Architect first.")
             return
        
        self.btn_start.configure(state="disabled", text="Harvesting...")
        
        # Start Thread
        t = threading.Thread(target=self.run_harvest_process, args=(urls, recipe_name))
        t.start()

    def run_harvest_process(self, urls, recipe_name):
        self.logic.perform_harvest(urls, recipe_name, self.log_message)
        # Re-enable button (needs main thread call technically, but CTk handles simple config usually gracefully, checking safety)
        self.btn_start.configure(state="normal", text="Start Harvest 🚜")


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

        self.btn_harvester = ctk.CTkButton(
           self.sidebar_frame, text="🚜 Harvester", command=self.show_harvester, anchor="w"
        )
        self.btn_harvester.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_janitor = ctk.CTkButton(
            self.sidebar_frame, text="🧹 Janitor", command=self.show_janitor, anchor="w"
        )
        self.btn_janitor.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_inspector = ctk.CTkButton(
            self.sidebar_frame, text="🕵️ Inspector", command=self.show_inspector, anchor="w"
        )
        self.btn_inspector.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

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
        self.nav_controller.show_placeholder("Janitor Module", "Welcome to the Janitor Module")

    def show_inspector(self):
        self.nav_controller.show_placeholder("Inspector Module", "Welcome to the Inspector Module")


if __name__ == "__main__":
    app = LeadGenApp()
    app.mainloop()
