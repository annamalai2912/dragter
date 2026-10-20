"""Sleek dark circular radial launcher HUD matching the multi-ring reference design."""

import math
import random
import threading
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QRadialGradient,
    QLinearGradient, QCursor, QKeyEvent, QPainterPath, QWheelEvent, QFontMetrics
)
from PyQt6.QtWidgets import QWidget, QApplication

from dragter.ui.donut_geometry import DonutGeometry
from dragter.ui.theme import (
    DISC_BG_TOP, DISC_BG_BOT, DISC_BORDER,
    INNER_RING_BG, INNER_RING_BORDER, INNER_ICON_NORMAL, INNER_ICON_HOVER,
    PETAL_BG_TOP, PETAL_BG_BOT, PETAL_BORDER_NORMAL, PETAL_TEXT_NORMAL,
    PETAL_TEXT_HOVER,
    HUB_BG_TOP, HUB_BG_BOT, HUB_BORDER, HUB_TEXT, HUB_SUBTEXT, HUB_ARROW_NORMAL, HUB_ARROW_HOVER,
    SATELLITE_BG, SATELLITE_BORDER, SATELLITE_TEXT, SATELLITE_HOVER_BG, SATELLITE_HOVER_BORDER, SATELLITE_HOVER_TEXT,
    HUB_BG_SUCCESS, HUB_TEXT_SUCCESS, HUB_BG_ERROR,
    FONT_PETAL, FONT_HUB_PAGE, FONT_HUB_SUB,
    FONT_BOLD_7, FONT_BOLD_8, FONT_BOLD_9, FONT_BOLD_10, FONT_BOLD_12,
    FONT_REG_6, FONT_REG_7, FONT_REG_9, FONT_REG_10,
    TOOL_ACCENT_COLORS, FORMAT_ACCENT_COLORS,
    get_tool_icon_pixmap
)
from dragter.core.file_info import get_file_info, get_clipboard_file
from dragter.core.converter import convert_file
from dragter.core.hook import is_key_down, VK_LBUTTON
from dragter.ui.tools import (
    CropDialog, CompressDialog, MetadataDialog,
    RedactDialog, EditDialog, AddBgDialog, AnnotateDialog,
    OcrDialog, PaletteDialog, WatermarkDialog, QrDialog
)

_TEXT_WIDTH_CACHE: Dict[Tuple[str, int, int, str], float] = {}


def get_text_advance(font: QFont, text: str) -> float:
    """Zero-allocation cached text horizontal advance query."""
    key = (font.family(), font.pointSize(), font.weight(), text)
    w = _TEXT_WIDTH_CACHE.get(key)
    if w is None:
        fm = QFontMetrics(font)
        w = _TEXT_WIDTH_CACHE[key] = float(fm.horizontalAdvance(text))
    return w


class SplashParticle:
    """Individual frosted pearl droplet particle spawned during drop splash."""

    def __init__(self, x: float, y: float, angle_rad: float, speed: float, color: QColor):
        self.x = x
        self.y = y
        self.vx = math.cos(angle_rad) * speed + (random.random() - 0.5) * 1.5
        self.vy = math.sin(angle_rad) * speed + (random.random() - 0.5) * 1.5
        self.radius = random.uniform(2.5, 4.8)
        self.color = color
        self.alpha = 240.0
        self.decay = random.uniform(8.0, 13.0)
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.90
        self.vy *= 0.90
        self.alpha -= self.decay
        self.radius = max(1.0, self.radius * 0.95)
        if self.alpha <= 0:
            self.alive = False


class RadialWindow(QWidget):
    """
    Sleek Dark Multi-Ring Radial HUD:
    - Outer Ring: Conversion formats or Quick Tools
    - Inner Ring: 6 utility shortcut buttons (Tools toggle, Explorer, Search, Star, etc.)
    - Center Hub: Page indicator (‹ 1/2 ›) with left/right navigation and file info
    - Satellite Buttons: 4 docked orbit controls (Close, Toggle, Explorer, Copy)
    - Full OLE drag & drop support, mouse wheel pagination, instant responsiveness
    """
    conversionFinished = pyqtSignal(list)
    conversionFailed = pyqtSignal(str)
    windowHidden = pyqtSignal()
    fileResolved = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(660, 600)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

        self.geometry_engine = DonutGeometry(
            hub_radius=56.0,
            inner_ring_r1=62.0,
            inner_ring_r2=95.0,
            outer_ring_r1=100.0,
            outer_ring_r2=175.0,
            disc_radius=186.0,
            sub_ring_r1=182.0,
            sub_ring_r2=265.0,
            center_x=290.0,
            center_y=300.0
        )

        self.file_info: Optional[Dict[str, Any]] = None
        self.hovered_item: Optional[str] = None      # 'slice' | 'satellite' | 'inner' | 'hub_prev' | 'hub_next' | 'center' | 'sub_item'
        self.hovered_index: Optional[int] = None
        self.hovered_sub_index: Optional[int] = None

        # Cascading Radial Sub-Tier state (blooms outward on hover)
        self.active_sub_id: Optional[str] = None
        self.sub_menu_anim: float = 0.0


        # Definitions for sub-option menus displayed in the cascading radial sub-tier
        self.sub_menus = {
            'tools': {
                'title': 'QUICK TOOLS',
                'items': [
                    {'id': 'crop',      'label': 'Crop',      'hint': '1:1, 16:9',        'accent': QColor(245, 158, 11)},
                    {'id': 'compress',  'label': 'Compress',  'hint': 'Reduce size',      'accent': QColor(16, 185, 129)},
                    {'id': 'metadata',  'label': 'Metadata',  'hint': 'EXIF data',        'accent': QColor(148, 163, 184)},
                    {'id': 'edit',      'label': 'Edit',      'hint': 'Adjust photo',     'accent': QColor(203, 213, 225)},
                    {'id': 'annotate',  'label': 'Annotate',  'hint': 'Draw / Notes',     'accent': QColor(168, 85, 247)},
                    {'id': 'add_bg',    'label': 'Add BG',    'hint': 'Backdrops',        'accent': QColor(236, 72, 153)},
                    {'id': 'redact',    'label': 'Redact',    'hint': 'Blackout / Blur',  'accent': QColor(244, 63, 94)},
                    {'id': 'ocr',       'label': 'OCR Text',  'hint': 'Extract text',     'accent': QColor(251, 191, 36)},
                    {'id': 'palette',   'label': 'Palette',   'hint': 'Color swatches',   'accent': QColor(192, 132, 252)},
                    {'id': 'watermark', 'label': 'Watermark', 'hint': 'Stamp / Brand',   'accent': QColor(20, 184, 166)},
                    {'id': 'qr',        'label': 'QR Code',   'hint': 'Scan & Gen',       'accent': QColor(248, 250, 252)},
                ]
            },
            'more': {
                'title': 'MORE FORMATS',
                'items': [
                    {'format': 'HEIC', 'label': 'HEIC', 'hint': 'Apple photo',       'accent': QColor(236, 72, 153)},
                    {'format': 'AVIF', 'label': 'AVIF', 'hint': 'AV1 Web',           'accent': QColor(168, 85, 247)},
                    {'format': 'TIFF', 'label': 'TIFF', 'hint': 'Print quality',      'accent': QColor(20, 184, 166)},
                    {'format': 'BMP',  'label': 'BMP',  'hint': 'Bitmap',            'accent': QColor(244, 63, 94)},
                    {'format': 'ICO',  'label': 'ICO',  'hint': 'App Icon (16-256)', 'accent': QColor(234, 179, 8)},
                    {'format': 'GIF',  'label': 'GIF',  'hint': 'Animated / Web',   'accent': QColor(251, 146, 60)},
                ]
            },
            'jpg': {
                'title': 'JPG / JPEG QUALITY',
                'items': [
                    {'format': 'JPG', 'label': '95% HQ',   'hint': 'Photo quality',  'quality': 95, 'accent': QColor(245, 158, 11)},
                    {'format': 'JPG', 'label': '80% Bal',  'hint': 'Balanced',       'quality': 80, 'accent': QColor(245, 158, 11)},
                    {'format': 'JPG', 'label': '65% Web',  'hint': 'Smallest size',  'quality': 65, 'accent': QColor(245, 158, 11)},
                    {'action': 'grayscale', 'label': 'B&W', 'hint': 'Monochrome',    'accent': QColor(203, 213, 225)},
                ]
            },
            'pdf': {
                'title': 'PDF DOCUMENT',
                'items': [
                    {'format': 'PDF', 'label': 'Standard', 'hint': '150 DPI vector', 'accent': QColor(239, 68, 68)},
                    {'format': 'PDF', 'label': 'Compact',  'hint': 'Screen / Email',  'accent': QColor(239, 68, 68)},
                    {'action': 'pdf_extract', 'label': 'Extract', 'hint': 'Text to TXT', 'accent': QColor(239, 68, 68)},
                    {'action': 'pdf_images',  'label': 'To Imgs', 'hint': 'Pages to PNG', 'accent': QColor(239, 68, 68)},
                ]
            },
            'webp': {
                'title': 'WEBP COMPRESSION',
                'items': [
                    {'format': 'WEBP', 'label': 'Lossless', 'hint': 'Perfect 100%', 'quality': 100, 'accent': QColor(34, 197, 94)},
                    {'format': 'WEBP', 'label': '90% Photo', 'hint': 'High quality', 'quality': 90, 'accent': QColor(34, 197, 94)},
                    {'format': 'WEBP', 'label': '75% Web',   'hint': 'Compressed',   'quality': 75, 'accent': QColor(34, 197, 94)},
                ]
            }
        }

        # Slices state
        self.page_index = 0
        self.primary_wheel_slices = [
            {'label': 'PNG',        'format': 'PNG'},
            {'label': 'JPG / JPEG', 'format': 'JPG',  'sub_id': 'jpg'},
            {'label': 'TOOLS',      'id': 'tools',    'sub_id': 'tools', 'badge': QColor(203, 213, 225)},
            {'label': 'MORE',       'format': 'HEIC', 'sub_id': 'more',  'badge': QColor(168, 85, 247)},
            {'label': 'PDF',        'format': 'PDF',  'sub_id': 'pdf'},
            {'label': 'WEBP',       'format': 'WEBP', 'sub_id': 'webp'},
            {'label': 'DOCX',       'format': 'DOCX'},
            {'label': 'TXT',        'format': 'TXT'},
        ]
        self.format_items = self.primary_wheel_slices
        self.tool_items = self.sub_menus['tools']['items']
        self.active_slices = self.primary_wheel_slices

        # Satellite actions: (tag, label, action_id) — NO emoji symbols, clean typography
        self.satellites = [
            {'tag': 'DIR',  'label': 'Explorer',  'action': 'open_explorer'},
            {'tag': 'COPY', 'label': 'Copy Path', 'action': 'copy_path'},
            {'tag': '✕',    'label': 'Close',     'action': 'close'},
        ]

        # Inner ring shortcuts: 6 clean geometric items
        self.inner_buttons = [
            {'tag': 'TOOLS', 'label': 'Tools',     'action': 'set_tools_page',   'tool_id': 'tools'},
            {'tag': 'EDIT',  'label': 'Edit',      'action': 'open_edit',        'tool_id': 'edit'},
            {'tag': 'QR',    'label': 'QR',        'action': 'open_qr',          'tool_id': 'qr'},
            {'tag': 'DIR',   'label': 'Folder',    'action': 'open_explorer',    'tool_id': ''},
            {'tag': 'CONV',  'label': 'Convert',   'action': 'set_formats_page', 'tool_id': ''},
            {'tag': 'META',  'label': 'Metadata',  'action': 'open_metadata',    'tool_id': 'metadata'},
        ]

        self.is_drag_mode = False
        self.is_converting = False
        self.success_state = False
        self.success_message = ""
        self.error_message = ""

        # Auto-close timer
        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.hide_animated)

        # Thread signals
        self.conversionFinished.connect(self._on_conversion_success)
        self.conversionFailed.connect(self._on_conversion_error)
        self.fileResolved.connect(self._on_file_resolved)

        # Performance & 60 FPS caches
        self._supported_cache: Dict[int, bool] = {}
        self._base_slice_paths: Dict[int, QPainterPath] = {}
        self._last_hover_key: Optional[Tuple[float, float, Optional[str]]] = None
        self._cached_disc_grad: Optional[QRadialGradient] = None
        self._cached_shadow_grad: Optional[QRadialGradient] = None

        # Animation states
        self.time_counter = 0.0
        self.bloom_progress = 0.0
        self.is_blooming = False
        self.mouse_up_counter = 0

        # Liquidify Physics: Slices elastic spring & viscous bulge arrays
        self.slice_glow: List[float] = []
        self.slice_bulge: List[float] = []
        self.slice_vel: List[float] = []

        # Liquidify Physics: Magnetic Ferrofluid Center Hub (pulled towards hovered slice)
        self.hub_offset_x = 0.0
        self.hub_offset_y = 0.0
        self.hub_vel_x = 0.0
        self.hub_vel_y = 0.0

        # Center hub scale animation
        self.hub_scale = 1.0
        self.hub_scale_vel = 0.0

        # Frosted pearl splash particles & shockwave
        self.ripple_radius = 0.0
        self.ripple_alpha = 0.0
        self.particles: List[SplashParticle] = []

        # 60 FPS update loop
        self.physics_timer = QTimer(self)
        self.physics_timer.timeout.connect(self.physics_tick)
        self.physics_timer.start(16)

    def show_at(self, screen_x: int, screen_y: int, initial_mode: str = "root", file_path: Optional[str] = None, is_drag: bool = True):
        """Spawn HUD centered at cursor."""
        self.is_drag_mode = is_drag
        self.is_converting = False
        self.success_state = False
        self.success_message = ""
        self.error_message = ""
        self.hovered_item = None
        self.hovered_index = None
        self.page_index = 0
        self.particles.clear()
        self.ripple_alpha = 0.0
        self.mouse_up_counter = -15

        if file_path:
            self.set_file(file_path)
        else:
            self.load_pages([], [])

        screen = QApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0

        cursor_pos = QCursor.pos()
        target_x = cursor_pos.x()
        target_y = cursor_pos.y()
        if target_x == 0 and target_y == 0 and (screen_x != 0 or screen_y != 0):
            if dpr > 1.01:
                target_x = int(screen_x / dpr)
                target_y = int(screen_y / dpr)
            else:
                target_x = screen_x
                target_y = screen_y

        # Center HUD directly around cursor
        win_x = int(target_x - self.geometry_engine.center_x)
        win_y = int(target_y - self.geometry_engine.center_y)

        if screen:
            geom = screen.availableGeometry()
            win_x = max(geom.left(), min(win_x, geom.right() - self.width()))
            win_y = max(geom.top(), min(win_y, geom.bottom() - self.height()))

        self.move(win_x, win_y)
        self.show()

        # Snappy entrance bloom
        self.is_blooming = True
        self.bloom_progress = 0.4
        self.hub_scale = 0.7
        self.hub_scale_vel = 0.12

        self._refresh_slice_state()

        # Keep topmost without stealing keyboard focus from drag origin
        try:
            import ctypes
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0053)
        except Exception:
            self.raise_()

    def hide_animated(self):
        self.hide()
        self.success_state = False
        self.is_converting = False
        self.particles.clear()
        self.windowHidden.emit()

    def _on_file_resolved(self, file_path: str):
        """Called when Explorer selection is resolved asynchronously on background thread."""
        if self.isVisible() and not self.file_info and Path(file_path).exists():
            self.set_file(file_path)

    def set_file(self, file_path: str):
        self._supported_cache.clear()
        self._base_slice_paths.clear()
        self.file_info = get_file_info(file_path)
        hierarchy = self.file_info.get('hierarchy', {})
        formats = hierarchy.get('format_items', [])
        tools = hierarchy.get('tool_items', [])
        self.load_pages(formats, tools)

    def load_pages(self, formats: List[Any], tools: List[Any]):
        self.primary_wheel_slices = [
            {'label': 'PNG',        'format': 'PNG'},
            {'label': 'JPG / JPEG', 'format': 'JPG',  'sub_id': 'jpg'},
            {'label': 'TOOLS',      'id': 'tools',    'sub_id': 'tools', 'badge': QColor(203, 213, 225)},
            {'label': 'MORE',       'format': 'HEIC', 'sub_id': 'more',  'badge': QColor(168, 85, 247)},
            {'label': 'PDF',        'format': 'PDF',  'sub_id': 'pdf'},
            {'label': 'WEBP',       'format': 'WEBP', 'sub_id': 'webp'},
            {'label': 'DOCX',       'format': 'DOCX'},
            {'label': 'TXT',        'format': 'TXT'},
        ]
        self.format_items = self.primary_wheel_slices
        self.tool_items = self.sub_menus['tools']['items']
        self.set_page(self.page_index)

    def set_page(self, page_idx: int):
        self._base_slice_paths.clear()
        self._supported_cache.clear()
        self.page_index = page_idx % 2
        self.active_slices = self.primary_wheel_slices if self.page_index == 0 else self.tool_items
        self.hovered_index = None
        self.hovered_sub_index = None
        self._refresh_slice_state()
        self.update()

    def toggle_page(self):
        self.set_page(self.page_index + 1)
        self.trigger_drop_splash(self.geometry_engine.center_x, self.geometry_engine.center_y)

    def _refresh_slice_state(self):
        num = len(self.active_slices)
        self.slice_glow = [0.0] * num
        self.slice_bulge = [0.0] * num
        self.slice_vel = [0.0] * num

    def is_item_supported(self, item: Any) -> bool:
        """
        Dynamically determine whether a format slice, sub-option, or tool is supported
        for the currently identified file type. Results are cached per file.
        """
        if not self.file_info or not self.file_info.get('path'):
            return True

        k = id(item)
        if k in self._supported_cache:
            return self._supported_cache[k]

        res = self._check_item_supported(item)
        self._supported_cache[k] = res
        return res

    def _check_item_supported(self, item: Any) -> bool:
        ext = self.file_info.get('ext', '').lower()
        category = self.file_info.get('category', 'generic')

        item_id = item.get('id') if isinstance(item, dict) else None
        item_fmt = (item.get('format') or item.get('label', '')).upper() if isinstance(item, dict) else str(item).upper()
        action = item.get('action') if isinstance(item, dict) else None
        sub_id = item.get('sub_id') if isinstance(item, dict) else None

        # 1. Tool support check
        if item_id:
            if item_id in ('qr', 'tools'):
                return True  # QR and Tools are universal
            if item_id in ('crop', 'edit', 'add_bg', 'palette', 'watermark'):
                return category == 'image'
            if item_id in ('annotate', 'redact'):
                return category in ('image', 'pdf')
            if item_id == 'compress':
                return category in ('image', 'pdf')
            if item_id == 'metadata':
                return category in ('image', 'pdf', 'docx')
            if item_id == 'ocr':
                return True

        # 2. Custom action support check
        if action:
            if action in ('pdf_extract', 'pdf_images'):
                return category == 'pdf'
            if action == 'grayscale':
                return category == 'image'

        # 3. Cascading radial sub-tier parent slice check
        if sub_id == 'tools':
            return True
        if sub_id == 'more':
            return category in ('image', 'pdf')
        if sub_id == 'jpg':
            return category in ('image', 'pdf', 'docx')
        if sub_id == 'pdf':
            return True
        if sub_id == 'webp':
            return category in ('image', 'pdf', 'docx')

        # 4. Conversion target format check
        clean_ext = ext.lstrip('.').upper()
        if clean_ext in ('JPG', 'JPEG') and item_fmt in ('JPG', 'JPEG'):
            return False
        if clean_ext and clean_ext == item_fmt:
            return False

        if item_fmt in ('PNG', 'JPG', 'JPEG', 'WEBP', 'BMP', 'TIFF', 'HEIC', 'AVIF', 'ICO', 'GIF'):
            if category == 'txt':
                return False
            return True

        if item_fmt == 'PDF':
            return True

        if item_fmt == 'DOCX':
            return True

        if item_fmt == 'TXT':
            if category == 'image':
                return False
            return True

        return True

    def wheelEvent(self, event: QWheelEvent):
        """Scroll wheel flips between Formats and Tools effortlessly."""
        if event.angleDelta().y() != 0:
            self.toggle_page()
            event.accept()

    # --- 60 FPS Physics & State Tick ---

    def physics_tick(self):
        if not self.isVisible():
            return
        self.time_counter += 0.04
        need_repaint = False

        # Distance-based auto-dismissal when dragged away (generous 580px radius to allow side sub-menu exploration)
        if self.isVisible() and self.is_drag_mode and not self.success_state and not self.is_converting:
            cursor_pos = QCursor.pos()
            center_x = self.x() + self.geometry_engine.center_x
            center_y = self.y() + self.geometry_engine.center_y
            dist = math.hypot(cursor_pos.x() - center_x, cursor_pos.y() - center_y)
            if dist > 580.0:
                self.hide_animated()
                return

            local_x = cursor_pos.x() - self.x()
            local_y = cursor_pos.y() - self.y()
            if 0 <= local_x <= self.width() and 0 <= local_y <= self.height():
                self._handle_hover(local_x, local_y)

            if not is_key_down(VK_LBUTTON):
                self.mouse_up_counter += 1
                if self.mouse_up_counter == 1:
                    # Mouse release drop fallback
                    self._handle_interaction_at_cursor()
                elif self.mouse_up_counter > 120:
                    self.hide_animated()
                    return
            else:
                self.mouse_up_counter = 0

        # Sub-Menu Animation (smooth fade in/out)
        if self.active_sub_id:
            if self.sub_menu_anim < 1.0:
                self.sub_menu_anim = min(1.0, self.sub_menu_anim + 0.16)
                need_repaint = True
        else:
            if self.sub_menu_anim > 0.0:
                self.sub_menu_anim = max(0.0, self.sub_menu_anim - 0.20)
                need_repaint = True

        # Entrance Bloom
        if self.is_blooming:
            self.bloom_progress += (1.0 - self.bloom_progress) * 0.28 + 0.02
            if self.bloom_progress >= 0.99:
                self.bloom_progress = 1.0
                self.is_blooming = False
            need_repaint = True

        # Liquidify Physics: Slices elastic spring & viscous neighbor drag
        num = len(self.active_slices)
        while len(self.slice_glow) < num:
            self.slice_glow.append(0.0)
            self.slice_bulge.append(0.0)
            self.slice_vel.append(0.0)

        hover_idx = self.hovered_index if self.hovered_item == 'slice' else None
        is_hover_supp = bool(hover_idx is not None and 0 <= hover_idx < num and self.is_item_supported(self.active_slices[hover_idx]))

        for i in range(num):
            is_supp = self.is_item_supported(self.active_slices[i])
            # Target glow: only if supported
            t_glow = 1.0 if (i == hover_idx and is_supp) else 0.0
            g_diff = t_glow - self.slice_glow[i]
            if abs(g_diff) > 0.02:
                self.slice_glow[i] += g_diff * 0.28
                need_repaint = True
            else:
                self.slice_glow[i] = t_glow

            # Authentic viscous surface tension coupling (only if hovered slice is supported)
            if hover_idx is not None and is_hover_supp and is_supp:
                d_idx = min(abs(i - hover_idx), num - abs(i - hover_idx))
                if d_idx == 0:
                    t_bulge = 16.0  # primary hover bulge
                elif d_idx == 1:
                    t_bulge = 7.0   # immediate neighbor viscous drag
                elif d_idx == 2:
                    t_bulge = 2.0   # secondary neighbor drag
                else:
                    t_bulge = -1.2  # subtle volume conservation compression
            else:
                t_bulge = 0.0

            # Damped spring oscillator for organic elastic response
            f_bulge = (t_bulge - self.slice_bulge[i]) * 0.26 - self.slice_vel[i] * 0.38
            self.slice_vel[i] += f_bulge
            self.slice_bulge[i] += self.slice_vel[i]
            if abs(self.slice_vel[i]) > 0.02 or abs(t_bulge - self.slice_bulge[i]) > 0.05:
                need_repaint = True

        # Liquidify Physics: Magnetic Ferrofluid Center Hub (pulled towards hovered slice ONLY if supported)
        if hover_idx is not None and num > 0 and is_hover_supp:
            slice_span = 360.0 / num
            mid_a_rad = math.radians(-90.0 + hover_idx * slice_span)
            target_hx = math.cos(mid_a_rad) * 7.5
            target_hy = math.sin(mid_a_rad) * 7.5
        else:
            target_hx = 0.0
            target_hy = 0.0

        f_hx = (target_hx - self.hub_offset_x) * 0.22 - self.hub_vel_x * 0.40
        f_hy = (target_hy - self.hub_offset_y) * 0.22 - self.hub_vel_y * 0.40
        self.hub_vel_x += f_hx
        self.hub_vel_y += f_hy
        self.hub_offset_x += self.hub_vel_x
        self.hub_offset_y += self.hub_vel_y
        if abs(self.hub_vel_x) > 0.02 or abs(self.hub_vel_y) > 0.02 or abs(target_hx - self.hub_offset_x) > 0.05:
            need_repaint = True

        # Hub scale spring
        target_scale = 1.15 if self.success_state else (1.05 if self.hovered_item in ('center', 'hub_prev', 'hub_next') else 1.0)
        f_scale = (target_scale - self.hub_scale) * 0.35
        self.hub_scale_vel = (self.hub_scale_vel + f_scale) * 0.70
        self.hub_scale += self.hub_scale_vel
        if abs(self.hub_scale_vel) > 0.01:
            need_repaint = True

        # Droplet particles
        if self.particles:
            for p in self.particles:
                p.update()
            self.particles = [p for p in self.particles if p.alive]
            need_repaint = True

        if self.ripple_alpha > 0:
            self.ripple_radius += 8.5
            self.ripple_alpha -= 10.0
            need_repaint = True

        if self.isVisible() and need_repaint:
            self.update()

    def trigger_drop_splash(self, drop_x: float, drop_y: float):
        self.ripple_radius = 24.0
        self.ripple_alpha = 220.0
        self.hub_scale = 0.88
        self.hub_scale_vel = 0.18

        for _ in range(16):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3.5, 8.5)
            # Frosted pearl white & platinum droplets (NO glowing cyan/blue)
            color = QColor(255, 255, 255) if random.random() > 0.35 else QColor(220, 228, 240)
            self.particles.append(SplashParticle(drop_x, drop_y, angle, speed, color))

    # --- Windows OLE Drag & Drop Handling ---

    def _accept_drag_event(self, event):
        proposed = event.proposedAction()
        possible = event.possibleActions()
        if proposed != Qt.DropAction.IgnoreAction and (proposed & possible):
            event.setDropAction(proposed)
            event.accept()
        elif possible & Qt.DropAction.MoveAction:
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        elif possible & Qt.DropAction.CopyAction:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.acceptProposedAction()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if path and Path(path).exists():
                    self.set_file(path)
        self._accept_drag_event(event)

    def _handle_hover(self, px: float, py: float):
        hover_key = (round(px, 1), round(py, 1), self.active_sub_id)
        if self._last_hover_key == hover_key:
            return
        self._last_hover_key = hover_key

        sub_count = len(self.sub_menus[self.active_sub_id]['items']) if (self.active_sub_id and self.active_sub_id in self.sub_menus) else 0
        item_type, idx = self.geometry_engine.hit_test(
            px, py, len(self.active_slices),
            active_sub_id=self.active_sub_id if self.sub_menu_anim > 0.05 else None,
            sub_items_count=sub_count
        )

        if item_type == 'sub_bridge':
            # Cursor is traveling between slice and outer arc tier - preserve sub-menu
            return

        if item_type == 'sub_item':
            if self.hovered_item != 'sub_item' or self.hovered_sub_index != idx:
                self.hovered_item = 'sub_item'
                self.hovered_index = idx
                self.hovered_sub_index = idx
                self.update()
            if idx is not None and self.active_sub_id:
                sub_items = self.sub_menus[self.active_sub_id]['items']
                if 0 <= idx < len(sub_items) and not self.is_item_supported(sub_items[idx]):
                    target_cursor = Qt.CursorShape.ForbiddenCursor
                else:
                    target_cursor = Qt.CursorShape.PointingHandCursor
                if self.cursor().shape() != target_cursor:
                    self.setCursor(target_cursor)
            return

        # Cursor is on the wheel or background
        self.hovered_sub_index = None

        if item_type == 'slice' and idx is not None and 0 <= idx < len(self.active_slices):
            slice_item = self.active_slices[idx]
            sub_id = slice_item.get('sub_id')
            if sub_id and self.is_item_supported(slice_item):
                if self.active_sub_id != sub_id:
                    self.active_sub_id = sub_id
                    self.sub_menu_anim = 0.0  # trigger bloom animation
            else:
                self.active_sub_id = None
        elif item_type == 'inner' and idx is not None and 0 <= idx < len(self.inner_buttons):
            inner_item = self.inner_buttons[idx]
            if inner_item['action'] == 'set_tools_page':
                if self.active_sub_id != 'tools':
                    self.active_sub_id = 'tools'
                    self.sub_menu_anim = 0.0
            elif inner_item['action'] == 'set_formats_page':
                if self.active_sub_id != 'more':
                    self.active_sub_id = 'more'
                    self.sub_menu_anim = 0.0
        elif item_type not in ('slice', 'sub_item', 'sub_bridge'):
            if item_type is None:
                cx = self.geometry_engine.center_x
                cy = self.geometry_engine.center_y
                dist = math.hypot(px - cx, py - cy)
                if dist < self.geometry_engine.inner_radius or dist > self.geometry_engine.sub_ring_r2 + 35.0:
                    self.active_sub_id = None

        # Update cursor shape based on hovered element support (ONLY when shape changed)
        if item_type == 'slice' and idx is not None and 0 <= idx < len(self.active_slices):
            if not self.is_item_supported(self.active_slices[idx]):
                target_cursor = Qt.CursorShape.ForbiddenCursor
            else:
                target_cursor = Qt.CursorShape.PointingHandCursor
        elif item_type in ('satellite', 'inner', 'hub_prev', 'hub_next', 'center'):
            target_cursor = Qt.CursorShape.PointingHandCursor
        else:
            target_cursor = Qt.CursorShape.ArrowCursor

        if self.cursor().shape() != target_cursor:
            self.setCursor(target_cursor)

        if item_type != self.hovered_item or idx != self.hovered_index:
            self.hovered_item = item_type
            self.hovered_index = idx
            self.update()

    def dragMoveEvent(self, event):
        pos = event.position()
        self._handle_hover(pos.x(), pos.y())
        self._accept_drag_event(event)

    def dragLeaveEvent(self, event):
        self.hovered_item = None
        self.hovered_index = None
        self.hovered_sub_index = None
        self.update()

    def dropEvent(self, event):
        self._accept_drag_event(event)
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if path and Path(path).exists() and not self.file_info:
                    self.set_file(path)

        pos = event.position()
        self._execute_hit(pos.x(), pos.y())

    # --- Mouse Handling (Click mode) ---

    def mouseMoveEvent(self, event):
        pos = event.position()
        self._handle_hover(pos.x(), pos.y())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            self._execute_hit(pos.x(), pos.y())

    def _handle_interaction_at_cursor(self):
        cursor = self.mapFromGlobal(QCursor.pos())
        self._execute_hit(cursor.x(), cursor.y())

    def _execute_hit(self, px: float, py: float):
        sub_count = len(self.sub_menus[self.active_sub_id]['items']) if (self.active_sub_id and self.active_sub_id in self.sub_menus) else 0
        item_type, idx = self.geometry_engine.hit_test(
            px, py, len(self.active_slices),
            active_sub_id=self.active_sub_id if self.sub_menu_anim > 0.05 else None,
            sub_items_count=sub_count
        )

        file_path = self.file_info['path'] if self.file_info else None
        if not file_path:
            file_path = get_clipboard_file()
            if file_path:
                self.set_file(file_path)

        # 1. Dropped on a Sub-Menu Item in the side panel
        if item_type == 'sub_item' and idx is not None and self.active_sub_id:
            sub_item = self.sub_menus[self.active_sub_id]['items'][idx]
            if not self.is_item_supported(sub_item):
                self._show_unsupported_feedback(sub_item)
                return
            self.trigger_drop_splash(px, py)
            if not file_path:
                from PyQt6.QtWidgets import QFileDialog
                picked, _ = QFileDialog.getOpenFileName(self, "Select file", "", "All Files (*.*)")
                if picked and Path(picked).exists():
                    self.set_file(picked)
                    file_path = picked
                else:
                    self.hide_animated()
                    return
            self.execute_action(sub_item, file_path)
            return

        # 1b. Dropped in bridge corridor with active sub-menu
        if item_type == 'sub_bridge' and self.active_sub_id:
            sub_items = self.sub_menus[self.active_sub_id]['items']
            if sub_items and self.is_item_supported(sub_items[0]):
                self.trigger_drop_splash(px, py)
                if not file_path:
                    from PyQt6.QtWidgets import QFileDialog
                    picked, _ = QFileDialog.getOpenFileName(self, "Select file", "", "All Files (*.*)")
                    if picked and Path(picked).exists():
                        self.set_file(picked)
                        file_path = picked
                    else:
                        self.hide_animated()
                        return
                self.execute_action(sub_items[0], file_path)
                return

        # 2. Dropped on Satellite button
        if item_type == 'satellite' and idx is not None and 0 <= idx < len(self.satellites):
            action = self.satellites[idx]['action']
            self.trigger_drop_splash(px, py)
            self._execute_satellite_action(action)
            return

        # 3. Hub Navigation
        if item_type in ('hub_prev', 'hub_next', 'center'):
            self.toggle_page()
            return

        # 4. Inner Ring Buttons
        if item_type == 'inner' and idx is not None and 0 <= idx < len(self.inner_buttons):
            action = self.inner_buttons[idx]['action']
            self.trigger_drop_splash(px, py)
            self._execute_inner_action(action)
            return

        # 5. Dropped directly on a Slice
        if item_type == 'slice' and idx is not None and 0 <= idx < len(self.active_slices):
            slice_item = self.active_slices[idx]
            if not self.is_item_supported(slice_item):
                self._show_unsupported_feedback(slice_item)
                return
            self.trigger_drop_splash(px, py)
            if not file_path:
                from PyQt6.QtWidgets import QFileDialog
                picked, _ = QFileDialog.getOpenFileName(self, "Select file", "", "All Files (*.*)")
                if picked and Path(picked).exists():
                    self.set_file(picked)
                    file_path = picked
                else:
                    self.hide_animated()
                    return
            self.execute_action(slice_item, file_path)
            return

        # Outside click
        if item_type is None:
            self.hide_animated()

    def _show_unsupported_feedback(self, item: Any):
        ext = self.file_info['ext'].upper() if self.file_info else ""
        label = item.get('label', '') if isinstance(item, dict) else str(item)
        self.error_message = f"{label[:12]}\nUnsupported for {ext}"
        self.trigger_drop_splash(self.geometry_engine.center_x, self.geometry_engine.center_y)
        QTimer.singleShot(1600, self._clear_error_message)
        self.update()

    def _clear_error_message(self):
        self.error_message = ""
        self.update()

    def _execute_satellite_action(self, action: str):
        if action == 'close':
            self.hide_animated()
        elif action == 'open_explorer':
            self._open_in_explorer()
        elif action == 'copy_path':
            if self.file_info:
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setText(self.file_info['path'])
                self.success_state = True
                self.success_message = "Path Copied!"
                self.update()
                self.auto_close_timer.stop()
                self.auto_close_timer.start(1200)
                self.update()
                self.auto_close_timer.start(1200)

    def _execute_inner_action(self, action: str):
        if action == 'set_tools_page':
            self.set_page(1)
        elif action == 'set_formats_page':
            self.set_page(0)
        elif action == 'open_edit':
            if self.file_info:
                self.hide()
                EditDialog(self.file_info['path']).exec()
        elif action == 'open_metadata':
            if self.file_info:
                self.hide()
                MetadataDialog(self.file_info['path']).exec()
        elif action == 'open_qr':
            self.hide()
            file_path = self.file_info['path'] if self.file_info else None
            QrDialog(file_path).exec()
        elif action == 'open_explorer':
            self._open_in_explorer()
        elif action == 'recent':
            self.toggle_page()

    def _open_in_explorer(self):
        if self.file_info and Path(self.file_info['path']).exists():
            path_str = str(Path(self.file_info['path']).resolve())
            subprocess.Popen(f'explorer.exe /select,"{path_str}"')
            self.hide_animated()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_animated()
        elif event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Left, Qt.Key.Key_Right):
            self.toggle_page()
        else:
            super().keyPressEvent(event)

    # --- Action Execution ---

    def execute_action(self, selected_item: Any, file_path: str):
        target_fmt = None
        is_tool = False
        tool_id = None
        action = None
        quality = None

        if isinstance(selected_item, dict):
            action = selected_item.get('action')
            quality = selected_item.get('quality')
            if 'id' in selected_item:
                is_tool = True
                tool_id = selected_item['id']
            elif 'format' in selected_item and selected_item['format']:
                target_fmt = selected_item['format']
            elif not action:
                target_fmt = selected_item.get('label')
        else:
            target_fmt = str(selected_item)

        # 1. Custom Action Handlers
        if action:
            self.hide()
            if action == 'pdf_extract':
                OcrDialog(file_path).exec()
                return
            elif action == 'pdf_images':
                self.is_converting = True
                self.show()
                def worker_pdf():
                    try:
                        from dragter.core.converter import convert_pdf_to_images
                        src = Path(file_path)
                        created = convert_pdf_to_images(src, 'PNG', src.parent)
                        self.conversionFinished.emit([str(p) for p in created])
                    except Exception as e:
                        self.conversionFailed.emit(str(e))
                threading.Thread(target=worker_pdf, daemon=True).start()
                return
            elif action == 'grayscale':
                self.is_converting = True
                self.show()
                def worker_gray():
                    try:
                        from PIL import Image
                        from dragter.core.converter import get_unique_output_path
                        src = Path(file_path)
                        with Image.open(src) as img:
                            bw = img.convert('L')
                            dest = get_unique_output_path(src.parent / f"{src.stem}_bw{src.suffix}")
                            bw.save(dest)
                            self.conversionFinished.emit([str(dest)])
                    except Exception as e:
                        self.conversionFailed.emit(str(e))
                threading.Thread(target=worker_gray, daemon=True).start()
                return

        # 2. Tool Dialogs
        if is_tool:
            if tool_id == 'tools':
                self.show()
                self.set_page(1)
                return
            self.hide()
            if tool_id == 'crop':
                CropDialog(file_path).exec()
            elif tool_id == 'compress':
                CompressDialog(file_path).exec()
            elif tool_id == 'metadata':
                MetadataDialog(file_path).exec()
            elif tool_id == 'redact':
                RedactDialog(file_path).exec()
            elif tool_id == 'edit':
                EditDialog(file_path).exec()
            elif tool_id == 'add_bg':
                AddBgDialog(file_path).exec()
            elif tool_id == 'annotate':
                AnnotateDialog(file_path).exec()
            elif tool_id == 'ocr':
                OcrDialog(file_path).exec()
            elif tool_id == 'palette':
                PaletteDialog(file_path).exec()
            elif tool_id == 'watermark':
                WatermarkDialog(file_path).exec()
            elif tool_id == 'qr':
                QrDialog(file_path).exec()
            return

        # 3. Format Conversions
        if target_fmt:
            self.is_converting = True
            self.error_message = ""
            self.update()

            def worker():
                try:
                    if quality and target_fmt in ('JPG', 'JPEG', 'WEBP'):
                        from PIL import Image
                        from dragter.core.converter import get_unique_output_path
                        src = Path(file_path)
                        ext = '.jpg' if target_fmt in ('JPG', 'JPEG') else '.webp'
                        dest = get_unique_output_path(src.parent / f"{src.stem}_{quality}q{ext}")
                        with Image.open(src) as img:
                            if target_fmt in ('JPG', 'JPEG'):
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    bg = Image.new('RGB', img.size, (255, 255, 255))
                                    bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                                    bg.save(dest, 'JPEG', quality=quality, optimize=True)
                                else:
                                    img.convert('RGB').save(dest, 'JPEG', quality=quality, optimize=True)
                            else:
                                img.save(dest, 'WEBP', quality=quality, lossless=(quality == 100))
                        self.conversionFinished.emit([str(dest)])
                    else:
                        created = convert_file(file_path, target_fmt)
                        self.conversionFinished.emit(created)
                except Exception as e:
                    self.conversionFailed.emit(str(e))

            threading.Thread(target=worker, daemon=True).start()

    def _on_conversion_success(self, created: list):
        self.is_converting = False
        self.success_state = True
        if created:
            self.success_message = f"Saved: {Path(created[0]).name}"
        self.update()
        self.auto_close_timer.stop()
        self.auto_close_timer.start(1300)

    def _on_conversion_error(self, err_msg: str):
        self.is_converting = False
        self.error_message = f"Error: {err_msg[:24]}" if len(err_msg) > 24 else f"Error: {err_msg}"
        self.update()
        self.auto_close_timer.stop()
        self.auto_close_timer.start(2400)

    # --- Painting (Dark Launcher Glass Design matching reference) ---

    # --- Painting (Executive Dark Titanium Frosted Glass HUD) ---

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.geometry_engine.center_x
        cy = self.geometry_engine.center_y
        scale = self.bloom_progress

        # 1. Natural Ambient Occlusion Shadow (Soft drop shadow, NO neon glow)
        disc_r = self.geometry_engine.disc_radius * scale
        shadow_r = disc_r + 28.0
        if scale >= 0.99:
            if not self._cached_shadow_grad:
                self._cached_shadow_grad = QRadialGradient(cx, cy, shadow_r)
                self._cached_shadow_grad.setColorAt(0.70, QColor(0, 0, 0, 85))
                self._cached_shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            shadow_grad = self._cached_shadow_grad
        else:
            shadow_grad = QRadialGradient(cx, cy, shadow_r)
            shadow_grad.setColorAt(0.70, QColor(0, 0, 0, 85))
            shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(QRectF(cx - shadow_r, cy - shadow_r, shadow_r * 2, shadow_r * 2), QBrush(shadow_grad))

        # 2. Main Dark Obsidian Container Disc (Dark titanium satin matte)
        disc_rect = QRectF(cx - disc_r, cy - disc_r, disc_r * 2, disc_r * 2)
        if scale >= 0.99:
            if not self._cached_disc_grad:
                self._cached_disc_grad = QRadialGradient(cx, cy, disc_r)
                self._cached_disc_grad.setColorAt(0.0, DISC_BG_TOP)
                self._cached_disc_grad.setColorAt(0.82, DISC_BG_TOP)
                self._cached_disc_grad.setColorAt(1.0, DISC_BG_BOT)
            disc_grad = self._cached_disc_grad
        else:
            disc_grad = QRadialGradient(cx, cy, disc_r)
            disc_grad.setColorAt(0.0, DISC_BG_TOP)
            disc_grad.setColorAt(0.82, DISC_BG_TOP)
            disc_grad.setColorAt(1.0, DISC_BG_BOT)
        painter.setBrush(QBrush(disc_grad))
        painter.setPen(QPen(DISC_BORDER, 1.8))
        painter.drawEllipse(disc_rect)

        # 3. Outer Slices (Format or Tool tiles with Liquid Surface Tension)
        num_slices = len(self.active_slices)
        for i in range(num_slices):
            glow = self.slice_glow[i] if i < len(self.slice_glow) else 0.0
            bulge = self.slice_bulge[i] if i < len(self.slice_bulge) else 0.0

            if scale >= 0.99 and abs(bulge) < 0.1 and glow < 0.01:
                path = self._base_slice_paths.get(i)
                if path is None:
                    path = self.geometry_engine.get_liquid_slice_path(
                        index=i,
                        total_slices=num_slices,
                        bulge_r=0.0,
                        stretch_angle_deg=0.0,
                        gap_angle_deg=3.5,
                        wobble=0.0,
                        scale=1.0,
                        corner_r=10.0
                    )
                    self._base_slice_paths[i] = path
            else:
                wobble = math.sin(self.time_counter * 2.8 + i * (2 * math.pi / max(1, num_slices))) * 0.8 if glow > 0.01 else 0.0
                path = self.geometry_engine.get_liquid_slice_path(
                    index=i,
                    total_slices=num_slices,
                    bulge_r=bulge,
                    stretch_angle_deg=0.0,
                    gap_angle_deg=3.5,
                    wobble=wobble,
                    scale=scale,
                    corner_r=10.0
                )

            mid_pt = self.geometry_engine.get_slice_center_point(
                i, num_slices, bulge, scale
            )

            item = self.active_slices[i]
            item_id = item.get('id', '') if isinstance(item, dict) else ''
            item_fmt = item.get('format', '') if isinstance(item, dict) else str(item)

            is_supported = self.is_item_supported(item)
            is_parent_active = bool(self.active_sub_id and isinstance(item, dict) and item.get('sub_id') == self.active_sub_id)

            if not is_supported:
                # Dimmed, faded-out titanium style for unsupported feature
                grad = QLinearGradient(mid_pt.x(), mid_pt.y() - 30, mid_pt.x(), mid_pt.y() + 30)
                grad.setColorAt(0.0, QColor(18, 20, 26, 40))
                grad.setColorAt(1.0, QColor(10, 12, 16, 50))
                painter.setBrush(QBrush(grad))
                painter.setPen(QPen(QColor(255, 255, 255, 12), 1.0, Qt.PenStyle.DashLine))
                painter.drawPath(path)

                # Muted Content (clean typography, no emojis)
                label = item.get('label', '') if isinstance(item, dict) else str(item)
                muted_text = QColor(100, 116, 139, 65)

                tool_icon = get_tool_icon_pixmap(item_id, size=18) if item_id else None
                if tool_icon and not tool_icon.isNull():
                    painter.setOpacity(0.25)
                    painter.drawPixmap(int(mid_pt.x() - tool_icon.width() / 2), int(mid_pt.y() - 17 - tool_icon.height() / 2), tool_icon)
                    painter.setOpacity(1.0)
                else:
                    painter.setBrush(QBrush(QColor(100, 116, 139, 45)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(QPointF(mid_pt.x(), mid_pt.y() - 14), 3.0, 3.0)

                if len(label) > 6:
                    font = FONT_REG_9
                elif len(label) > 4:
                    font = FONT_REG_10
                else:
                    font = FONT_PETAL
                painter.setFont(font)
                painter.setPen(muted_text)
                tw = get_text_advance(font, label)
                painter.drawText(QPointF(mid_pt.x() - tw / 2, mid_pt.y() + 6), label)
                continue

            if glow > 0.01 or is_parent_active:
                # Frosted Platinum Glass Specular Sheen (NO CYAN, NO GLOWING BLUE)
                alpha_f = max(glow, 0.85 if is_parent_active else 0.0)
                grad = QLinearGradient(mid_pt.x() - 25, mid_pt.y() - 25, mid_pt.x() + 25, mid_pt.y() + 25)
                grad.setColorAt(0.0, QColor(255, 255, 255, int(52 * alpha_f)))
                grad.setColorAt(1.0, QColor(255, 255, 255, int(18 * alpha_f)))
                painter.setBrush(QBrush(grad))
                painter.setPen(QPen(QColor(255, 255, 255, int(175 * alpha_f)), 1.8))
            else:
                # Brushed Dark Titanium Slate
                grad = QLinearGradient(mid_pt.x(), mid_pt.y() - 30, mid_pt.x(), mid_pt.y() + 30)
                grad.setColorAt(0.0, PETAL_BG_TOP)
                grad.setColorAt(1.0, PETAL_BG_BOT)
                painter.setBrush(QBrush(grad))
                painter.setPen(QPen(PETAL_BORDER_NORMAL, 1.2))

            painter.drawPath(path)

            # Draw Item Content: Real Tool Icon or Accent pip dot + clean bold label (NO emoji symbols)
            label = item.get('label', '') if isinstance(item, dict) else str(item)
            text_color = PETAL_TEXT_HOVER if (glow > 0.5 or is_parent_active) else PETAL_TEXT_NORMAL

            tool_icon = get_tool_icon_pixmap(item_id, size=20) if item_id else None
            if tool_icon and not tool_icon.isNull():
                icon_x = mid_pt.x() - tool_icon.width() / 2.0
                icon_y = mid_pt.y() - 17.0 - tool_icon.height() / 2.0
                painter.setOpacity(1.0 if (glow > 0.01 or is_parent_active) else 0.92)
                painter.drawPixmap(int(icon_x), int(icon_y), tool_icon)
                painter.setOpacity(1.0)
            else:
                badge_color = TOOL_ACCENT_COLORS.get(item_id, FORMAT_ACCENT_COLORS.get(item_fmt, QColor(226, 232, 240)))
                if glow <= 0.01 and not is_parent_active:
                    painter.setBrush(QBrush(badge_color))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(QPointF(mid_pt.x(), mid_pt.y() - 14), 3.5, 3.5)

            if len(label) > 6:
                font = FONT_BOLD_9
            elif len(label) > 4:
                font = FONT_BOLD_10
            else:
                font = FONT_PETAL
            painter.setFont(font)
            painter.setPen(text_color)
            tw = get_text_advance(font, label)
            painter.drawText(QPointF(mid_pt.x() - tw / 2, mid_pt.y() + 6), label)

            # Outward indicator triangle for slices with cascading radial sub-tiers
            has_sub = isinstance(item, dict) and bool(item.get('sub_id'))
            if has_sub:
                slice_span = 360.0 / num_slices
                mid_a_rad = math.radians(-90.0 + i * slice_span)
                tri_r = (self.geometry_engine.outer_radius + bulge - 6.0) * scale
                tri_x = cx + tri_r * math.cos(mid_a_rad)
                tri_y = cy + tri_r * math.sin(mid_a_rad)
                tri_path = QPainterPath()
                p1 = QPointF(tri_x + 5.0 * math.cos(mid_a_rad), tri_y + 5.0 * math.sin(mid_a_rad))
                p2 = QPointF(tri_x - 3.0 * math.cos(mid_a_rad) - 4.0 * math.sin(mid_a_rad), tri_y - 3.0 * math.sin(mid_a_rad) + 4.0 * math.cos(mid_a_rad))
                p3 = QPointF(tri_x - 3.0 * math.cos(mid_a_rad) + 4.0 * math.sin(mid_a_rad), tri_y - 3.0 * math.sin(mid_a_rad) - 4.0 * math.cos(mid_a_rad))
                tri_path.moveTo(p1)
                tri_path.lineTo(p2)
                tri_path.lineTo(p3)
                tri_path.closeSubpath()
                painter.setBrush(QColor(255, 255, 255) if (glow > 0.01 or is_parent_active) else QColor(148, 163, 184))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(tri_path)

        # 4. Concentric Inner Divider Ring
        r_inner2 = self.geometry_engine.inner_ring_r2 * scale
        ring_rect2 = QRectF(cx - r_inner2, cy - r_inner2, r_inner2 * 2, r_inner2 * 2)

        painter.setBrush(QBrush(INNER_RING_BG))
        painter.setPen(QPen(INNER_RING_BORDER, 1.2))
        painter.drawEllipse(ring_rect2)

        # Inner ring utility buttons (6 circular icons)
        for i in range(self.geometry_engine.inner_button_count):
            btn_pos = self.geometry_engine.get_inner_button_pos(i)
            bx = cx + (btn_pos.x() - cx) * scale
            by = cy + (btn_pos.y() - cy) * scale

            is_inner_hovered = (self.hovered_item == 'inner' and self.hovered_index == i)

            btn_r = 11.0
            if is_inner_hovered:
                painter.setBrush(QBrush(QColor(255, 255, 255, 45)))
                painter.setPen(QPen(QColor(255, 255, 255, 140), 1.5))
            else:
                painter.setBrush(QBrush(QColor(25, 28, 38, 200)))
                painter.setPen(QPen(QColor(255, 255, 255, 22), 1.0))

            painter.drawEllipse(QPointF(bx, by), btn_r, btn_r)

            btn_data = self.inner_buttons[i]
            tool_id = btn_data.get('tool_id', '')
            icon_pm = get_tool_icon_pixmap(tool_id, size=14) if tool_id else None

            if icon_pm and not icon_pm.isNull():
                painter.setOpacity(1.0 if is_inner_hovered else 0.85)
                painter.drawPixmap(int(bx - icon_pm.width() / 2), int(by - icon_pm.height() / 2), icon_pm)
                painter.setOpacity(1.0)
            else:
                tag = btn_data.get('tag', btn_data.get('label', '')[:3].upper())
                painter.setFont(FONT_BOLD_7)
                painter.setPen(INNER_ICON_HOVER if is_inner_hovered else INNER_ICON_NORMAL)
                gw = get_text_advance(FONT_BOLD_7, tag)
                painter.drawText(QPointF(bx - gw / 2, by + 3), tag)

        # 5. Center Hub with Magnetic Ferrofluid Physics (pulled towards hovered slice)
        hub_cx = cx + self.hub_offset_x
        hub_cy = cy + self.hub_offset_y
        hub_r = self.geometry_engine.hub_radius * self.hub_scale
        hub_rect = QRectF(hub_cx - hub_r, hub_cy - hub_r, hub_r * 2, hub_r * 2)

        if self.success_state:
            painter.setBrush(QBrush(HUB_BG_SUCCESS))
            painter.setPen(QPen(QColor(255, 255, 255, 240), 2.0))
            painter.drawEllipse(hub_rect)
            painter.setFont(FONT_BOLD_12)
            painter.setPen(HUB_TEXT_SUCCESS)
            painter.drawText(hub_rect, Qt.AlignmentFlag.AlignCenter, "✓")
        elif self.is_converting:
            painter.setBrush(QBrush(HUB_BG_TOP))
            painter.setPen(QPen(QColor(255, 255, 255, 80), 1.6))
            painter.drawEllipse(hub_rect)
            spin_angle = int((self.time_counter * 240) % 360)
            painter.setPen(QPen(QColor(255, 255, 255, 220), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(hub_rect.adjusted(6, 6, -6, -6), -spin_angle * 16, 120 * 16)
        else:
            hub_grad = QRadialGradient(hub_cx, hub_cy, hub_r)
            hub_grad.setColorAt(0.0, HUB_BG_TOP)
            hub_grad.setColorAt(1.0, HUB_BG_BOT)
            painter.setBrush(QBrush(hub_grad))
            painter.setPen(QPen(HUB_BORDER, 1.6))
            painter.drawEllipse(hub_rect)

            if self.error_message:
                painter.setFont(FONT_BOLD_8)
                painter.setPen(HUB_BG_ERROR)
                painter.drawText(hub_rect, Qt.AlignmentFlag.AlignCenter, self.error_message)
            else:
                # Check hover state on slices or sub-items
                hov_slice = self.active_slices[self.hovered_index] if (self.hovered_item == 'slice' and self.hovered_index is not None and 0 <= self.hovered_index < len(self.active_slices)) else None
                hov_sub = None
                if self.hovered_item == 'sub_item' and self.hovered_sub_index is not None and self.active_sub_id:
                    sub_items = self.sub_menus[self.active_sub_id]['items']
                    if 0 <= self.hovered_sub_index < len(sub_items):
                        hov_sub = sub_items[self.hovered_sub_index]

                active_hov = hov_sub or hov_slice

                if active_hov is not None:
                    is_supp = self.is_item_supported(active_hov)
                    if not is_supp:
                        # Top Line: UNSUPPORTED in soft coral red
                        painter.setFont(FONT_BOLD_7)
                        painter.setPen(QColor(248, 113, 113))
                        painter.drawText(QRectF(hub_cx - 48, hub_cy - 24 * self.hub_scale, 96, 14), Qt.AlignmentFlag.AlignCenter, "UNSUPPORTED")

                        # Mid Line: Dash
                        painter.setFont(FONT_BOLD_12)
                        painter.setPen(QColor(248, 113, 113, 200))
                        painter.drawText(QRectF(hub_cx - 48, hub_cy - 8 * self.hub_scale, 96, 18), Qt.AlignmentFlag.AlignCenter, "—")

                        # Bottom Line: For [ext]
                        ext_tag = self.file_info['ext'].upper() if self.file_info else ""
                        painter.setFont(FONT_REG_7)
                        painter.setPen(QColor(148, 163, 184))
                        painter.drawText(QRectF(hub_cx - 52, hub_cy + 12 * self.hub_scale, 104, 14), Qt.AlignmentFlag.AlignCenter, f"Not for {ext_tag}")
                    else:
                        # Supported Hover: Action or Target Format Preview
                        lbl = active_hov.get('label') or str(active_hov)
                        hint = active_hov.get('hint', '')

                        painter.setFont(FONT_BOLD_7)
                        painter.setPen(QColor(203, 213, 225))
                        painter.drawText(QRectF(hub_cx - 48, hub_cy - 24 * self.hub_scale, 96, 14), Qt.AlignmentFlag.AlignCenter, "CONVERT" if self.page_index == 0 else "QUICK TOOL")

                        painter.setFont(FONT_BOLD_10)
                        painter.setPen(QColor(255, 255, 255))
                        painter.drawText(QRectF(hub_cx - 50, hub_cy - 8 * self.hub_scale, 100, 18), Qt.AlignmentFlag.AlignCenter, lbl[:10])

                        painter.setFont(FONT_REG_7)
                        painter.setPen(QColor(148, 163, 184))
                        painter.drawText(QRectF(hub_cx - 52, hub_cy + 12 * self.hub_scale, 104, 14), Qt.AlignmentFlag.AlignCenter, hint[:16] if hint else "Release to Run")
                else:
                    # Idle: Clearly identify the dragged file type!
                    if self.file_info:
                        cat = self.file_info.get('category', 'generic').upper()
                        ext_upper = self.file_info.get('ext', '').upper()
                        if cat == 'IMAGE':
                            mode_title = f"IMAGE • {ext_upper}"
                        elif cat == 'PDF':
                            mode_title = "PDF DOCUMENT"
                        elif cat == 'DOCX':
                            mode_title = "WORD DOCX"
                        elif cat == 'TXT':
                            mode_title = "TEXT FILE"
                        else:
                            mode_title = f"FILE • {ext_upper}"
                        sub_label = self.file_info.get('size_str', '')
                    else:
                        mode_title = "FORMATS" if self.page_index == 0 else "TOOLS"
                        sub_label = "DRAG FILE"

                    # Mode / File Type Header
                    painter.setFont(FONT_HUB_SUB)
                    painter.setPen(HUB_SUBTEXT)
                    mw = get_text_advance(FONT_HUB_SUB, mode_title)
                    painter.drawText(QPointF(hub_cx - mw / 2, hub_cy - 14 * self.hub_scale), mode_title)

                    # Page indicator: ‹  1/2  ›
                    page_text = f"{self.page_index + 1}/2"
                    painter.setFont(FONT_HUB_PAGE)
                    painter.setPen(HUB_TEXT)
                    pw = get_text_advance(FONT_HUB_PAGE, page_text)
                    painter.drawText(QPointF(hub_cx - pw / 2, hub_cy + 4 * self.hub_scale), page_text)

                    # Left Arrow ‹
                    is_prev_hovered = (self.hovered_item == 'hub_prev')
                    painter.setPen(HUB_ARROW_HOVER if is_prev_hovered else HUB_ARROW_NORMAL)
                    painter.drawText(QPointF(hub_cx - pw / 2 - 16, hub_cy + 3 * self.hub_scale), "‹")

                    # Right Arrow ›
                    is_next_hovered = (self.hovered_item == 'hub_next')
                    painter.setPen(HUB_ARROW_HOVER if is_next_hovered else HUB_ARROW_NORMAL)
                    painter.drawText(QPointF(hub_cx + pw / 2 + 8, hub_cy + 3 * self.hub_scale), "›")

                    # File size or hint
                    painter.setFont(FONT_HUB_SUB)
                    painter.setPen(HUB_SUBTEXT)
                    bw = get_text_advance(FONT_HUB_SUB, sub_label)
                    painter.drawText(QPointF(hub_cx - bw / 2, hub_cy + 20 * self.hub_scale), sub_label)

        # 6. Satellite Buttons (Top-Left Docked Orbits)
        for i in range(len(self.satellites)):
            sat_pos = self.geometry_engine.get_satellite_pos(i)
            sx = cx + (sat_pos.x() - cx) * scale
            sy = cy + (sat_pos.y() - cy) * scale

            is_sat_hovered = (self.hovered_item == 'satellite' and self.hovered_index == i)
            sr = self.geometry_engine.satellite_btn_r

            if is_sat_hovered:
                painter.setBrush(QBrush(SATELLITE_HOVER_BG))
                painter.setPen(QPen(SATELLITE_HOVER_BORDER, 1.8))
            else:
                painter.setBrush(QBrush(SATELLITE_BG))
                painter.setPen(QPen(SATELLITE_BORDER, 1.2))

            painter.drawEllipse(QPointF(sx, sy), sr, sr)

            tag = self.satellites[i].get('tag', self.satellites[i].get('label', '')[:3].upper())
            painter.setFont(FONT_BOLD_7)
            painter.setPen(SATELLITE_HOVER_TEXT if is_sat_hovered else SATELLITE_TEXT)
            gw = get_text_advance(FONT_BOLD_7, tag)
            painter.drawText(QPointF(sx - gw / 2, sy + 3), tag)

        # 7. Frosted Droplet Particles & Shockwave Ripple (NO CYAN GLOW)
        if self.ripple_alpha > 0:
            rip_pen = QPen(QColor(255, 255, 255, int(self.ripple_alpha * 0.65)), 1.5)
            painter.setPen(rip_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), self.ripple_radius, self.ripple_radius)

        if self.particles:
            painter.setPen(Qt.PenStyle.NoPen)
            for p in self.particles:
                p_color = QColor(p.color.red(), p.color.green(), p.color.blue(), int(max(0, min(255, p.alpha))))
                painter.setBrush(QBrush(p_color))
                painter.drawEllipse(QPointF(p.x, p.y), p.radius, p.radius)

        # 8. Cascading Concentric Radial Sub-Tier (curved annular arc sectors fanning outward)
        if self.active_sub_id and self.active_sub_id in self.sub_menus and self.sub_menu_anim > 0.01:
            sub_info = self.sub_menus[self.active_sub_id]
            items = sub_info.get('items', [])
            num_sub = len(items)
            anim = self.bloom_progress * (0.85 + 0.15 * self.sub_menu_anim)
            alpha = int(self.sub_menu_anim * self.bloom_progress * 255)

            center_angle, total_span, r_in, r_out = self.geometry_engine.get_sub_tier_params(self.active_sub_id, num_sub)
            start_angle = center_angle - total_span / 2.0
            step_angle = total_span / max(1, num_sub)

            cur_r_in = (self.geometry_engine.outer_radius + 7.0) * anim
            cur_r_out = cur_r_in + (r_out - r_in) * anim

            # Soft natural dark shadow behind the outer arc tier (NO glowing blue)
            tier_shadow_path = self.geometry_engine.get_annular_sector_path(
                cx, cy, start_angle - 3.0, start_angle + total_span + 3.0,
                cur_r_in - 4.0, cur_r_out + 8.0, gap_deg=0.0, corner_r=12.0
            )
            painter.setBrush(QBrush(QColor(0, 0, 0, int(0.35 * alpha))))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(tier_shadow_path)

            for j, itm in enumerate(items):
                a1 = start_angle + j * step_angle
                a2 = a1 + step_angle

                sub_path = self.geometry_engine.get_annular_sector_path(
                    cx, cy, a1, a2, cur_r_in, cur_r_out, gap_deg=2.5, corner_r=7.0
                )

                is_sub_supported = self.is_item_supported(itm)
                is_sub_hovered = (self.hovered_item == 'sub_item' and self.hovered_sub_index == j and is_sub_supported)

                if not is_sub_supported:
                    # Muted, faded-out sub-tier card for unsupported action
                    grad = QLinearGradient(cx, cy, cx + cur_r_out, cy)
                    grad.setColorAt(0.0, QColor(18, 20, 26, int(0.20 * alpha)))
                    grad.setColorAt(1.0, QColor(12, 14, 18, int(0.20 * alpha)))
                    painter.setBrush(QBrush(grad))
                    painter.setPen(QPen(QColor(255, 255, 255, int(0.06 * alpha)), 1.0, Qt.PenStyle.DashLine))
                    t_color = QColor(100, 116, 139, int(0.35 * alpha))
                    h_color = QColor(71, 85, 105, int(0.25 * alpha))
                elif is_sub_hovered:
                    # Hovered: Frosted Platinum Glass Sheen
                    grad = QLinearGradient(cx, cy, cx + cur_r_out, cy)
                    grad.setColorAt(0.0, QColor(255, 255, 255, int(0.24 * alpha)))
                    grad.setColorAt(1.0, QColor(255, 255, 255, int(0.08 * alpha)))
                    painter.setBrush(QBrush(grad))
                    painter.setPen(QPen(QColor(255, 255, 255, int(0.75 * alpha)), 1.8))
                    t_color = QColor(255, 255, 255, alpha)
                    h_color = QColor(226, 232, 240, alpha)
                else:
                    # Normal: Dark Titanium Matte Card
                    grad = QLinearGradient(cx, cy, cx + cur_r_out, cy)
                    grad.setColorAt(0.0, QColor(28, 32, 42, int(0.94 * alpha)))
                    grad.setColorAt(1.0, QColor(18, 21, 28, int(0.98 * alpha)))
                    painter.setBrush(QBrush(grad))
                    painter.setPen(QPen(QColor(255, 255, 255, int(0.18 * alpha)), 1.2))
                    t_color = QColor(241, 245, 249, alpha)
                    h_color = QColor(148, 163, 184, alpha)

                painter.drawPath(sub_path)

                # Midpoint for placing text and icon
                mid_angle_deg = a1 + step_angle / 2.0
                mid_angle_rad = math.radians(mid_angle_deg)
                mid_radius = (cur_r_in + cur_r_out) / 2.0
                tx = cx + mid_radius * math.cos(mid_angle_rad)
                ty = cy + mid_radius * math.sin(mid_angle_rad)

                # Real Tool Icon or Accent Pip Dot (clean geometric badge, NO emoji)
                tool_id = itm.get('id', '')
                icon_pm = get_tool_icon_pixmap(tool_id, size=18) if tool_id else None

                if icon_pm and not icon_pm.isNull():
                    if not is_sub_supported:
                        painter.setOpacity(0.30 * (alpha / 255.0))
                    elif is_sub_hovered:
                        painter.setOpacity(1.0 * (alpha / 255.0))
                    else:
                        painter.setOpacity(0.92 * (alpha / 255.0))
                    painter.drawPixmap(int(tx - icon_pm.width() / 2), int(ty - 13 - icon_pm.height() / 2), icon_pm)
                    painter.setOpacity(1.0)
                else:
                    accent_col = itm.get('accent', QColor(226, 232, 240))
                    painter.setBrush(QBrush(accent_col))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(QPointF(tx, ty - 12), 3.5, 3.5)

                # Label (Bold Title)
                i_label = itm.get('label', '')
                painter.setFont(FONT_BOLD_8)
                painter.setPen(t_color)
                painter.drawText(QRectF(tx - 38, ty - 2, 76, 16), Qt.AlignmentFlag.AlignCenter, i_label)

                # Hint / Badge
                i_hint = itm.get('hint', '')
                if i_hint:
                    short_hint = i_hint.split('(')[0].strip() if '(' in i_hint else i_hint
                    painter.setFont(FONT_REG_6)
                    painter.setPen(h_color)
                    painter.drawText(QRectF(tx - 44, ty + 13, 88, 14), Qt.AlignmentFlag.AlignCenter, short_hint[:18])

