#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
echo "Current directory: $(pwd)"

# Check if requirements.txt exists
if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "requirements.txt not found in $SCRIPT_DIR. Please ensure the file is in the same directory as this script."
    read -p "Press Enter to exit..."
    exit 1
fi

# Function to install dependencies for Debian-based systems
install_debian_dependencies() {
    echo "Detected Debian-based system. Installing dependencies..."
    sudo apt update
    sudo apt install -y python3-pip python3-virtualenv curl
}

# Function to install dependencies for Arch-based systems
install_arch_dependencies() {
    echo "Detected Arch-based system. Installing dependencies..."
    sudo pacman -Syu --noconfirm base-devel curl python-pip python-virtualenv
}

# Function to install dependencies for SteamOS (Arch-based with specific adjustments)
install_steamos_dependencies() {
    echo "Detected SteamOS. Installing SteamOS-specific dependencies..."
    sudo pacman -Syu --noconfirm base-devel curl python-pip python-virtualenv
}

# Check if the system is SteamOS or Arch-based
if [ -f /etc/arch-release ]; then
    if [ -f /etc/os-release ] && grep -q "SteamOS" /etc/os-release; then
        # SteamOS-specific setup
        install_steamos_dependencies
	sudo steamos-devmode enable
    else
        # Generic Arch-based setup
        install_arch_dependencies
    fi
elif [ -f /etc/debian_version ]; then
    # Debian-based system setup (Ubuntu, etc.)
    install_debian_dependencies
else
    echo "Unknown distribution. Please ensure necessary dependencies are installed manually."
    exit 1
fi

# Ensure that the script is running as the `deck` user (SteamOS default user)
if [ "$(whoami)" != "deck" ] && [ "$(logname)" != "deck" ]; then
    echo "This script must be run as the 'deck' user."
    read -p "Press Enter to exit..."
    exit 1
fi

# Install uv using pip
if ! command -v uv &> /dev/null; then
    echo "Installing uv using pip..."
    pip install --user uv --break-system-packages
fi

# Add local bin to PATH for uv
export PATH="$HOME/.local/bin:$PATH"
exec bash

# Install dependencies using uv
echo "Installing dependencies using uv..."
uv run --with-requirements requirements.txt SkrunksModEXT.pyw 

# Remount the filesystem as read-only (if necessary for SteamOS)
echo "Remounting the filesystem as read-only..."
sudo mount -o remount,ro /

echo "Setup complete! Dependencies installed using uv."
read -p "Press Enter to exit..."
