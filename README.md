# VirtualHere SpaceMouse Forwarding

Sandboxed VirtualHere setup to forward SpaceMouse Compact to Windows VM via reverse SSL connection.

## Features

- **Reverse SSL**: Linux initiates connection to Windows (no inbound ports on Linux)
- **Mutual cert auth**: Both sides verify certificates
- **Sandboxed service**: VirtualHere runs with filesystem/kernel protections
- **Device filtering**: Only SpaceMouse is exposed (AllowedDevices)
- **Quick toggle**: CLI and tray icon to switch between local (Onshape) and forward (Windows)

## Prerequisites

- VirtualHere USB Server license ($49): https://www.virtualhere.com/purchase
- VirtualHere binary: https://www.virtualhere.com/usb_server_software
- spacenavd + spacenav-ws (for local Onshape use)

## Install

```bash
./install.sh
```

Or manually:

```bash
# Binary (download separately, requires license)
sudo mkdir -p /opt/virtualhere
sudo cp vhusbdx86_64 /opt/virtualhere/
sudo chmod 755 /opt/virtualhere/vhusbdx86_64

# Scripts
sudo cp spacemouse-ctl /usr/local/bin/
sudo cp spacemouse-ctl-root /usr/local/bin/
sudo chmod 755 /usr/local/bin/spacemouse-ctl*
cp spacemouse-tray.py ~/.local/bin/

# Systemd service
sudo cp virtualhere-spacemouse.service /etc/systemd/system/
sudo systemctl daemon-reload

# Polkit policy (for GUI auth dialogs)
sudo cp org.spacemouse.ctl.policy /usr/share/polkit-1/actions/

# Config directory + certs (generate your own)
sudo mkdir -p /etc/virtualhere/certs
sudo cp config.ini.example /etc/virtualhere/config.ini
# Edit config.ini: set SSLReverseClients to your Windows VM IP
```

## Generate SSL Certificates

```bash
cd /etc/virtualhere/certs

# CA
sudo openssl genrsa -out ca.key 4096
sudo openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/CN=SpaceMouse-CA/O=Homelab"

# Server
sudo openssl genrsa -out server.key 2048
sudo openssl req -new -key server.key -out server.csr -subj "/CN=spacemouse-server/O=Homelab"
sudo openssl x509 -req -days 3650 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt
sudo cat server.key server.crt | sudo tee server.pem > /dev/null

# Client (copy to Windows)
sudo openssl genrsa -out client.key 2048
sudo openssl req -new -key client.key -out client.csr -subj "/CN=windows-vm/O=Homelab"
sudo openssl x509 -req -days 3650 -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt
sudo cat client.key client.crt | sudo tee client.pem > /dev/null
```

Copy to Windows VM:
- `ca.crt` (rename to `ca.pem` if needed)
- `client.pem`

## Windows VM Setup

1. Install VirtualHere Client
2. USB Hubs → Specify Hubs → Advanced → ☑ Enable Reverse SSL Connections
3. Advanced Settings → SSL tab:
   - Client Certificate File: `client.pem`
   - Certificate Authority File: `ca.pem`
4. Firewall: allow TCP 7572 inbound

## Usage

```bash
spacemouse-ctl local     # Use with Onshape (browser)
spacemouse-ctl forward   # Forward to Windows VM
spacemouse-ctl stop      # Idle (spacenavd only)
spacemouse-ctl status    # Check current mode
```

Tray icon: left-click cycles modes, right-click for menu.

## Sandbox Protections

| Protection | Status |
|------------|--------|
| ProtectHome=yes | ✅ /home hidden |
| ProtectSystem=strict | ✅ Filesystem read-only |
| ProtectKernelModules | ✅ Can't load modules |
| ProtectKernelTunables | ✅ Can't modify sysctl |
| NoNewPrivileges | ✅ Can't escalate |
| AllowedDevices | ✅ Only SpaceMouse visible |
| MemoryMax/CPUQuota | ✅ Resource limited |

## Files

| Installed Location | Purpose |
|--------------------|---------|
| `/opt/virtualhere/vhusbdx86_64` | VirtualHere binary |
| `/etc/virtualhere/config.ini` | Server config |
| `/etc/virtualhere/certs/` | SSL certificates |
| `/etc/systemd/system/virtualhere-spacemouse.service` | Sandboxed service |
| `/usr/local/bin/spacemouse-ctl` | Toggle script |
| `/usr/local/bin/spacemouse-ctl-root` | Privileged helper |
| `/usr/share/polkit-1/actions/org.spacemouse.ctl.policy` | Polkit auth policy |
| `~/.local/bin/spacemouse-tray.py` | System tray app |

## Acknowledgments

This project was developed with assistance from Claude (Anthropic).
