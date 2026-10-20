"""Executive dark titanium & frosted glass radial HUD theme — professional, precision matte with zero glowing neon blues."""

from PyQt6.QtGui import QColor, QFont

# ── Outer Disc (Main dark circular container) ─────────────────────────────────
DISC_BG_TOP       = QColor(24,  27,  34,  248)   # Dark titanium matte
DISC_BG_BOT       = QColor(14,  16,  20,  253)   # Deep obsidian slate
DISC_BORDER       = QColor(255, 255, 255, 30)    # Crisp precision glass rim
DISC_AURA         = QColor(0,   0,   0,   85)    # Subtle natural drop shadow (NO glowing blue aura)

# ── Inner Ring (Concentric utility divider ring) ──────────────────────────────
INNER_RING_BG     = QColor(18,  20,  26,  242)
INNER_RING_BORDER = QColor(255, 255, 255, 22)
INNER_ICON_NORMAL = QColor(148, 163, 184)
INNER_ICON_HOVER  = QColor(255, 255, 255)

# ── Slices / Petals (Format and Tool Tiles) ──────────────────────────────────
PETAL_BG_TOP          = QColor(32,  36,  46,  235)   # Brushed dark slate
PETAL_BG_BOT          = QColor(20,  23,  30,  245)
PETAL_BORDER_NORMAL   = QColor(255, 255, 255, 26)
PETAL_TEXT_NORMAL     = QColor(226, 232, 240)         # Crisp platinum white
PETAL_SUBTEXT_NORMAL  = QColor(148, 163, 184)         # Slate 400

# ── Hovered / Active Slice (Frosted Platinum Glass Highlight — NO CYAN) ───────
GLASS_HOVER_TOP       = QColor(255, 255, 255, 48)    # Frosted specular sheen
GLASS_HOVER_BOT       = QColor(255, 255, 255, 18)    # Pure glass gradient
PETAL_BORDER_HOVER    = QColor(255, 255, 255, 165)   # High-contrast precision silver rim
PETAL_TEXT_HOVER      = QColor(255, 255, 255)

# Backwards compatibility alias
CYAN_ACCENT_TOP       = GLASS_HOVER_TOP
CYAN_ACCENT_BOT       = GLASS_HOVER_BOT

# ── Center Hub (Navigation & Mode Indicator) ─────────────────────────────────
HUB_BG_TOP        = QColor(28,  32,  40,  252)
HUB_BG_BOT        = QColor(16,  18,  24,  255)
HUB_BORDER        = QColor(255, 255, 255, 38)
HUB_TEXT          = QColor(255, 255, 255)
HUB_SUBTEXT       = QColor(148, 163, 184)
HUB_ARROW_NORMAL  = QColor(160, 174, 192)
HUB_ARROW_HOVER   = QColor(255, 255, 255)

# ── Satellite Buttons (Top-Left Docked Orbits) ───────────────────────────────
SATELLITE_BG          = QColor(28,  31,  40,  245)
SATELLITE_BORDER      = QColor(255, 255, 255, 35)
SATELLITE_TEXT        = QColor(203, 213, 225)
SATELLITE_HOVER_BG    = QColor(255, 255, 255, 45)
SATELLITE_HOVER_BORDER= QColor(255, 255, 255, 160)
SATELLITE_HOVER_TEXT  = QColor(255, 255, 255)

# ── State Colours ─────────────────────────────────────────────────────────────
HUB_BG_SUCCESS   = QColor(34,  197, 94,  240)   # Emerald green
HUB_TEXT_SUCCESS = QColor(255, 255, 255)
HUB_BG_ERROR     = QColor(239, 68,  68,  240)   # Crimson red

# ── Typography ────────────────────────────────────────────────────────────────
FONT_PETAL       = QFont("Segoe UI", 11, QFont.Weight.Bold)
FONT_PETAL_SUB   = QFont("Segoe UI",  8, QFont.Weight.DemiBold)
FONT_HUB_PAGE    = QFont("Segoe UI", 12, QFont.Weight.Bold)
FONT_HUB_SUB     = QFont("Segoe UI",  8, QFont.Weight.DemiBold)
FONT_SATELLITE   = QFont("Segoe UI", 10, QFont.Weight.Bold)
FONT_INNER       = QFont("Segoe UI", 10, QFont.Weight.Normal)

# Static pre-instantiated fonts for zero-allocation 60 FPS rendering
FONT_EMOJI_12    = QFont("Segoe UI Emoji", 12)
FONT_EMOJI_13    = QFont("Segoe UI Emoji", 13)
FONT_BOLD_7      = QFont("Segoe UI", 7, QFont.Weight.Bold)
FONT_BOLD_8      = QFont("Segoe UI", 8, QFont.Weight.Bold)
FONT_BOLD_9      = QFont("Segoe UI", 9, QFont.Weight.Bold)
FONT_BOLD_10     = QFont("Segoe UI", 10, QFont.Weight.Bold)
FONT_BOLD_12     = QFont("Segoe UI", 12, QFont.Weight.Bold)
FONT_REG_6       = QFont("Segoe UI", 6)
FONT_REG_7       = QFont("Segoe UI", 7)
FONT_REG_9       = QFont("Segoe UI", 9)
FONT_REG_10      = QFont("Segoe UI", 10)

import sys
from pathlib import Path
from typing import Optional, Dict, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPixmap, QIcon

# ── Real Icon Asset Management (Zero-latency cached PNG blits) ─────────────────
if getattr(sys, 'frozen', False):
    _base_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    if (_base_dir / "icons").exists():
        ICONS_DIR = _base_dir / "icons"
    elif (_base_dir / "_internal" / "icons").exists():
        ICONS_DIR = _base_dir / "_internal" / "icons"
    else:
        ICONS_DIR = Path(sys.executable).parent / "icons"
else:
    ICONS_DIR = Path(__file__).resolve().parent.parent.parent / "icons"

TOOL_ICON_FILES = {
    'crop':      'crop.png',
    'compress':  'data-compression.png',
    'metadata':  'metadata.png',
    'edit':      'color-wheel.png',
    'annotate':  'notes.png',
    'add_bg':    'generative-image.png',
    'redact':    'text-recognising.png',
    'ocr':       'ocr.png',
    'palette':   'color-wheel.png',
    'watermark': 'watermark.png',
    'qr':        'qr-code.png',
    'tools':     'video-editor.png',
}

_PIXMAP_CACHE: Dict[Tuple[str, int, int], QPixmap] = {}


def get_tool_icon_pixmap(tool_id: str, size: int = 24) -> Optional[QPixmap]:
    """Retrieve pre-scaled and smoothly cached QPixmap for the desired tool icon."""
    if not tool_id:
        return None
    key = (tool_id.lower(), size, size)
    cached = _PIXMAP_CACHE.get(key)
    if cached is not None:
        return cached

    fname = TOOL_ICON_FILES.get(tool_id.lower())
    if not fname:
        for k, v in TOOL_ICON_FILES.items():
            if k in tool_id.lower():
                fname = v
                break

    if not fname:
        return None

    path = ICONS_DIR / fname
    if not path.exists():
        return None

    orig = QPixmap(str(path))
    if orig.isNull():
        return None

    scaled = orig.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )
    _PIXMAP_CACHE[key] = scaled
    return scaled


def get_tool_qicon(tool_id: str, size: int = 24) -> Optional[QIcon]:
    """Return a QIcon for buttons and window icons."""
    pm = get_tool_icon_pixmap(tool_id, size)
    return QIcon(pm) if pm else None


# ── Tool Glyph & Distinct Accent Map ──────────────────────────────────────────
TOOL_ICONS = {k: '' for k in TOOL_ICON_FILES}

# Individual refined badge colors per tool
TOOL_ACCENT_COLORS = {
    'crop':      QColor(245, 158, 11),  # Amber
    'compress':  QColor(16,  185, 129), # Emerald
    'edit':      QColor(203, 213, 225), # Platinum Slate
    'annotate':  QColor(168, 85,  247), # Purple
    'add_bg':    QColor(236, 72,  153), # Rose
    'redact':    QColor(244, 63,  94),  # Coral
    'metadata':  QColor(148, 163, 184), # Slate
    'ocr':       QColor(251, 191, 36),  # Gold
    'palette':   QColor(192, 132, 252), # Violet
    'watermark': QColor(20,  184, 166), # Teal
    'qr':        QColor(248, 250, 252), # Crisp White Platinum
}

# Format badge colors (clean, distinguished, non-neon)
FORMAT_ACCENT_COLORS = {
    'PNG':  QColor(226, 232, 240),  # Pure Platinum
    'JPG':  QColor(245, 158, 11),   # Warm Amber
    'WEBP': QColor(34,  197, 94),   # Emerald
    'PDF':  QColor(239, 68,  68),   # Crimson
    'ICO':  QColor(234, 179, 8),    # Yellow
    'DOCX': QColor(148, 163, 184),  # Slate
    'TXT':  QColor(203, 213, 225),  # Silver
    'HEIC': QColor(236, 72,  153),  # Rose
    'JPEG': QColor(245, 158, 11),   # Amber
    'AVIF': QColor(168, 85,  247),  # Purple
    'TIFF': QColor(20,  184, 166),  # Teal
    'BMP':  QColor(244, 63,  94),   # Coral
    'GIF':  QColor(251, 146, 60),   # Orange
    'SVG':  QColor(168, 85,  247),  # Violet
}

# ── Shared Dark Titanium Modal Dialog Styles (Clean Apple / Raycast aesthetic) ──
MODAL_CONTAINER_STYLE = """
    QFrame#container, QFrame {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(28, 32, 40, 0.98),
            stop:1 rgba(15, 17, 22, 0.99));
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 18px;
    }
"""

MODAL_TITLE_STYLE = "color: #f8fafc; background: transparent; font-size: 14px; font-weight: bold; letter-spacing: 0.3px;"
MODAL_LABEL_STYLE = "color: #94a3b8; background: transparent; font-size: 11px;"

MODAL_CLOSE_STYLE = """
    QPushButton {
        background: rgba(255, 255, 255, 0.08);
        color: #94a3b8;
        border: none;
        border-radius: 15px;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover {
        background: rgba(239, 68, 68, 0.85);
        color: white;
    }
"""

# Professional clean high-contrast primary button (Apple / Linear style white on dark)
MODAL_BTN_PRIMARY_STYLE = """
    QPushButton {
        background: #ffffff;
        color: #0f172a;
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 12px;
        font-weight: 700;
        font-size: 11px;
        padding: 6px 18px;
    }
    QPushButton:hover {
        background: #f1f5f9;
        color: #020617;
    }
    QPushButton:pressed {
        background: #e2e8f0;
    }
"""

MODAL_BTN_SECONDARY_STYLE = """
    QPushButton {
        background: rgba(255, 255, 255, 0.07);
        color: #cbd5e1;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 12px;
        font-weight: 500;
        font-size: 11px;
        padding: 6px 14px;
    }
    QPushButton:hover {
        background: rgba(255, 255, 255, 0.15);
        color: #ffffff;
    }
    QPushButton:pressed {
        background: rgba(255, 255, 255, 0.04);
    }
"""

