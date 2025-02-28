#!/bin/bash
# Linux/Steam Deck Setup Script

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Display the current directory
echo "Current directory: $(pwd)"

# Check for the existence of requirements.txt
if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "requirements.txt not found in $SCRIPT_DIR. Please ensure the file is in the same directory as this script."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check for Python installation
echo "Checking for Python..."
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python 3.x using your distribution's package manager."
    echo "For SteamOS/Arch: sudo pacman -S python"
    echo "For Debian/Ubuntu: sudo apt install python3"
    read -p "Press Enter to exit..."
    exit 1
fi

python3 --version

# Check for pip installation
echo "Checking for pip..."
if ! command -v pip3 &> /dev/null; then
    echo "Pip is not installed. Installing pip..."
    python3 -m ensurepip --upgrade
    if [ $? -ne 0 ]; then
        echo "Failed to install pip. Please install pip manually:"
        echo "For SteamOS/Arch: sudo pacman -S python-pip"
        echo "For Debian/Ubuntu: sudo apt install python3-pip"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

# Check for the existence of the virtual environment
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Virtual environment not found. Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Checking if python3-venv is installed..."
        echo "For SteamOS/Arch: sudo pacman -S python-virtualenv"
        echo "For Debian/Ubuntu: sudo apt install python3-venv"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"

# Install dependencies from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies. Please check requirements.txt and try again."
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Dependencies installed successfully."
read -p "Press Enter to continue..."