"""File Compression Dialog (Image & PDF size reduction)."""

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QMessageBox
)
from PIL import Image
import pymupdf

from dragter.core.file_info import format_file_size
from dragter.ui.theme import MODAL_BTN_PRIMARY_STYLE, MODAL_BTN_SECONDARY_STYLE, get_tool_icon_pixmap


class CompressDialog(QDialog):
    """Modern modal for quick offline file compression."""

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = Path(file_path)
        self.compressed_result: Optional[str] = None
        self.orig_size = self.file_path.stat().st_size
        self.quality = 75

        self.setWindowTitle("Compress File")
        self.setFixedSize(540, 420)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setup_ui()
        self.update_estimated_size()

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
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        icon_pm = get_tool_icon_pixmap('compress', 26)
        if icon_pm:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_pm)
            icon_lbl.setStyleSheet("background: transparent;")
            header.addWidget(icon_lbl)
        title = QLabel("Compress File")
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

        # File summary card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(36, 41, 54, 0.75);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(6)

        name_lbl = QLabel(self.file_path.name)
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        name_lbl.setStyleSheet("color: #f1f5f9; background: transparent;")
        card_layout.addWidget(name_lbl)

        sizes_layout = QHBoxLayout()
        orig_lbl = QLabel(f"Original: {format_file_size(self.orig_size)}")
        orig_lbl.setStyleSheet("color: #94a3b8; font-weight: 500; background: transparent;")
        sizes_layout.addWidget(orig_lbl)

        sizes_layout.addSpacing(16)
        self.est_lbl = QLabel()
        self.est_lbl.setStyleSheet("color: #f8fafc; font-weight: bold; background: transparent;")
        sizes_layout.addWidget(self.est_lbl)
        sizes_layout.addStretch()
        card_layout.addLayout(sizes_layout)
        layout.addWidget(card)

        # Quality Slider
        slider_box = QVBoxLayout()
        slider_box.setSpacing(8)

        slider_header = QHBoxLayout()
        quality_title = QLabel("Compression Quality")
        quality_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        quality_title.setStyleSheet("color: #cbd5e1; background: transparent;")
        slider_header.addWidget(quality_title)
        slider_header.addStretch()

        self.val_lbl = QLabel("75%")
        self.val_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.val_lbl.setStyleSheet("color: #f8fafc; background: transparent;")
        slider_header.addWidget(self.val_lbl)
        slider_box.addLayout(slider_header)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(20, 95)
        self.slider.setValue(75)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: rgba(255, 255, 255, 0.12);
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: rgba(255, 255, 255, 0.5);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid rgba(0, 0, 0, 0.2);
                width: 18px;
                margin-top: -6px;
                margin-bottom: -6px;
                border-radius: 9px;
            }
        """)
        self.slider.valueChanged.connect(self.on_slider_changed)
        slider_box.addWidget(self.slider)
        layout.addLayout(slider_box)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(90, 34)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(MODAL_BTN_SECONDARY_STYLE)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("Compress")
        apply_btn.setFixedSize(110, 34)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet(MODAL_BTN_PRIMARY_STYLE)
        apply_btn.clicked.connect(self.apply_compression)
        btn_layout.addWidget(apply_btn)

        layout.addLayout(btn_layout)
        main_layout.addWidget(self.container)

    def on_slider_changed(self, val: int):
        self.quality = val
        self.val_lbl.setText(f"{val}%")
        self.update_estimated_size()

    def update_estimated_size(self):
        # Heuristic estimation based on quality factor
        ratio = 0.2 + (self.quality / 100.0) * 0.7
        est = int(self.orig_size * ratio)
        reduction = int((1 - est / self.orig_size) * 100)
        self.est_lbl.setText(f"Estimated: ~{format_file_size(est)} (-{reduction}%)")

    def apply_compression(self):
        ext = self.file_path.suffix.lower()
        out_path = self.file_path.parent / f"{self.file_path.stem} Compressed{self.file_path.suffix}"
        counter = 1
        while out_path.exists():
            out_path = self.file_path.parent / f"{self.file_path.stem} Compressed ({counter}){self.file_path.suffix}"
            counter += 1

        try:
            if ext in ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'):
                with Image.open(self.file_path) as img:
                    if ext in ('.jpg', '.jpeg'):
                        img.convert('RGB').save(out_path, quality=self.quality, optimize=True)
                    elif ext == '.webp':
                        img.save(out_path, 'WEBP', quality=self.quality, method=6)
                    elif ext == '.png':
                        # Convert to indexed palette if quality is lower, or optimize PNG
                        if self.quality < 65:
                            quantized = img.convert('RGB').quantize(colors=128)
                            quantized.save(out_path, optimize=True)
                        else:
                            img.save(out_path, optimize=True)
                    else:
                        img.save(out_path)

            elif ext == '.pdf':
                doc = pymupdf.open(str(self.file_path))
                # Save with compression options in PyMuPDF
                doc.save(str(out_path), deflate=True, garbage=4, clean=True)
                doc.close()

            self.compressed_result = str(out_path)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Compression Failed", f"Could not compress file: {str(e)}")
