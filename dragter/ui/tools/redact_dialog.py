"""Sensitive Data Redaction Dialog (Blackout and Blur)."""

from pathlib import Path
from typing import Optional, List
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFrame, QMessageBox, QRadioButton
)
from PIL import Image, ImageFilter, ImageDraw
from dragter.ui.theme import MODAL_BTN_PRIMARY_STYLE, MODAL_BTN_SECONDARY_STYLE, get_tool_icon_pixmap


class RedactCanvas(QWidget):
    """Interactive canvas to draw censor bars or blur boxes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap: Optional[QPixmap] = None
        self.image_path: Optional[str] = None
        self.redactions: List[dict] = []  # List of {'rect': QRectF, 'mode': 'black' | 'blur'}
        self.current_mode = 'black'
        self.drawing = False
        self.start_pt = QPointF()
        self.current_pt = QPointF()
        self.image_rect = QRectF()

    def load_image(self, path: str):
        self.image_path = path
        self.pixmap = QPixmap(path)
        self.redactions.clear()
        self.update_geometry()
        self.update()

    def update_geometry(self):
        if not self.pixmap or self.width() <= 20 or self.height() <= 20:
            return
        w, h = self.width() - 40, self.height() - 40
        self.display_pixmap = self.pixmap.scaled(
            int(w), int(h),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        x = (self.width() - self.display_pixmap.width()) / 2
        y = (self.height() - self.display_pixmap.height()) / 2
        self.image_rect = QRectF(x, y, self.display_pixmap.width(), self.display_pixmap.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_geometry()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.image_rect.contains(event.position()):
            self.drawing = True
            self.start_pt = event.position()
            self.current_pt = event.position()
            self.update()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.current_pt = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.drawing and event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            rect = QRectF(self.start_pt, self.current_pt).normalized()
            # Intersect with image rect
            rect = rect.intersected(self.image_rect)
            if rect.width() > 5 and rect.height() > 5:
                self.redactions.append({'rect': rect, 'mode': self.current_mode})
            self.update()

    def undo(self):
        if self.redactions:
            self.redactions.pop()
            self.update()

    def clear(self):
        self.redactions.clear()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not hasattr(self, 'display_pixmap') or not self.display_pixmap:
            return

        painter.drawPixmap(int(self.image_rect.x()), int(self.image_rect.y()), self.display_pixmap)

        # Draw existing redaction boxes
        for item in self.redactions:
            r = item['rect']
            if item['mode'] == 'black':
                painter.fillRect(r, QColor(0, 0, 0, 240))
                painter.setPen(QPen(QColor(245, 110, 30, 200), 1))
                painter.drawRect(r)
            else:
                # Blur representation
                painter.fillRect(r, QColor(160, 160, 160, 200))
                painter.setPen(QPen(QColor(255, 255, 255, 180), 1, Qt.PenStyle.DashLine))
                painter.drawRect(r)

        # Draw active box while dragging
        if self.drawing:
            active_rect = QRectF(self.start_pt, self.current_pt).normalized().intersected(self.image_rect)
            color = QColor(0, 0, 0, 180) if self.current_mode == 'black' else QColor(180, 180, 180, 180)
            painter.fillRect(active_rect, color)
            painter.setPen(QPen(QColor(255, 255, 255, 220), 2, Qt.PenStyle.DashLine))
            painter.drawRect(active_rect)

    def save_redacted(self) -> Optional[str]:
        if not self.image_path:
            return None

        with Image.open(self.image_path) as img:
            orig = img.convert('RGB')
        orig_w, orig_h = orig.size
        scale_x = orig_w / self.image_rect.width()
        scale_y = orig_h / self.image_rect.height()

        draw = ImageDraw.Draw(orig)

        for item in self.redactions:
            r = item['rect']
            left = int(round((r.left() - self.image_rect.left()) * scale_x))
            top = int(round((r.top() - self.image_rect.top()) * scale_y))
            right = int(round((r.right() - self.image_rect.left()) * scale_x))
            bottom = int(round((r.bottom() - self.image_rect.top()) * scale_y))

            if item['mode'] == 'black':
                draw.rectangle([left, top, right, bottom], fill=(0, 0, 0))
            else:
                # Blur crop area
                crop_box = (left, top, right, bottom)
                cropped = orig.crop(crop_box)
                blurred = cropped.filter(ImageFilter.GaussianBlur(radius=15))
                orig.paste(blurred, crop_box)

        src_path = Path(self.image_path)
        out_path = src_path.parent / f"{src_path.stem} Redacted{src_path.suffix}"
        counter = 1
        while out_path.exists():
            out_path = src_path.parent / f"{src_path.stem} Redacted ({counter}){src_path.suffix}"
            counter += 1

        orig.save(str(out_path), quality=95)
        return str(out_path)


class RedactDialog(QDialog):
    """The Redaction tool modal window."""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.redacted_result: Optional[str] = None

        self.setWindowTitle("Redact Information")
        self.setMinimumSize(800, 680)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setup_ui()
        self.canvas.load_image(image_path)

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
        icon_pm = get_tool_icon_pixmap('redact', 26)
        if icon_pm:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_pm)
            icon_lbl.setStyleSheet("background: transparent;")
            header.addWidget(icon_lbl)
        title = QLabel("Redact & Censor")
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

        # Canvas
        self.canvas = RedactCanvas(self)
        self.canvas.setStyleSheet("background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px;")
        layout.addWidget(self.canvas)

        # Bottom Bar
        controls = QHBoxLayout()
        hint = QLabel("Drag rectangles over sensitive text or areas")
        hint.setStyleSheet("color: #94a3b8; font-weight: 500; background: transparent;")
        controls.addWidget(hint)
        controls.addSpacing(16)

        # Radio mode buttons
        self.radio_black = QRadioButton("Blackout")
        self.radio_black.setChecked(True)
        self.radio_black.setStyleSheet("color: #f1f5f9; font-weight: bold;")
        self.radio_black.toggled.connect(lambda checked: self.set_mode('black') if checked else None)
        controls.addWidget(self.radio_black)

        self.radio_blur = QRadioButton("Blur")
        self.radio_blur.setStyleSheet("color: #f1f5f9; font-weight: bold;")
        self.radio_blur.toggled.connect(lambda checked: self.set_mode('blur') if checked else None)
        controls.addWidget(self.radio_blur)

        controls.addStretch()

        undo_btn = QPushButton("Undo")
        undo_btn.setFixedSize(70, 32)
        undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        undo_btn.setFixedSize(80, 32)
        undo_btn.setStyleSheet(MODAL_BTN_SECONDARY_STYLE)
        undo_btn.clicked.connect(self.canvas.undo)
        controls.addWidget(undo_btn)

        apply_btn = QPushButton("Save Redacted")
        apply_btn.setFixedSize(120, 32)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet(MODAL_BTN_PRIMARY_STYLE)
        apply_btn.clicked.connect(self.on_apply)
        controls.addWidget(apply_btn)

        layout.addLayout(controls)
        main_layout.addWidget(self.container)

    def set_mode(self, mode: str):
        self.canvas.current_mode = mode

    def on_apply(self):
        res = self.canvas.save_redacted()
        if res:
            self.redacted_result = res
            self.accept()
        else:
            QMessageBox.warning(self, "Redact Error", "Failed to save redacted image.")
