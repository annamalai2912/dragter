"""Metadata and EXIF Inspector & Sanitizer."""

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PIL import Image, ExifTags
import pymupdf
from dragter.ui.theme import MODAL_BTN_PRIMARY_STYLE, MODAL_BTN_SECONDARY_STYLE, get_tool_icon_pixmap


class MetadataDialog(QDialog):
    """View and strip metadata/EXIF tags for privacy."""

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = Path(file_path)
        self.sanitized_result: Optional[str] = None

        self.setWindowTitle("File Metadata")
        self.setFixedSize(560, 460)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setup_ui()
        self.load_metadata()

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
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        icon_pm = get_tool_icon_pixmap('metadata', 26)
        if icon_pm:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_pm)
            icon_lbl.setStyleSheet("background: transparent;")
            header.addWidget(icon_lbl)
        title = QLabel("Metadata Inspector")
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

        # Subtitle
        sub_lbl = QLabel(f"File: {self.file_path.name}")
        sub_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        sub_lbl.setStyleSheet("color: #94a3b8; background: transparent;")
        layout.addWidget(sub_lbl)

        # Table for EXIF attributes
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Attribute", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background: rgba(0, 0, 0, 0.35);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                gridline-color: rgba(255, 255, 255, 0.06);
                color: #e2e8f0;
            }
            QHeaderView::section {
                background: rgba(36, 41, 54, 0.9);
                color: #f8fafc;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
        """)
        layout.addWidget(self.table)

        # Actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Close")
        cancel_btn.setFixedSize(85, 34)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(MODAL_BTN_SECONDARY_STYLE)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        strip_btn = QPushButton("Strip All Metadata")
        strip_btn.setFixedSize(150, 34)
        strip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        strip_btn.setStyleSheet(MODAL_BTN_PRIMARY_STYLE)
        strip_btn.clicked.connect(self.strip_metadata)
        btn_layout.addWidget(strip_btn)

        layout.addLayout(btn_layout)
        main_layout.addWidget(self.container)

    def load_metadata(self):
        ext = self.file_path.suffix.lower()
        items = []

        if ext in ('.png', '.jpg', '.jpeg', '.webp', '.tiff'):
            try:
                with Image.open(self.file_path) as img:
                    items.append(("Format", img.format))
                    items.append(("Dimensions", f"{img.width} x {img.height} px"))
                    items.append(("Color Mode", img.mode))
                    exif_data = img.getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                            val_str = str(value)
                            if len(val_str) > 80:
                                val_str = val_str[:77] + "..."
                            items.append((tag_name, val_str))
            except Exception:
                pass
        elif ext == '.pdf':
            try:
                doc = pymupdf.open(str(self.file_path))
                items.append(("Pages", str(len(doc))))
                for k, v in doc.metadata.items():
                    if v:
                        items.append((k.capitalize(), str(v)))
                doc.close()
            except Exception:
                pass

        if not items:
            items.append(("Notice", "No embedded EXIF / metadata found."))

        self.table.setRowCount(len(items))
        for row, (k, v) in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(k)))
            self.table.setItem(row, 1, QTableWidgetItem(str(v)))

    def strip_metadata(self):
        ext = self.file_path.suffix.lower()
        out_path = self.file_path.parent / f"{self.file_path.stem} Cleaned{self.file_path.suffix}"
        
        counter = 1
        while out_path.exists():
            out_path = self.file_path.parent / f"{self.file_path.stem} Cleaned ({counter}){self.file_path.suffix}"
            counter += 1

        try:
            if ext in ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'):
                with Image.open(self.file_path) as img:
                    # Strip EXIF by saving pure pixel data without metadata dictionary
                    data = list(img.getdata())
                    clean_img = Image.new(img.mode, img.size)
                    clean_img.putdata(data)
                    clean_img.save(out_path)
            elif ext == '.pdf':
                doc = pymupdf.open(str(self.file_path))
                doc.set_metadata({})
                doc.save(str(out_path), clean=True)
                doc.close()

            self.sanitized_result = str(out_path)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Stripping Failed", f"Could not strip metadata: {str(e)}")
