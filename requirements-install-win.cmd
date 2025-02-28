@echo off

:: Get the directory of the script
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

:: Display the current directory
echo Current directory: %cd%

:: Check for the existence of requirements.txt
if not exist "%SCRIPT_DIR%requirements.txt" (
    echo requirements.txt not found in %SCRIPT_DIR%. Please ensure the file is in the same directory as this script.
    pause
    exit /b 1
)

:: Check for Python installation
echo Checking for Python...
python --version
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.x from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check for pip installation
echo Checking for pip...
python -m ensurepip --upgrade
if %errorlevel% neq 0 (
    echo Pip is not installed. Installing pip...
    python -m ensurepip
)

:: Check for the existence of the virtual environment
if not exist "%SCRIPT_DIR%venv" (
    echo Virtual environment not found. Creating virtual environment...
    python -m venv venv
)

:: Activate the virtual environment
echo Activating virtual environment...
call "%SCRIPT_DIR%venv\Scripts\activate.bat"

:: Install dependencies from requirements.txt
echo Installing dependencies from requirements.txt...
pip install -r "%SCRIPT_DIR%requirements.txt"
if %errorlevel% neq 0 (
    echo Failed to install dependencies. Please check requirements.txt and try again.
    pause
    exit /b 1
)

echo Dependencies installed successfully.
pause
