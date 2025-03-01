@echo off
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%
echo Checking for Python...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.x from https://www.python.org/downloads/
    pause
    exit /b 1
)
if not exist "%SCRIPT_DIR%venv" (
    echo Virtual environment not found. Please ensure the virtual environment is created.
    pause
    exit /b 1
)
echo Activating virtual environment...
call "%SCRIPT_DIR%venv\Scripts\activate.bat"
echo Running Skrunks Mod EXT.pyw...
python "%SCRIPT_DIR%SkrunksModEXT.pyw"
if %errorlevel% neq 0 (
    echo Failed to run Skrunks Mod EXT.pyw. Please check the script and try again.
    pause
    exit /b 1
)

echo Keep on Skrunkin.
pause
