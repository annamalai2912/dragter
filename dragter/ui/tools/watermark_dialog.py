"""Watermark and Stamp Tool — Add customizable text or logo stamp to images."""

from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QSlider, QComboBox,
    QMessageBox
)

from dragter.ui.theme import (
    MODAL_CONTAINER_STYLE, MODAL_TITLE_STYLE, MODAL_LABEL_STYLE,
    MODAL_CLOSE_STYLE, MODAL_BTN_PRIMARY_STYLE, MODAL_BTN_SECONDARY_STYLE,
    get_tool_icon_pixmap
)
from dragter.core.converter import get_unique_output_path


class WatermarkDialog(QDialog):
    """Interactive tool to watermark images with text or logo stamp."""

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = Path(file_path)
        self.setWindowTitle("Watermark & Stamp — Dragter")
        self.setFixedSize(720, 560)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.watermark_text = "CONFIDENTIAL"
        self.opacity = 65
        self.position = "Bottom-Right"  # "Center", "Bottom-Right", "Bottom-Left", "Tiled"
        self.font_scale = 32

        self.original_image: Optional[Image.Image] = None
        self._load_image()
        self._setup_ui()
        self._update_preview()

    def _load_image(self):
        try:
            self.original_image = Image.open(self.file_path).convert("RGBA")
        except Exception:
            self.original_image = Image.new("RGBA", (800, 600), (40, 44, 52))

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet(MODAL_CONTAINER_STYLE)
        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(20, 16, 20, 16)
        c_layout.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        hdr.setSpacing(10)
        icon_pm = get_tool_icon_pixmap('watermark', 26)
        if icon_pm:
            icon_lbl = QLabel(self)
            icon_lbl.setPixmap(icon_pm)
            icon_lbl.setStyleSheet("background: transparent;")
            hdr.addWidget(icon_lbl)
        title = QLabel("Watermark & Stamp", self)
        title.setStyleSheet(MODAL_TITLE_STYLE)
        hdr.addWidget(title)
        hdr.addStretch()

        close_btn = QPushButton("✕", self)
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(MODAL_CLOSE_STYLE)
        close_btn.clicked.connect(self.reject)
        hdr.addWidget(close_btn)
        c_layout.addLayout(hdr)

        # Body: Preview + Controls
        body = QHBoxLayout()
        body.setSpacing(16)

        # Left Preview Area
        prev_card = QFrame()
        prev_card.setStyleSheet("background: rgba(0, 0, 0, 0.4); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08);")
        prev_layout = QVBoxLayout(prev_card)
        prev_layout.setContentsMargins(8, 8, 8, 8)

        self.preview_lbl = QLabel()
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setMinimumSize(420, 340)
        prev_layout.addWidget(self.preview_lbl)
        body.addWidget(prev_card, 3)

        # Right Controls
        ctrls = QVBoxLayout()
        ctrls.setSpacing(10)

        # Watermark Text input
        txt_lbl = QLabel("Watermark Text:")
        txt_lbl.setStyleSheet(MODAL_LABEL_STYLE)
        ctrls.addWidget(txt_lbl)

        self.txt_input = QLineEdit(self.watermark_text)
        self.txt_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 8px;
                color: #f1f5f9;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
        """)
        self.txt_input.textChanged.connect(self._on_text_changed)
        ctrls.addWidget(self.txt_input)

        # Position Dropdown
        pos_lbl = QLabel("Position:")
        pos_lbl.setStyleSheet(MODAL_LABEL_STYLE)
        ctrls.addWidget(pos_lbl)

        self.pos_combo = QComboBox()
        self.pos_combo.addItems(["Bottom-Right", "Center", "Bottom-Left", "Top-Right", "Tiled"])
        self.pos_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 8px;
                color: #f1f5f9;
                padding: 6px 10px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background: #1e222b;
                color: #f1f5f9;
                selection-background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.pos_combo.currentTextChanged.connect(self._on_pos_changed)
        ctrls.addWidget(self.pos_combo)

        # Opacity Slider
        op_lbl = QLabel("Opacity:")
        op_lbl.setStyleSheet(MODAL_LABEL_STYLE)
        ctrls.addWidget(op_lbl)

        self.op_slider = QSlider(Qt.Orientation.Horizontal)
        self.op_slider.setRange(10, 100)
        self.op_slider.setValue(self.opacity)
        self.op_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 5px;
                background: rgba(255, 255, 255, 0.12);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: rgba(255, 255, 255, 0.5);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        self.op_slider.valueChanged.connect(self._on_op_changed)
        ctrls.addWidget(self.op_slider)

        # Font Size Slider
        sz_lbl = QLabel("Stamp Size:")
        sz_lbl.setStyleSheet(MODAL_LABEL_STYLE)
        ctrls.addWidget(sz_lbl)

        self.sz_slider = QSlider(Qt.Orientation.Horizontal)
        self.sz_slider.setRange(16, 72)
        self.sz_slider.setValue(self.font_scale)
        self.sz_slider.setStyleSheet(self.op_slider.styleSheet())
        self.sz_slider.valueChanged.connect(self._on_sz_changed)
        ctrls.addWidget(self.sz_slider)

        ctrls.addStretch()
        body.addLayout(ctrls, 2)
        c_layout.addLayout(body)

        # Footer
        ftr = QHBoxLayout()
        ftr.addStretch()

        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.setStyleSheet(MODAL_BTN_SECONDARY_STYLE)
        cancel_btn.clicked.connect(self.reject)
        ftr.addWidget(cancel_btn)

        save_btn = QPushButton("Apply Watermark", self)
        save_btn.setStyleSheet(MODAL_BTN_PRIMARY_STYLE)
        save_btn.clicked.connect(self._apply_and_save)
        ftr.addWidget(save_btn)

        c_layout.addLayout(ftr)
        main_layout.addWidget(self.container)

    def _on_text_changed(self, txt: str):
        self.watermark_text = txt
        self._update_preview()

    def _on_pos_changed(self, pos: str):
        self.position = pos
        self._update_preview()

    def _on_op_changed(self, val: int):
        self.opacity = val
        self._update_preview()

    def _on_sz_changed(self, val: int):
        self.font_scale = val
        self._update_preview()

    def _render_watermarked(self) -> Image.Image:
        if not self.original_image:
            return Image.new("RGBA", (400, 400), (0, 0, 0, 0))

        base = self.original_image.copy()
        txt_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        text = self.watermark_text or "WATERMARK"
        alpha = int(255 * (self.opacity / 100.0))
        fill_color = (255, 255, 255, alpha)

        try:
            font = ImageFont.truetype("arial.ttf", self.font_scale)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        W, H = base.size

        if self.position == "Center":
            x = (W - tw) // 2
            y = (H - th) // 2
            draw.text((x, y), text, font=font, fill=fill_color)
        elif self.position == "Bottom-Right":
            x = W - tw - 24
            y = H - th - 24
            draw.text((x, y), text, font=font, fill=fill_color)
        elif self.position == "Bottom-Left":
            x = 24
            y = H - th - 24
            draw.text((x, y), text, font=font, fill=fill_color)
        elif self.position == "Top-Right":
            x = W - tw - 24
            y = 24
            draw.text((x, y), text, font=font, fill=fill_color)
        elif self.position == "Tiled":
            step_x = max(tw + 60, 120)
            step_y = max(th + 60, 80)
            for ty in range(20, H, step_y):
                for tx in range(20, W, step_x):
                    draw.text((tx, ty), text, font=font, fill=(255, 255, 255, int(alpha * 0.45)))

        return Image.alpha_composite(base, txt_layer)

    def _update_preview(self):
        result = self._render_watermarked()
        # Scale for preview label
        preview_img = result.copy()
        preview_img.thumbnail((420, 340), Image.Resampling.LANCZOS)
        data = preview_img.convert("RGBA").tobytes("raw", "RGBA")
        qim = QImage(data, preview_img.width, preview_img.height, QImage.Format.Format_RGBA8888)
        pix = QPixmap.fromImage(qim)
        self.preview_lbl.setPixmap(pix)

    def _apply_and_save(self):
        out_path = get_unique_output_path(self.file_path.parent / f"{self.file_path.stem}_watermarked.png")
        try:
            result = self._render_watermarked()
            result.save(out_path, "PNG")
            QMessageBox.information(self, "Success", f"Watermarked image saved to:\n{out_path.name}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save image: {e}")
