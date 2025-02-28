#!/bin/bash
CURRENT_USER=$(whoami)
CURRENT_UID=$(id -u)
RULE_FILE="/etc/udev/rules.d/99-arcticfox.rules"
if [[ "$EUID" -ne 0 ]]; then
    echo "This script must be run as root! Use: sudo $0"
    exit 1
fi
if ! grep -q "^arcticfox:" /etc/group; then
    echo "Creating arcticfox group..."
    sudo groupadd arcticfox
fi
echo "Adding $CURRENT_USER to arcticfox group..."
sudo usermod -aG arcticfox "$CURRENT_USER"
echo "Making filesystem writable..."
sudo steamos-readonly disable
echo "Creating udev rules..."
echo '# HIDAPI/libusb
SUBSYSTEM=="usb", ATTRS{idVendor}=="0416", ATTRS{idProduct}=="5020", MODE="0660", GROUP="arcticfox"
KERNEL=="hidraw*", ATTRS{busnum}=="1", ATTRS{idVendor}=="0416", ATTRS{idProduct}=="5020", MODE="0660", GROUP="arcticfox"' | sudo tee "$RULE_FILE" > /dev/null
echo "Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "Restoring readonly mode..."
sudo steamos-readonly enable

echo "Setup complete! Log out and back in for group changes to take effect."
exit 0
