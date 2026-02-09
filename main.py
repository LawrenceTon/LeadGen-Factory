import customtkinter as ctk
import os
# Import your modules
from modules.harvester import HarvesterModule
from modules.janitor import JanitorModule
from modules.inspector import InspectorModule

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class LeadGenFactoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🏭 LeadGen Factory v4.0")
        self.geometry("1400x900")
        
        # Configure Grid (Single column, full width)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- TAB SYSTEM (ON TOP) ---
        self.tab_view = ctk.CTkTabview(self, anchor="nw")
        self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Create Tabs
        self.tab_view.add("Harvester")
        self.tab_view.add("Janitor") 
        self.tab_view.add("Inspector")

        # Load Modules
        self.setup_tabs()

    def setup_tabs(self):
        # 1. Harvester (Search & SOP Genesis)
        self.harvester = HarvesterModule(self.tab_view.tab("Harvester"))
        self.harvester.pack(fill="both", expand=True)

        # 2. Janitor (Verification & SOP Audit)
        self.janitor = JanitorModule(self.tab_view.tab("Janitor"))
        self.janitor.pack(fill="both", expand=True)

        # 3. Inspector (AI Vision)
        self.inspector = InspectorModule(self.tab_view.tab("Inspector"))
        self.inspector.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = LeadGenFactoryApp()
    app.mainloop()