"""QR Code Studio — Scan & Decode QR codes from images, and Generate customizable high-res QR codes."""

import webbrowser
from pathlib import Path
from typing import Optional
import cv2
import qrcode
from PIL import Image

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QComboBox, QSlider,
    QApplication, QFileDialog, QMessageBox, QTabWidget
)

from dragter.ui.theme import (
    MODAL_CONTAINER_STYLE, MODAL_TITLE_STYLE, MODAL_LABEL_STYLE,
    MODAL_CLOSE_STYLE, MODAL_BTN_PRIMARY_STYLE, MODAL_BTN_SECONDARY_STYLE,
    get_tool_icon_pixmap
)


class QrDialog(QDialog):
    """
    Comprehensive QR Code Studio:
    1. Scan & Decode: Reads and decodes any QR code present in dragged images (URLs, WiFi, text).
    2. Generate: Generates high-res QR codes from any text, URL, or file with customizable styling,
       error correction, live preview, 1-click clipboard copy, and file export.
    """

    def __init__(self, file_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.file_path = Path(file_path) if file_path else None
        self.decoded_text: Optional[str] = None
        self.current_qr_image: Optional[Image.Image] = None

        self.setWindowTitle("QR Code Studio")
        self.setMinimumSize(780, 620)
        self.resize(820, 660)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._setup_ui()
        self._initial_process()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        self.container = QFrame()
        self.container.setStyleSheet(MODAL_CONTAINER_STYLE)
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        header.setSpacing(12)
        icon_pm = get_tool_icon_pixmap('qr', 30)
        if icon_pm:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_pm)
            icon_lbl.setStyleSheet("background: transparent;")
            header.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title = QLabel("QR Code Studio")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(MODAL_TITLE_STYLE)
        title_box.addWidget(title)

        subtitle = QLabel("Scan and decode QR codes from images, or generate custom high-resolution codes")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent;")
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(MODAL_CLOSE_STYLE)
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Tabs: Generate QR & Scan / Decode
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 12px;
                background: rgba(14, 16, 20, 0.70);
                padding: 16px;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.05);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 20px;
                font-weight: 600;
                font-size: 13px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: rgba(255, 255, 255, 0.12);
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.22);
            }
            QTabBar::tab:hover:!selected {
                background: rgba(255, 255, 255, 0.08);
                color: #e2e8f0;
            }
        """)

        # Tab 1: Generate QR
        self.tab_generate = QWidget()
        self._setup_generate_tab()
        self.tabs.addTab(self.tab_generate, "Generate QR Code")

        # Tab 2: Scan & Decode QR
        self.tab_scan = QWidget()
        self._setup_scan_tab()
        self.tabs.addTab(self.tab_scan, "Scan & Decode")

        layout.addWidget(self.tabs)
        main_layout.addWidget(self.container)

    def _setup_generate_tab(self):
        tab_layout = QHBoxLayout(self.tab_generate)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(24)

        # Left Column: Configuration Controls
        controls_col = QVBoxLayout()
        controls_col.setSpacing(14)

        # Text / URL Input
        lbl_content = QLabel("Content / URL / Text:")
        lbl_content.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_content.setStyleSheet(MODAL_LABEL_STYLE)
        controls_col.addWidget(lbl_content)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter URL, link, text, contact info, or Wi-Fi configuration...")
        self.input_text.setFixedHeight(95)
        self.input_text.setStyleSheet("""
            QTextEdit {
                background: rgba(0, 0, 0, 0.40);
                color: #f8fafc;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Segoe UI', monospace;
                font-size: 12px;
            }
            QTextEdit:focus {
                border: 1px solid rgba(255, 255, 255, 0.35);
            }
        """)
        self.input_text.textChanged.connect(self.update_qr_preview)
        controls_col.addWidget(self.input_text)

        # Quick Links / Presets
        presets_row = QHBoxLayout()
        presets_row.setSpacing(8)
        for label, prefix in [("URL (https://)", "https://"), ("Wi-Fi", "WIFI:S:MyNetwork;T:WPA;P:MyPassword;;"), ("Email", "mailto:user@example.com")]:
            btn = QPushButton(label)
            btn.setFixedHeight(26)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.06);
                    color: #cbd5e1;
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 6px;
                    font-size: 11px;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.12);
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, p=prefix: self._insert_preset(p))
            presets_row.addWidget(btn)
        presets_row.addStretch()
        controls_col.addLayout(presets_row)

        # Theme & Color Preset
        theme_row = QHBoxLayout()
        theme_lbl = QLabel("Color Theme:")
        theme_lbl.setStyleSheet(MODAL_LABEL_STYLE)
        theme_row.addWidget(theme_lbl)

        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Classic (Black on White)", "Dark Titanium (White on Dark)", "Inverted (Black on Transparent)"])
        self.combo_theme.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.08);
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
        """)
        self.combo_theme.currentIndexChanged.connect(self.update_qr_preview)
        theme_row.addWidget(self.combo_theme)
        controls_col.addLayout(theme_row)

        # Error Correction Level
        ec_row = QHBoxLayout()
        ec_lbl = QLabel("Error Correction:")
        ec_lbl.setStyleSheet(MODAL_LABEL_STYLE)
        ec_row.addWidget(ec_lbl)

        self.combo_ec = QComboBox()
        self.combo_ec.addItems(["Medium (15% - Recommended)", "Low (7% - Compact)", "Quartile (25% - Robust)", "High (30% - Maximum)"])
        self.combo_ec.setStyleSheet(self.combo_theme.styleSheet())
        self.combo_ec.currentIndexChanged.connect(self.update_qr_preview)
        ec_row.addWidget(self.combo_ec)
        controls_col.addLayout(ec_row)

        # Size / Scale Slider
        size_row = QHBoxLayout()
        self.lbl_size = QLabel("Box Resolution: 10")
        self.lbl_size.setStyleSheet(MODAL_LABEL_STYLE)
        size_row.addWidget(self.lbl_size)

        self.slider_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_size.setRange(5, 25)
        self.slider_size.setValue(10)
        self.slider_size.valueChanged.connect(self._on_size_slider_changed)
        size_row.addWidget(self.slider_size)
        controls_col.addLayout(size_row)

        controls_col.addStretch()

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        copy_btn = QPushButton("Copy Image")
        copy_btn.setFixedHeight(34)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(MODAL_BTN_SECONDARY_STYLE)
        copy_btn.clicked.connect(self.copy_qr_image)
        btn_row.addWidget(copy_btn)

        save_btn = QPushButton("Save QR (PNG)")
        save_btn.setFixedHeight(34)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(MODAL_BTN_PRIMARY_STYLE)
        save_btn.clicked.connect(self.save_qr_image)
        btn_row.addWidget(save_btn)

        controls_col.addLayout(btn_row)
        tab_layout.addLayout(controls_col, stretch=3)

        # Right Column: High-Res QR Code Preview Card
        preview_col = QVBoxLayout()
        preview_col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        preview_frame = QFrame()
        preview_frame.setFixedSize(290, 290)
        preview_frame.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.45);
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 12px;
            }
        """)
        pf_layout = QVBoxLayout(preview_frame)
        pf_layout.setContentsMargins(12, 12, 12, 12)
        pf_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.qr_preview_lbl = QLabel()
        self.qr_preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pf_layout.addWidget(self.qr_preview_lbl)
        preview_col.addWidget(preview_frame)

        self.lbl_dims = QLabel("Dimensions: —")
        self.lbl_dims.setStyleSheet("color: #64748b; font-size: 11px; margin-top: 6px;")
        self.lbl_dims.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_col.addWidget(self.lbl_dims)

        tab_layout.addLayout(preview_col, stretch=2)

    def _setup_scan_tab(self):
        tab_layout = QVBoxLayout(self.tab_scan)
        tab_layout.setContentsMargins(14, 14, 14, 14)
        tab_layout.setSpacing(16)

        # Status & Image Info Bar
        info_bar = QHBoxLayout()
        self.scan_status_badge = QLabel("Status: Idle")
        self.scan_status_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.scan_status_badge.setStyleSheet("color: #94a3b8;")
        info_bar.addWidget(self.scan_status_badge)

        info_bar.addStretch()

        browse_btn = QPushButton("Scan Another Image...")
        browse_btn.setFixedHeight(30)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(MODAL_BTN_SECONDARY_STYLE)
        browse_btn.clicked.connect(self._browse_and_scan_image)
        info_bar.addWidget(browse_btn)

        tab_layout.addLayout(info_bar)

        # Decoded Content Card
        lbl_decoded = QLabel("Decoded QR Content:")
        lbl_decoded.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_decoded.setStyleSheet(MODAL_LABEL_STYLE)
        tab_layout.addWidget(lbl_decoded)

        self.scan_result_text = QTextEdit()
        self.scan_result_text.setReadOnly(True)
        self.scan_result_text.setStyleSheet("""
            QTextEdit {
                background: rgba(0, 0, 0, 0.40);
                color: #f8fafc;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 8px;
                padding: 12px;
                font-family: 'Consolas', 'Segoe UI', monospace;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        tab_layout.addWidget(self.scan_result_text)

        # Actions for Decoded Content
        scan_btn_row = QHBoxLayout()
        scan_btn_row.setSpacing(12)

        self.btn_open_url = QPushButton("Open Link in Browser")
        self.btn_open_url.setFixedHeight(34)
        self.btn_open_url.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_url.setStyleSheet(MODAL_BTN_PRIMARY_STYLE)
        self.btn_open_url.setEnabled(False)
        self.btn_open_url.clicked.connect(self._open_decoded_url)
        scan_btn_row.addWidget(self.btn_open_url)

        self.btn_copy_decoded = QPushButton("Copy Decoded Text")
        self.btn_copy_decoded.setFixedHeight(34)
        self.btn_copy_decoded.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_decoded.setStyleSheet(MODAL_BTN_SECONDARY_STYLE)
        self.btn_copy_decoded.setEnabled(False)
        self.btn_copy_decoded.clicked.connect(self._copy_decoded_text)
        scan_btn_row.addWidget(self.btn_copy_decoded)

        self.btn_use_in_generator = QPushButton("Send to Generator")
        self.btn_use_in_generator.setFixedHeight(34)
        self.btn_use_in_generator.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_use_in_generator.setStyleSheet(MODAL_BTN_SECONDARY_STYLE)
        self.btn_use_in_generator.setEnabled(False)
        self.btn_use_in_generator.clicked.connect(self._send_to_generator)
        scan_btn_row.addWidget(self.btn_use_in_generator)

        scan_btn_row.addStretch()
        tab_layout.addLayout(scan_btn_row)

    def _insert_preset(self, text: str):
        self.input_text.setPlainText(text)

    def _on_size_slider_changed(self, val: int):
        self.lbl_size.setText(f"Box Resolution: {val}")
        self.update_qr_preview()

    def _initial_process(self):
        """Intelligently inspect input file: scan image or pre-populate generator."""
        if not self.file_path or not self.file_path.exists():
            self.input_text.setPlainText("https://github.com")
            self.update_qr_preview()
            return

        ext = self.file_path.suffix.lower()
        image_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif', '.gif'}

        if ext in image_exts:
            # First attempt to decode QR from image
            found = self._scan_image_file(str(self.file_path))
            if found:
                self.tabs.setCurrentIndex(1)  # Focus Scan & Decode tab
            else:
                # No QR found in image: switch to generate and populate path
                self.input_text.setPlainText(str(self.file_path.name))
                self.update_qr_preview()
                self.tabs.setCurrentIndex(0)
        else:
            # Text / Document / PDF file: populate generator with text or path
            try:
                if ext in ('.txt', '.md', '.rtf', '.csv', '.json', '.xml', '.log'):
                    content = self.file_path.read_text(encoding='utf-8', errors='ignore')
                    self.input_text.setPlainText(content[:800].strip())
                else:
                    self.input_text.setPlainText(str(self.file_path.resolve()))
            except Exception:
                self.input_text.setPlainText(str(self.file_path.resolve()))
            self.update_qr_preview()
            self.tabs.setCurrentIndex(0)

    def _scan_image_file(self, img_path: str) -> bool:
        """Scan and decode QR code from an image using OpenCV."""
        try:
            img = cv2.imread(img_path)
            if img is None:
                # Attempt Pillow fallback for format OpenCV might not open directly
                pil_img = Image.open(img_path).convert('RGB')
                import numpy as np
                img = np.array(pil_img)[:, :, ::-1].copy()

            # Accelerate scan for high-res images to under 20ms
            h, w = img.shape[:2]
            max_dim = max(h, w)
            if max_dim > 1200:
                scale = 1200.0 / max_dim
                scan_img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            else:
                scan_img = img

            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(scan_img)
            if (not data or not data.strip()) and max_dim > 1200:
                data, bbox, _ = detector.detectAndDecode(img)

            if data and data.strip():
                self.decoded_text = data.strip()
                self.scan_status_badge.setText("Status: ✓ QR Code Successfully Detected")
                self.scan_status_badge.setStyleSheet("color: #34d399; font-weight: bold;")
                self.scan_result_text.setPlainText(self.decoded_text)
                self.btn_copy_decoded.setEnabled(True)
                self.btn_use_in_generator.setEnabled(True)
                if self.decoded_text.startswith(('http://', 'https://')):
                    self.btn_open_url.setEnabled(True)
                else:
                    self.btn_open_url.setEnabled(False)
                return True
            else:
                self.scan_status_badge.setText(f"Status: No QR code found in {Path(img_path).name}")
                self.scan_status_badge.setStyleSheet("color: #94a3b8;")
                self.scan_result_text.setPlainText("No valid QR code was detected in this image.\n\nYou can switch to the 'Generate QR Code' tab to create a custom QR code.")
                self.btn_open_url.setEnabled(False)
                self.btn_copy_decoded.setEnabled(False)
                self.btn_use_in_generator.setEnabled(False)
                return False
        except Exception as e:
            self.scan_status_badge.setText(f"Scan Error: {str(e)}")
            self.scan_status_badge.setStyleSheet("color: #f87171;")
            return False

    def _browse_and_scan_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image to Scan", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;All Files (*.*)"
        )
        if file_path:
            self._scan_image_file(file_path)

    def _open_decoded_url(self):
        if self.decoded_text and self.decoded_text.startswith(('http://', 'https://')):
            webbrowser.open(self.decoded_text)

    def _copy_decoded_text(self):
        if self.decoded_text:
            QApplication.clipboard().setText(self.decoded_text)
            self.scan_status_badge.setText("Status: ✓ Copied to Clipboard!")

    def _send_to_generator(self):
        if self.decoded_text:
            self.input_text.setPlainText(self.decoded_text)
            self.tabs.setCurrentIndex(0)

    def update_qr_preview(self):
        """Generate QR image and update live preview widget."""
        text = self.input_text.toPlainText().strip()
        if not text:
            text = " "

        # Map error correction
        ec_idx = self.combo_ec.currentIndex()
        ec_map = {
            0: qrcode.constants.ERROR_CORRECT_M,
            1: qrcode.constants.ERROR_CORRECT_L,
            2: qrcode.constants.ERROR_CORRECT_Q,
            3: qrcode.constants.ERROR_CORRECT_H
        }
        ec_level = ec_map.get(ec_idx, qrcode.constants.ERROR_CORRECT_M)

        # Map colors
        theme_idx = self.combo_theme.currentIndex()
        if theme_idx == 1:
            # Dark Titanium: White QR on dark background
            fill_color = "#ffffff"
            back_color = "#181b22"
        elif theme_idx == 2:
            # Inverted: Black on Transparent / Light
            fill_color = "#0e1014"
            back_color = "#f1f5f9"
        else:
            # Classic
            fill_color = "black"
            back_color = "white"

        box_size = self.slider_size.value()

        try:
            qr = qrcode.QRCode(
                version=None,
                error_correction=ec_level,
                box_size=box_size,
                border=4
            )
            qr.add_data(text)
            qr.make(fit=True)
            pil_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGBA')
            self.current_qr_image = pil_img

            self.lbl_dims.setText(f"Dimensions: {pil_img.width} × {pil_img.height} px")

            # Convert to QPixmap for preview
            data = pil_img.tobytes("raw", "RGBA")
            qimg = QImage(data, pil_img.width, pil_img.height, pil_img.width * 4, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg).scaled(
                260, 260,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.qr_preview_lbl.setPixmap(pixmap)
        except Exception as e:
            self.lbl_dims.setText(f"Error: {e}")

    def copy_qr_image(self):
        """Copy generated QR code image directly to system clipboard."""
        if not self.current_qr_image:
            return
        data = self.current_qr_image.tobytes("raw", "RGBA")
        qimg = QImage(
            data, self.current_qr_image.width, self.current_qr_image.height,
            self.current_qr_image.width * 4, QImage.Format.Format_RGBA8888
        )
        QApplication.clipboard().setImage(qimg)
        QMessageBox.information(self, "QR Copied", "QR Code image has been copied to your clipboard!")

    def save_qr_image(self):
        """Export high-resolution QR code PNG image."""
        if not self.current_qr_image:
            return

        default_dir = self.file_path.parent if self.file_path else Path.home() / "Desktop"
        default_name = f"{self.file_path.stem}_qr.png" if self.file_path else "qr_code.png"
        default_target = default_dir / default_name

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save QR Code Image", str(default_target), "PNG Image (*.png);;All Files (*.*)"
        )
        if save_path:
            out_path = Path(save_path)
            self.current_qr_image.save(out_path, format="PNG")
            QMessageBox.information(self, "QR Saved", f"Saved successfully to:\n{out_path.name}")
            self.accept()
