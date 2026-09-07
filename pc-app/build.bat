@echo off
REM Builds RedLight.exe (single file, no console window) into dist\
if not exist redlight.ico python generate_icon.py
pyinstaller --onefile --windowed --name RedLight --icon redlight.ico --add-data "templates;templates" main.py
