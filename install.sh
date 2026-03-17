#!/bin/bash
# install.sh - Install SpaceMouse VirtualHere forwarding setup

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "SpaceMouse VirtualHere Forwarding - Install"
echo "============================================"
echo ""

# Check for VirtualHere binary
if [[ ! -f /opt/virtualhere/vhusbdx86_64 ]]; then
    log_warn "VirtualHere binary not found at /opt/virtualhere/vhusbdx86_64"
    echo "    Download from: https://www.virtualhere.com/usb_server_software"
    echo "    Then: sudo mkdir -p /opt/virtualhere && sudo cp vhusbdx86_64 /opt/virtualhere/"
    echo ""
fi

# Install scripts
log_info "Installing scripts..."
sudo cp "$SCRIPT_DIR/spacemouse-ctl" /usr/local/bin/
sudo cp "$SCRIPT_DIR/spacemouse-ctl-root" /usr/local/bin/
sudo chmod 755 /usr/local/bin/spacemouse-ctl /usr/local/bin/spacemouse-ctl-root

# Tray app
mkdir -p ~/.local/bin
cp "$SCRIPT_DIR/spacemouse-tray.py" ~/.local/bin/
chmod +x ~/.local/bin/spacemouse-tray.py
log_info "Installed tray app to ~/.local/bin/"

# Systemd service
log_info "Installing systemd service..."
sudo cp "$SCRIPT_DIR/virtualhere-spacemouse.service" /etc/systemd/system/
sudo systemctl daemon-reload

# Polkit policy
log_info "Installing polkit policy..."
sudo cp "$SCRIPT_DIR/org.spacemouse.ctl.policy" /usr/share/polkit-1/actions/

# Config directory
if [[ ! -d /etc/virtualhere ]]; then
    log_info "Creating /etc/virtualhere..."
    sudo mkdir -p /etc/virtualhere/certs
fi

if [[ ! -f /etc/virtualhere/config.ini ]]; then
    log_warn "No config.ini found - copying example"
    sudo cp "$SCRIPT_DIR/config.ini.example" /etc/virtualhere/config.ini
    echo "    Edit /etc/virtualhere/config.ini and set SSLReverseClients to your Windows VM IP"
fi

# Autostart
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/spacemouse-tray.desktop << EOF
[Desktop Entry]
Name=SpaceMouse Control
Comment=Toggle SpaceMouse between local and Windows VM
Exec=/usr/bin/python3 $HOME/.local/bin/spacemouse-tray.py
Icon=input-mouse
Type=Application
Categories=Utility;
X-GNOME-Autostart-enabled=true
EOF
log_info "Created autostart entry"

echo ""
log_info "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Ensure VirtualHere binary is at /opt/virtualhere/vhusbdx86_64"
echo "  2. Edit /etc/virtualhere/config.ini (set Windows VM IP)"
echo "  3. Generate SSL certs (see README.md)"
echo "  4. Copy ca.crt and client.pem to Windows VM"
echo "  5. Configure Windows VirtualHere client for reverse SSL"
echo "  6. Test: spacemouse-ctl forward"
echo ""
