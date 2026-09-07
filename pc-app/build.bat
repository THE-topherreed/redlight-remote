@echo off
REM Builds RedLight.exe (single file, no console window) into dist\
pyinstaller --onefile --windowed --name RedLight --add-data "templates;templates" main.py
