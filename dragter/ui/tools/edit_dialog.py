"""Image Adjustments and Transform Dialog (Brightness, Contrast, Rotation, Flip, Filters)."""

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QSizePolicy
)
from PIL import Image, ImageEnhance, ImageOps
from dragter.ui.theme import MODAL_BTN_PRIMARY_STYLE, get_tool_icon_pixmap


class EditDialog(QDialog):
    """Adjust brightness, contrast, saturation, and transform images."""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.edited_result: Optional[str] = None
        
        with Image.open(image_path) as img:
            self.original_img = img.convert('RGB')
        self.current_img = self.original_img.copy()
        
        self.rotation_angle = 0
        self.flip_h = False
        self.flip_v = False
        self.grayscale = False
        self.invert = False

        self.setWindowTitle("Edit Image")
        self.setMinimumSize(820, 680)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setup_ui()
        self.update_preview()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(26, 29, 39, 0.98),
                    stop:1 rgba(15, 17, 23, 0.99));
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 20px;
            }
        """)
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        icon_pm = get_tool_icon_pixmap('edit', 26)
        if icon_pm:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_pm)
            icon_lbl.setStyleSheet("background: transparent;")
            header.addWidget(icon_lbl)
        title = QLabel("Edit & Enhance Image")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #f1f5f9; background: transparent;")
        header.addWidget(title)
        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
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
        """)
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Center Preview Label
        self.preview_lbl = QLabel()
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_lbl.setStyleSheet("background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px;")
        layout.addWidget(self.preview_lbl)

        # Sliders panel
        sliders_panel = QHBoxLayout()
        sliders_panel.setSpacing(20)

        # Brightness
        b_box = QVBoxLayout()
        b_lbl = QLabel("Brightness")
        b_lbl.setStyleSheet("color: #cbd5e1; font-weight: bold;")
        b_box.addWidget(b_lbl)
        self.b_slider = self.create_slider()
        b_box.addWidget(self.b_slider)
        sliders_panel.addLayout(b_box)

        # Contrast
        c_box = QVBoxLayout()
        c_lbl = QLabel("Contrast")
        c_lbl.setStyleSheet("color: #cbd5e1; font-weight: bold;")
        c_box.addWidget(c_lbl)
        self.c_slider = self.create_slider()
        c_box.addWidget(self.c_slider)
        sliders_panel.addLayout(c_box)

        # Saturation
        s_box = QVBoxLayout()
        s_lbl = QLabel("Saturation")
        s_lbl.setStyleSheet("color: #cbd5e1; font-weight: bold;")
        s_box.addWidget(s_lbl)
        self.s_slider = self.create_slider()
        s_box.addWidget(self.s_slider)
        sliders_panel.addLayout(s_box)

        layout.addLayout(sliders_panel)

        # Transform and Action Buttons
        controls = QHBoxLayout()
        controls.setSpacing(10)

        rot_cw_btn = self.create_btn("↷ Rotate 90°", self.rotate_cw)
        controls.addWidget(rot_cw_btn)

        flip_h_btn = self.create_btn("⇄ Flip H", self.toggle_flip_h)
        controls.addWidget(flip_h_btn)

        bw_btn = self.create_btn("◐ B&W", self.toggle_bw)
        controls.addWidget(bw_btn)

        invert_btn = self.create_btn("◑ Invert", self.toggle_invert)
        controls.addWidget(invert_btn)

        reset_btn = self.create_btn("Reset", self.reset_adjustments)
        controls.addWidget(reset_btn)

        controls.addStretch()

        apply_btn = QPushButton("Save Edited")
        apply_btn.setFixedSize(120, 34)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet(MODAL_BTN_PRIMARY_STYLE)
        apply_btn.clicked.connect(self.save_and_apply)
        controls.addWidget(apply_btn)

        layout.addLayout(controls)
        main_layout.addWidget(self.container)

    def create_slider(self) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(20, 200)
        slider.setValue(100)
        slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; background: rgba(255, 255, 255, 0.12); border-radius: 3px; }
            QSlider::sub-page:horizontal { background: rgba(255, 255, 255, 0.5); border-radius: 3px; }
            QSlider::handle:horizontal { background: #ffffff; border: 2px solid rgba(0, 0, 0, 0.2); width: 16px; margin: -5px 0; border-radius: 8px; }
        """)
        slider.valueChanged.connect(self.update_preview)
        return slider

    def create_btn(self, text: str, callback) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 16px;
                color: #cbd5e1;
                font-weight: 500;
                padding: 0 12px;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.15); color: white; }
        """)
        btn.clicked.connect(callback)
        return btn

    def rotate_cw(self):
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.update_preview()

    def toggle_flip_h(self):
        self.flip_h = not self.flip_h
        self.update_preview()

    def toggle_bw(self):
        self.grayscale = not self.grayscale
        self.update_preview()

    def toggle_invert(self):
        self.invert = not self.invert
        self.update_preview()

    def reset_adjustments(self):
        self.b_slider.setValue(100)
        self.c_slider.setValue(100)
        self.s_slider.setValue(100)
        self.rotation_angle = 0
        self.flip_h = False
        self.flip_v = False
        self.grayscale = False
        self.invert = False
        self.update_preview()

    def apply_pipeline(self) -> Image.Image:
        img = self.original_img.copy()

        # Rotation
        if self.rotation_angle != 0:
            img = img.rotate(-self.rotation_angle, expand=True)

        # Flips
        if self.flip_h:
            img = ImageOps.mirror(img)

        # Filters
        if self.grayscale:
            img = ImageOps.grayscale(img).convert('RGB')

        if self.invert:
            img = ImageOps.invert(img)

        # Enhancements
        b_val = self.b_slider.value() / 100.0
        if b_val != 1.0:
            img = ImageEnhance.Brightness(img).enhance(b_val)

        c_val = self.c_slider.value() / 100.0
        if c_val != 1.0:
            img = ImageEnhance.Contrast(img).enhance(c_val)

        s_val = self.s_slider.value() / 100.0
        if s_val != 1.0 and not self.grayscale:
            img = ImageEnhance.Color(img).enhance(s_val)

        return img

    def update_preview(self):
        img = self.apply_pipeline()
        w, h = max(100, self.preview_lbl.width() - 20), max(100, self.preview_lbl.height() - 20)
        preview_copy = img.copy()
        preview_copy.thumbnail((w, h), Image.Resampling.LANCZOS)
        
        # Convert PIL to QPixmap
        data = preview_copy.tobytes("raw", "RGB")
        qimg = QImage(data, preview_copy.width, preview_copy.height, preview_copy.width * 3, QImage.Format.Format_RGB888)
        self.preview_lbl.setPixmap(QPixmap.fromImage(qimg))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_preview()

    def save_and_apply(self):
        img = self.apply_pipeline()
        src_path = Path(self.image_path)
        out_path = src_path.parent / f"{src_path.stem} Edited{src_path.suffix}"
        counter = 1
        while out_path.exists():
            out_path = src_path.parent / f"{src_path.stem} Edited ({counter}){src_path.suffix}"
            counter += 1

        img.save(str(out_path), quality=95)
        self.edited_result = str(out_path)
        self.accept()
