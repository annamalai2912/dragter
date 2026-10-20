"""System Tray Icon and Desktop Notification Manager."""

import os
from pathlib import Path
from typing import Optional, List
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QBrush, QFont
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication


def create_tray_pixmap() -> QPixmap:
    """Generate a clean amber circular icon with letter 'D' for Dragter."""
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Amber gradient circle
    painter.setBrush(QBrush(QColor(234, 88, 12)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, 28, 28)

    # White 'D' letter
    painter.setPen(QColor(255, 255, 255))
    painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "D")
    painter.end()
    return pix


class DragterTray(QSystemTrayIcon):
    """System tray manager with quick actions and notification dispatch."""
    toggleTriggerRequested = pyqtSignal(bool)
    summonWheelRequested = pyqtSignal()

    def __init__(self, parent=None):
        icon = QIcon(create_tray_pixmap())
        super().__init__(icon, parent)
        self.setToolTip("Dragter - Drag + Shift Instant File Converter")
        
        self.is_hook_enabled = True
        self.last_converted_path: Optional[str] = None
        
        self.setup_menu()
        self.activated.connect(self.on_tray_activated)

    def setup_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background: rgba(255, 255, 255, 0.96);
                border: 1px solid rgba(0, 122, 255, 0.3);
                border-radius: 8px;
                padding: 4px;
                color: #1c1c1e;
                font-family: 'Segoe UI';
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #007aff;
                color: white;
            }
        """)

        # Open Radial Wheel
        act_open = QAction("Open Radial Wheel", self)
        act_open.triggered.connect(self.summonWheelRequested.emit)
        menu.addAction(act_open)

        menu.addSeparator()

        # Toggle hook
        self.act_toggle = QAction("✓ Shift+Drag Hook Active", self)
        self.act_toggle.setCheckable(True)
        self.act_toggle.setChecked(True)
        self.act_toggle.triggered.connect(self.on_toggle_hook)
        menu.addAction(self.act_toggle)

        # Open Last Output
        self.act_last = QAction("Open Last Converted File", self)
        self.act_last.setEnabled(False)
        self.act_last.triggered.connect(self.open_last_file)
        menu.addAction(self.act_last)

        menu.addSeparator()

        # Exit
        act_exit = QAction("Exit Dragter", self)
        act_exit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_exit)

        self.setContextMenu(menu)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.summonWheelRequested.emit()

    def on_toggle_hook(self, checked: bool):
        self.is_hook_enabled = checked
        self.act_toggle.setText("✓ Shift+Drag Hook Active" if checked else "Shift+Drag Hook Paused")
        self.toggleTriggerRequested.emit(checked)

    def notify_success(self, files: List[str]):
        if not files:
            return
        self.last_converted_path = files[0]
        self.act_last.setEnabled(True)
        filename = Path(files[0]).name
        self.showMessage(
            "Conversion Complete",
            f"Successfully converted to {filename}",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def open_last_file(self):
        if self.last_converted_path and Path(self.last_converted_path).exists():
            os.startfile(self.last_converted_path)
