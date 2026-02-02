@echo off
echo 🚀 Building LeadGen Factory...
pip install pyinstaller
pyinstaller --noconsole --onefile --name="LeadGenFactory" --icon="app_icon.ico" --add-data="logo.png;." --add-data="modules;modules" --hidden-import="playwright" --collect-all="customtkinter" main.py
echo ✅ Build Complete! Look in the 'dist' folder.
pause
