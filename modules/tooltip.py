import customtkinter as ctk
import tkinter as tk

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        
        try:
            # Calculate Position
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
            
            self.tip_window = tk.Toplevel(self.widget)
            self.tip_window.wm_overrideredirect(True)
            self.tip_window.wm_geometry(f"+{x}+{y}")
            
            label = ctk.CTkLabel(
                self.tip_window, 
                text=self.text, 
                fg_color="#111111", 
                text_color="white", 
                corner_radius=6,
                padx=10, 
                pady=5,
                font=ctk.CTkFont(size=12)
            )
            label.pack()

            # Lift above everything
            self.tip_window.lift()
        except Exception:
            pass

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
