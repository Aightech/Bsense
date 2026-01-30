@echo off
REM Local build script for Bsense (Windows)
REM Usage: build.bat

echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Building Bsense...
pyinstaller bsense.spec

echo.
echo Build complete! Executable is in: dist\Bsense.exe
echo.

dir dist\Bsense.exe
