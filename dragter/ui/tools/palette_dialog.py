"""Extract dominant color palette from images with 1-click HEX/RGB copy."""

from pathlib import Path
from typing import List, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QApplication
)
from PyQt6.QtGui import QFont
from dragter.ui.theme import get_tool_icon_pixmap
from PIL import Image


class PaletteDialog(QDialog):
    """Professional dark glass color palette extractor dialog."""

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = Path(file_path)
        self.colors: List[Tuple[int, int, int]] = []

        self.setWindowTitle("Color Palette — Dragter")
        self.setFixedSize(620, 460)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._extract_palette()
        self._init_ui()

    def _extract_palette(self):
        try:
            with Image.open(self.file_path) as img:
                # Resize for fast processing and convert to RGB
                small = img.convert('RGB').resize((150, 150), Image.Resampling.LANCZOS)
                # Quantize to 6 dominant colors
                quantized = small.quantize(colors=6, method=Image.Quantize.FASTOCTREE)
                palette = quantized.getpalette()[:18]
                self.colors = [
                    (palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2])
                    for i in range(len(palette) // 3)
                ]
        except Exception:
            # Fallback neutral palette
            self.colors = [
                (24, 28, 36), (64, 72, 88), (148, 163, 184),
                (203, 213, 225), (241, 245, 249), (255, 255, 255)
            ]

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)

        container = QFrame(self)
        container.setObjectName("container")
        container.setStyleSheet("""
            QFrame#container {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(26, 28, 35, 0.98),
                    stop:1 rgba(15, 17, 22, 0.99));
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 16px;
            }
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(24, 20, 24, 20)
        c_layout.setSpacing(16)

        # Header bar
        header = QHBoxLayout()
        header.setSpacing(10)
        icon_pm = get_tool_icon_pixmap('palette', 26)
        if icon_pm:
            icon_lbl = QLabel(self)
            icon_lbl.setPixmap(icon_pm)
            icon_lbl.setStyleSheet("background: transparent;")
            header.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title = QLabel("Color Palette Extractor", self)
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC; background: transparent;")
        sub = QLabel(f"Dominant colors from: {self.file_path.name}", self)
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet("color: #94A3B8; background: transparent;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)

        header.addStretch()

        close_btn = QPushButton("✕", self)
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #CBD5E1;
                border: none;
                border-radius: 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.16);
                color: #FFFFFF;
            }
        """)
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)
        c_layout.addLayout(header)

        # Swatch bar preview
        bar_frame = QFrame(self)
        bar_frame.setFixedHeight(48)
        bar_layout = QHBoxLayout(bar_frame)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        for r, g, b in self.colors:
            swatch = QFrame(self)
            swatch.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); border: none;")
            bar_layout.addWidget(swatch)
        bar_frame.setStyleSheet("border-radius: 8px; overflow: hidden;")
        c_layout.addWidget(bar_frame)

        # Color cards grid (3 columns x 2 rows)
        grid = QGridLayout()
        grid.setSpacing(12)
        self.card_buttons = []

        for i, (r, g, b) in enumerate(self.colors):
            hex_str = f"#{r:02X}{g:02X}{b:02X}"
            rgb_str = f"rgb({r}, {g}, {b})"

            card = QPushButton(self)
            card.setFixedHeight(68)
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 10px;
                    padding: 8px 14px;
                    text-align: left;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.10);
                    border: 1px solid rgba(255, 255, 255, 0.22);
                }
            """)

            row_layout = QHBoxLayout(card)
            row_layout.setContentsMargins(10, 8, 10, 8)
            row_layout.setSpacing(12)

            dot = QFrame(card)
            dot.setFixedSize(36, 36)
            dot.setStyleSheet(f"background-color: {hex_str}; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.18);")
            row_layout.addWidget(dot)

            info_box = QVBoxLayout()
            h_lbl = QLabel(hex_str, card)
            h_lbl.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            h_lbl.setStyleSheet("color: #FFFFFF; background: transparent;")
            r_lbl = QLabel(rgb_str, card)
            r_lbl.setFont(QFont("Consolas", 8))
            r_lbl.setStyleSheet("color: #94A3B8; background: transparent;")
            info_box.addWidget(h_lbl)
            info_box.addWidget(r_lbl)
            row_layout.addLayout(info_box)

            row_layout.addStretch()

            copy_icon = QLabel("Copy", card)
            copy_icon.setStyleSheet("color: #64748B; background: transparent; font-size: 10px; font-weight: 600;")
            row_layout.addWidget(copy_icon)

            card.clicked.connect(lambda checked, h=hex_str, b=card: self._copy_single(h, b))
            grid.addWidget(card, i // 3, i % 3)

        c_layout.addLayout(grid)

        # Footer
        footer = QHBoxLayout()
        self.status_lbl = QLabel("Click any card to copy HEX code", self)
        self.status_lbl.setFont(QFont("Segoe UI", 9))
        self.status_lbl.setStyleSheet("color: #94A3B8; background: transparent;")
        footer.addWidget(self.status_lbl)

        footer.addStretch()

        copy_all_btn = QPushButton("Copy All (CSS Variables)", self)
        copy_all_btn.setFixedHeight(36)
        copy_all_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.10);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                font-size: 11px;
                font-weight: bold;
                padding: 0 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.18);
            }
        """)
        copy_all_btn.clicked.connect(self._copy_all_css)
        footer.addWidget(copy_all_btn)

        done_btn = QPushButton("Done", self)
        done_btn.setFixedHeight(36)
        done_btn.setFixedWidth(80)
        done_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #0F172A;
                border: none;
                border-radius: 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #F1F5F9;
            }
        """)
        done_btn.clicked.connect(self.accept)
        footer.addWidget(done_btn)

        c_layout.addLayout(footer)
        root_layout.addWidget(container)

    def _copy_single(self, hex_code: str, button: QPushButton):
        cb = QApplication.clipboard()
        if cb:
            cb.setText(hex_code)
            self.status_lbl.setText(f"✓ Copied {hex_code} to clipboard!")
            self.status_lbl.setStyleSheet("color: #4ADE80; font-weight: bold; background: transparent;")

    def _copy_all_css(self):
        cb = QApplication.clipboard()
        if cb:
            css_vars = "\n".join([f"  --color-{i + 1}: #{r:02X}{g:02X}{b:02X};" for i, (r, g, b) in enumerate(self.colors)])
            css_text = f":root {{\n{css_vars}\n}}"
            cb.setText(css_text)
            self.status_lbl.setText("✓ Copied all CSS variables to clipboard!")
            self.status_lbl.setStyleSheet("color: #4ADE80; font-weight: bold; background: transparent;")
