import sys
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication

from dragter.ui.radial_window import RadialWindow
from dragter.ui.tray import DragterTray
from dragter.core.hook import GlobalInputHook
from dragter.core.file_info import get_clipboard_file


class DragterApplication:
    """Master application class managing lifecycle and cross-component signals."""

    def __init__(self, sys_argv=None):
        self.app = QApplication.instance() or QApplication(sys_argv or sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Components
        self.radial_window = RadialWindow()
        self.tray = DragterTray()
        self.hook = GlobalInputHook()

        self._connect_signals()

    def _connect_signals(self):
        # 1. Global gesture hook -> Radial Window
        self.hook.signals.dragTriggered.connect(self.on_drag_triggered)
        self.hook.signals.dragEnded.connect(self.on_drag_ended)
        self.hook.signals.hotkeyTriggered.connect(self.summon_wheel_at_cursor)

        # 2. Tray actions
        self.tray.summonWheelRequested.connect(self.summon_wheel_at_cursor)
        self.tray.toggleTriggerRequested.connect(self.hook.set_enabled)

        # 3. Conversion completed -> Notification
        self.radial_window.conversionFinished.connect(self.tray.notify_success)
        self.radial_window.windowHidden.connect(self.hook.reset_drag_state)

    def start(self):
        """Start background input hook, show tray icon, enter Qt event loop."""
        self.hook.start()
        self.tray.show()
        print("[Dragter] Running! Drag any file (or hold Shift) to convert instantly.")
        return self.app.exec()

    def on_drag_triggered(self, x: int, y: int, is_alt_held: bool):
        """Called when drag gesture is detected globally. Spawns HUD with 0ms latency."""
        if not self.radial_window.isVisible():
            clip_file = get_clipboard_file()
            self.radial_window.show_at(x, y, initial_mode="root", file_path=clip_file, is_drag=True)

    def on_drag_ended(self, x: int, y: int):
        """Called when mouse button is released anywhere."""
        self.hook.reset_drag_state()

    def summon_wheel_at_cursor(self):
        """Summon wheel at current mouse cursor with 0ms latency."""
        pos = QCursor.pos()
        clip_file = get_clipboard_file()
        self.radial_window.show_at(pos.x(), pos.y(), initial_mode="root", file_path=clip_file, is_drag=False)
