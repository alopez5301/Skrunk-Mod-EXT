#!/bin/bash
SCRIPT_DIR=$(dirname "$(realpath "$0")")
cd "$SCRIPT_DIR"
echo "Checking for Python..."
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python 3.x from https://www.python.org/downloads/"
    read -p "Press any key to continue..."
    exit 1
fi

if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Virtual environment not found. Please ensure the virtual environment is created."
    read -p "Press any key to continue..."
    exit 1
fi

echo "Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"

echo "Running SkrunksModEXT.pyw..."
"${SCRIPT_DIR}/venv/bin/python" "${SCRIPT_DIR}/SkrunksModEXT.pyw"

if [ $? -ne 0 ]; then
    echo "Failed to run SkrunksModEXT.pyw. Please check the script and try again."
    read -p "Press any key to continue..."
    exit 1
fi

echo "Keep on Skrunkin"
read -p "Press any key to continue..."
exit 1