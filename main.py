import customtkinter as ctk

class NavigationController:
    """
    Handles navigation between different views/modules in the main content area.
    """
    def __init__(self, main_content_frame):
        self.main_content_frame = main_content_frame
        self.current_frame = None

    def show_view(self, view_name, title_text):
        """
        Clears the current view and displays the new one with a simple title.
        """
        if self.current_frame is not None:
            self.current_frame.destroy()

        self.current_frame = ctk.CTkFrame(self.main_content_frame, corner_radius=0, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title Label
        title = ctk.CTkLabel(
            self.current_frame, 
            text=title_text, 
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=40, anchor="center")
        
        # Placeholder content
        desc = ctk.CTkLabel(
            self.current_frame,
            text=f"This is the {view_name} view.",
            font=ctk.CTkFont(size=16)
        )
        desc.pack(pady=10)


class LeadGenApp(ctk.CTk):
    def __init__(self):
        super().__init__()

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
        self.nav_controller.show_view("Architect Module", "Welcome to the Architect Module")

    def show_harvester(self):
        self.nav_controller.show_view("Harvester Module", "Welcome to the Harvester Module")

    def show_janitor(self):
        self.nav_controller.show_view("Janitor Module", "Welcome to the Janitor Module")

    def show_inspector(self):
        self.nav_controller.show_view("Inspector Module", "Welcome to the Inspector Module")


if __name__ == "__main__":
    app = LeadGenApp()
    app.mainloop()
