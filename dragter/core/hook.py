"""Global Drag + Shift gesture detection using Windows low-level state and pynput hooks."""

import ctypes
from typing import Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from pynput import mouse, keyboard

# Windows Virtual Key Codes
VK_LBUTTON = 0x01
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_ALT = 0x12


class POINT(ctypes.Structure):
    _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]


def is_key_down(vk_code: int) -> bool:
    """Directly query Windows hardware key state."""
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)


class GestureSignals(QObject):
    """Qt Signals to safely communicate from background hook threads to UI thread."""
    dragTriggered = pyqtSignal(int, int, bool)   # screen_x, screen_y, is_alt_held
    dragEnded = pyqtSignal(int, int)             # screen_x, screen_y
    hotkeyTriggered = pyqtSignal()               # triggered via shortcut


class GlobalInputHook:
    """
    Monitors global mouse and keyboard events.
    Detects when files are being dragged while holding Shift (or Shift+Alt).
    Uses hardware polling + mouse listener for 100% rock-solid detection.
    """

    def __init__(self, drag_threshold: int = 10):
        self.drag_threshold = drag_threshold
        self.signals = GestureSignals()

        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._poll_timer: Optional[QTimer] = None

        self._shift_pressed = False
        self._ctrl_pressed = False
        self._left_pressed = False
        self._press_x = 0
        self._press_y = 0
        self._current_x = 0
        self._current_y = 0

        self._drag_active = False
        self._enabled = True

    def start(self):
        """Start global mouse and keyboard listeners in background threads + hardware polling."""
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._keyboard_listener.daemon = True
        self._keyboard_listener.start()

        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_move=self._on_move
        )
        self._mouse_listener.daemon = True
        self._mouse_listener.start()

        # Dual-detection: hardware state poll running on Qt UI thread every 20ms
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._hardware_poll)
        self._poll_timer.start(20)

    def stop(self):
        """Stop global listeners and poll timer."""
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    def is_shift_down(self) -> bool:
        """Physical hardware key check is definitive. Clears stuck software flags."""
        hw_down = is_key_down(VK_SHIFT) or is_key_down(0xA0) or is_key_down(0xA1)
        if not hw_down:
            self._shift_pressed = False
            return False
        return True

    def is_left_button_down(self) -> bool:
        """Physical hardware mouse button check."""
        hw_down = is_key_down(VK_LBUTTON)
        if not hw_down:
            self._left_pressed = False
            return False
        return True

    def reset_drag_state(self):
        """Reset drag lock so the wheel can be summoned again cleanly."""
        self._drag_active = False
        self._press_x = 0
        self._press_y = 0
        self._left_pressed = False
        if not is_key_down(VK_SHIFT):
            self._shift_pressed = False

    def _get_cursor_pos(self) -> Tuple[int, int]:
        """Get true physical cursor coordinates from Windows API."""
        try:
            pt = POINT()
            if ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
                return int(pt.x), int(pt.y)
        except Exception:
            pass
        return self._current_x, self._current_y

    def _hardware_poll(self):
        """20ms hardware state poll: triggers ONLY when actually dragging (moved >= threshold) with Shift."""
        if not self._enabled:
            return

        try:
            lbutton = self.is_left_button_down()
            if not lbutton:
                if self._drag_active or self._press_x != 0 or self._press_y != 0:
                    self.reset_drag_state()
                return

            if self._drag_active:
                return

            shift = self.is_shift_down()
            if not shift:
                return

            cur_x, cur_y = self._get_cursor_pos()
            if self._press_x == 0 and self._press_y == 0:
                self._press_x = cur_x
                self._press_y = cur_y
                return

            dx = cur_x - self._press_x
            dy = cur_y - self._press_y
            # NEVER trigger on stationary clicks: require actual mouse movement
            if (dx * dx + dy * dy) >= (self.drag_threshold * self.drag_threshold):
                self._trigger_drag(cur_x, cur_y)
        except Exception:
            pass

    # --- Keyboard Callbacks ---

    def _on_key_press(self, key):
        if not self._enabled:
            return

        try:
            # Shift key pressed while already dragging past threshold: trigger immediately
            if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                self._shift_pressed = True
                if self.is_left_button_down() and not self._drag_active:
                    cur_x, cur_y = self._get_cursor_pos()
                    if self._press_x != 0 or self._press_y != 0:
                        dx = cur_x - self._press_x
                        dy = cur_y - self._press_y
                        if (dx * dx + dy * dy) >= (self.drag_threshold * self.drag_threshold):
                            self._trigger_drag(cur_x, cur_y)
                            return

            if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                self._ctrl_pressed = True

            # Hotkeys: Ctrl + Shift + D OR Alt + D to summon dialer anywhere
            if hasattr(key, 'char') and key.char and key.char.lower() == 'd':
                if (getattr(self, '_ctrl_pressed', False) or is_key_down(VK_CONTROL)) and self.is_shift_down():
                    self.signals.hotkeyTriggered.emit()
                    return
                if is_key_down(VK_ALT):
                    self.signals.hotkeyTriggered.emit()
                    return
        except Exception:
            pass

    def _on_key_release(self, key):
        try:
            if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                self._shift_pressed = False
            if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                self._ctrl_pressed = False
        except Exception:
            pass

    # --- Mouse Callbacks ---

    def _on_click(self, x, y, button, pressed):
        if not self._enabled:
            return

        try:
            if button == mouse.Button.left:
                if pressed:
                    self._left_pressed = True
                    self._press_x = int(x)
                    self._press_y = int(y)
                    # DO NOT trigger on press! A press is a click, not a drag.
                    # Drag is only triggered after moving >= drag_threshold.
                else:
                    self._left_pressed = False
                    was_drag = self._drag_active
                    self.reset_drag_state()
                    if was_drag:
                        self.signals.dragEnded.emit(int(x), int(y))
        except Exception:
            pass

    def _on_move(self, x, y):
        self._current_x = int(x)
        self._current_y = int(y)

        # Trigger instantly on mouse movement if left button + Shift are held and moved >= threshold
        if self._left_pressed and not self._drag_active and self._press_x != 0:
            dx = self._current_x - self._press_x
            dy = self._current_y - self._press_y
            if (dx * dx + dy * dy) >= (self.drag_threshold * self.drag_threshold):
                if self.is_shift_down():
                    self._trigger_drag(self._current_x, self._current_y)

    def _trigger_drag(self, x: int, y: int):
        if self._drag_active:
            return
        self._drag_active = True
        is_alt = is_key_down(VK_ALT)
        self.signals.dragTriggered.emit(int(x), int(y), is_alt)
