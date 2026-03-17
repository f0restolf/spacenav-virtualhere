#!/usr/bin/python3
"""
SpaceMouse Tray - System tray icon for switching SpaceMouse modes
Secure version with sandboxed VirtualHere forwarding

Requires: PyQt6 (sudo dnf install python3-pyqt6)
"""

import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox

SPACEMOUSE_CTL = "/usr/local/bin/spacemouse-ctl"

# Inline SVG icons
ICON_IDLE = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#888888" stroke-width="2">
  <circle cx="12" cy="12" r="10"/>
  <circle cx="12" cy="12" r="3"/>
</svg>
"""

ICON_LOCAL = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#4CAF50" stroke-width="2">
  <circle cx="12" cy="12" r="10"/>
  <circle cx="12" cy="12" r="3" fill="#4CAF50"/>
  <path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>
</svg>
"""

ICON_FORWARD = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#2196F3" stroke-width="2">
  <circle cx="12" cy="12" r="10"/>
  <circle cx="12" cy="12" r="3" fill="#2196F3"/>
  <path d="M12 5l3 3-3 3M12 8h7"/>
  <path d="M6 16h2M10 16h2M14 16h2" stroke-width="1.5"/>
</svg>
"""

# Forward icon with lock to indicate sandboxed/secure
ICON_FORWARD_SECURE = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#2196F3" stroke-width="2">
  <circle cx="12" cy="12" r="10"/>
  <circle cx="12" cy="12" r="3" fill="#2196F3"/>
  <path d="M12 5l3 3-3 3M12 8h7"/>
  <rect x="15" y="14" width="6" height="5" rx="1" stroke="#4CAF50" fill="none" stroke-width="1.5"/>
  <path d="M16 14v-1.5a2 2 0 0 1 4 0V14" stroke="#4CAF50" stroke-width="1.5"/>
</svg>
"""


def svg_to_icon(svg_data: str) -> QIcon:
    """Convert inline SVG to QIcon."""
    from PyQt6.QtCore import QByteArray
    from PyQt6.QtSvg import QSvgRenderer
    from PyQt6.QtGui import QPixmap, QPainter
    
    renderer = QSvgRenderer(QByteArray(svg_data.encode()))
    pixmap = QPixmap(64, 64)
    pixmap.fill()
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def run_ctl(command: str) -> tuple[bool, str]:
    """Run spacemouse-ctl command and return (success, output)."""
    try:
        result = subprocess.run(
            [SPACEMOUSE_CTL, command],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except FileNotFoundError:
        return False, f"spacemouse-ctl not found at {SPACEMOUSE_CTL}"
    except Exception as e:
        return False, str(e)


def get_status() -> str:
    """Get current SpaceMouse mode."""
    success, output = run_ctl("status")
    if "LOCAL" in output:
        return "local"
    elif "FORWARD" in output:
        return "forward"
    return "idle"


def get_security_info() -> str:
    """Get security sandbox status."""
    success, output = run_ctl("security")
    return output if success else "Unable to get security info"


class SpaceMouseTray(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        
        self.icons = {
            "idle": svg_to_icon(ICON_IDLE),
            "local": svg_to_icon(ICON_LOCAL),
            "forward": svg_to_icon(ICON_FORWARD_SECURE),
        }
        
        self.status_labels = {
            "idle": "Idle (native apps only)",
            "local": "Local (Onshape)",
            "forward": "Forward (Windows VM) 🔒",
        }
        
        self.setup_menu()
        self.update_status()
        
        # Poll status every 5 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)
        
        self.activated.connect(self.on_activated)
    
    def setup_menu(self):
        self.menu = QMenu()
        
        # Status display (non-clickable)
        self.status_action = QAction("Status: ...")
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        
        self.menu.addSeparator()
        
        # Mode actions
        self.local_action = QAction("🖥️  Local (Onshape)")
        self.local_action.triggered.connect(lambda: self.set_mode("local"))
        self.menu.addAction(self.local_action)
        
        self.forward_action = QAction("🔒  Forward (Windows VM)")
        self.forward_action.triggered.connect(lambda: self.set_mode("forward"))
        self.menu.addAction(self.forward_action)
        
        self.stop_action = QAction("⏹️  Stop")
        self.stop_action.triggered.connect(lambda: self.set_mode("stop"))
        self.menu.addAction(self.stop_action)
        
        self.menu.addSeparator()
        
        # Security info
        security_action = QAction("🛡️  Security Status...")
        security_action.triggered.connect(self.show_security_info)
        self.menu.addAction(security_action)
        
        # View logs
        logs_action = QAction("📋  View Forward Logs...")
        logs_action.triggered.connect(self.view_logs)
        self.menu.addAction(logs_action)
        
        self.menu.addSeparator()
        
        # Quit
        quit_action = QAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        self.menu.addAction(quit_action)
        
        self.setContextMenu(self.menu)
    
    def update_status(self):
        status = get_status()
        self.setIcon(self.icons.get(status, self.icons["idle"]))
        self.status_action.setText(f"Status: {self.status_labels.get(status, 'Unknown')}")
        self.setToolTip(f"SpaceMouse: {self.status_labels.get(status, 'Unknown')}")
        
        # Update checkmarks
        self.local_action.setChecked(status == "local")
        self.forward_action.setChecked(status == "forward")
    
    def set_mode(self, mode: str):
        self.setToolTip(f"SpaceMouse: Switching...")
        success, output = run_ctl(mode)
        
        if not success:
            QMessageBox.warning(
                None, 
                "SpaceMouse Error", 
                f"Failed to switch mode:\n\n{output}"
            )
        
        self.update_status()
    
    def show_security_info(self):
        info = get_security_info()
        QMessageBox.information(
            None,
            "SpaceMouse Security Status",
            f"Sandbox Configuration:\n\n{info}"
        )
    
    def view_logs(self):
        try:
            subprocess.Popen([
                "konsole", "-e", 
                "bash", "-c", 
                "sudo journalctl -u virtualhere-spacemouse -f; read -p 'Press enter to close...'"
            ])
        except FileNotFoundError:
            # Try generic terminal
            try:
                subprocess.Popen([
                    "x-terminal-emulator", "-e",
                    "bash", "-c",
                    "sudo journalctl -u virtualhere-spacemouse -f; read -p 'Press enter to close...'"
                ])
            except:
                QMessageBox.information(
                    None,
                    "View Logs",
                    "Run in terminal:\nsudo journalctl -u virtualhere-spacemouse -f"
                )
    
    def on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click: cycle through modes
            status = get_status()
            if status == "idle":
                self.set_mode("local")
            elif status == "local":
                self.set_mode("forward")
            else:
                self.set_mode("local")


def main():
    if not Path(SPACEMOUSE_CTL).exists():
        print(f"Error: {SPACEMOUSE_CTL} not found")
        print("Run the install script first: sudo ./install-spacemouse-secure.sh")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("SpaceMouse Control")
    
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("Error: System tray not available")
        sys.exit(1)
    
    tray = SpaceMouseTray()
    tray.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
