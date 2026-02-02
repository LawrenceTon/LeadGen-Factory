🏭 LeadGen Factory
LeadGen Factory is a modular, desktop-based automation suite designed for high-performance lead generation, data harvesting, list cleaning, and quality assurance. Unlike linear scripts, this application functions as a "Digital Office" with specialized modules for each stage of the data lifecycle.

🚀 Architecture
The application is built on a modular Python architecture using CustomTkinter for the GUI and Playwright for the automation engine.

📂 The Modules
The application is divided into four isolated workspaces:

Module,Icon,Role,Function
The Architect,🧠,Strategy Builder,"Visual editor to create scraping ""Recipes"" (JSON). Users define target columns (e.g., ""CEO Name"") and context rules without coding."
The Harvester,🚜,List Builder,"Executes recipes. Features a ""Human Mode"" to bypass authentication walls (LinkedIn/Facebook) by allowing manual user login before automation."
The Janitor,🧹,Data Cleaner,"Drag-and-drop cleaning suite. Handles deduplication, name splitting, and toxic keyword filtering on any CSV file."
The Inspector,🕵️,Quality Control,Validates data integrity. Pings URLs for 200 OK status and verifies email syntax before finalizing the list.

🛠️ Technical Stack
Interface: customtkinter (Python GUI)

Automation: playwright (Browser Engine)

Data Processing: pandas (CSV/Excel Logic)

Configuration: JSON (Recipe Storage)

LeadGen-Factory/
├── modules/           # Independent logic for each worker (harvester.py, etc.)
├── recipes/           # JSON files defining search strategies
├── output/            # Raw and Cleaned CSV exports (GitIgnored)
├── assets/            # Icons and UI resources
├── main.py            # GUI Entry point and Navigation Controller
└── requirements.txt   # Dependency list


🔮 Roadmap
[ ] Phase 1: Core GUI Shell & Navigation (Current)

[ ] Phase 2: Recipe Builder & JSON Logic

[ ] Phase 3: Harvester Engine & Human Mode

[ ] Phase 4: Cleaning & QC Utilities


Property of Lawrence Anthony Juntilla
