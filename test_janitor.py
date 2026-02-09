import customtkinter as ctk
from modules.janitor import JanitorModule

# Create a standalone window just for the Janitor
app = ctk.CTk()
app.geometry("800x600")
app.title("Janitor Isolation Test")

print("--- ATTEMPTING TO LOAD JANITOR MODULE ---")

try:
    # Initialize the Janitor directly
    janitor = JanitorModule(app)
    janitor.pack(fill="both", expand=True)
    print("✅ SUCCESS: Janitor Module Loaded.")
except Exception as e:
    print(f"❌ CRITICAL FAILURE: {e}")

app.mainloop()