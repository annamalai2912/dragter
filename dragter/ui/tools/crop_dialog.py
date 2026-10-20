"""Interactive Image Cropping Dialog matching the visual design from Image 5."""

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPixmap, QFont, QCursor, QIntValidator
)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QWidget, QFrame, QSizePolicy, QMessageBox
)
from PIL import Image
from dragter.ui.theme import MODAL_BTN_PRIMARY_STYLE, MODAL_BTN_SECONDARY_STYLE, get_tool_icon_pixmap


class CropCanvas(QWidget):
    """Interactive canvas with movable/resizable crop box, dim mask, and grid lines."""
    cropChanged = pyqtSignal(int, int)  # Emits original image cropped width, height

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.original_image: Optional[Image.Image] = None
        self.pixmap: Optional[QPixmap] = None
        self.image_rect = QRectF()
        self.crop_rect = QRectF()
        
        self.aspect_ratio: Optional[float] = None  # None = Free
        self.lock_aspect = False
        
        self.handle_size = 10
        self.active_handle = None
        self.drag_start_pos = QPointF()
        self.drag_start_crop = QRectF()

    def load_image(self, image_path: str):
        self.image_path = image_path
        with Image.open(image_path) as img:
            self.original_image = img.copy()
        self.orig_w, self.orig_h = self.original_image.size
        self.pixmap = QPixmap(image_path)
        canvas_w = max(400, self.width() - 40) if self.width() > 20 else 720
        canvas_h = max(300, self.height() - 40) if self.height() > 20 else 460
        scaled = self.pixmap.scaled(
            int(canvas_w), int(canvas_h),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.display_pixmap = scaled
        x = (canvas_w - scaled.width()) / 2 + 20
        y = (canvas_h - scaled.height()) / 2 + 20
        self.image_rect = QRectF(x, y, scaled.width(), scaled.height())
        self.reset_crop()

    def set_aspect_ratio(self, ratio: Optional[float]):
        self.aspect_ratio = ratio
        if ratio is not None and not self.crop_rect.isEmpty():
            cx, cy = self.crop_rect.center().x(), self.crop_rect.center().y()
            current_w = self.crop_rect.width()
            target_h = current_w / ratio
            if target_h > self.image_rect.height():
                target_h = self.image_rect.height() * 0.8
                target_w = target_h * ratio
            else:
                target_w = current_w

            new_rect = QRectF(cx - target_w / 2, cy - target_h / 2, target_w, target_h)
            self.crop_rect = self.clamp_rect(new_rect)
            self.notify_crop_change()
            self.update()

    def set_custom_size(self, target_orig_w: int, target_orig_h: int):
        if not self.original_image or self.image_rect.isEmpty():
            return
        target_orig_w = max(10, min(self.orig_w, target_orig_w))
        target_orig_h = max(10, min(self.orig_h, target_orig_h))

        scale_x = self.image_rect.width() / max(1.0, self.orig_w)
        scale_y = self.image_rect.height() / max(1.0, self.orig_h)

        w = target_orig_w * scale_x
        h = target_orig_h * scale_y

        cx = self.crop_rect.center().x() if not self.crop_rect.isEmpty() else self.image_rect.center().x()
        cy = self.crop_rect.center().y() if not self.crop_rect.isEmpty() else self.image_rect.center().y()

        new_rect = QRectF(cx - w / 2, cy - h / 2, w, h)
        self.crop_rect = self.clamp_rect(new_rect)
        self.notify_crop_change()
        self.update()

    def reset_crop(self):
        if self.image_rect.isEmpty():
            return
        # Default to 80% of centered image
        w = self.image_rect.width() * 0.85
        h = self.image_rect.height() * 0.85
        if self.aspect_ratio is not None:
            if w / self.aspect_ratio <= self.image_rect.height():
                h = w / self.aspect_ratio
            else:
                w = h * self.aspect_ratio

        cx, cy = self.image_rect.center().x(), self.image_rect.center().y()
        self.crop_rect = QRectF(cx - w / 2, cy - h / 2, w, h)
        self.notify_crop_change()
        self.update()

    def update_geometry(self):
        if not self.pixmap or self.width() <= 20 or self.height() <= 20:
            return
        
        canvas_w, canvas_h = self.width() - 40, self.height() - 40
        scaled = self.pixmap.scaled(
            int(canvas_w), int(canvas_h),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.display_pixmap = scaled
        x = (self.width() - scaled.width()) / 2
        y = (self.height() - scaled.height()) / 2
        self.image_rect = QRectF(x, y, scaled.width(), scaled.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        prev_img_rect = QRectF(self.image_rect)
        self.update_geometry()
        if not prev_img_rect.isEmpty() and not self.image_rect.isEmpty():
            # Re-scale crop rect proportionally
            scale_x = self.image_rect.width() / prev_img_rect.width()
            scale_y = self.image_rect.height() / prev_img_rect.height()
            rx = self.image_rect.x() + (self.crop_rect.x() - prev_img_rect.x()) * scale_x
            ry = self.image_rect.y() + (self.crop_rect.y() - prev_img_rect.y()) * scale_y
            rw = self.crop_rect.width() * scale_x
            rh = self.crop_rect.height() * scale_y
            self.crop_rect = self.clamp_rect(QRectF(rx, ry, rw, rh))
            self.notify_crop_change()

    def clamp_rect(self, rect: QRectF) -> QRectF:
        r = QRectF(rect)
        if r.width() < 30:
            r.setWidth(30)
        if r.height() < 30:
            r.setHeight(30)
        if r.left() < self.image_rect.left():
            r.moveLeft(self.image_rect.left())
        if r.top() < self.image_rect.top():
            r.moveTop(self.image_rect.top())
        if r.right() > self.image_rect.right():
            r.moveRight(self.image_rect.right())
        if r.bottom() > self.image_rect.bottom():
            r.moveBottom(self.image_rect.bottom())
        return r

    def notify_crop_change(self):
        if self.image_rect.isEmpty() or not self.original_image:
            return
        orig_w, orig_h = self.original_image.size
        factor_x = orig_w / self.image_rect.width()
        factor_y = orig_h / self.image_rect.height()
        w = int(round(self.crop_rect.width() * factor_x))
        h = int(round(self.crop_rect.height() * factor_y))
        self.cropChanged.emit(max(1, w), max(1, h))

    def get_handles(self):
        r = self.crop_rect
        hs = self.handle_size
        return {
            'tl': QRectF(r.left() - hs / 2, r.top() - hs / 2, hs, hs),
            'tr': QRectF(r.right() - hs / 2, r.top() - hs / 2, hs, hs),
            'bl': QRectF(r.left() - hs / 2, r.bottom() - hs / 2, hs, hs),
            'br': QRectF(r.right() - hs / 2, r.bottom() - hs / 2, hs, hs),
            't': QRectF(r.center().x() - hs / 2, r.top() - hs / 2, hs, hs),
            'b': QRectF(r.center().x() - hs / 2, r.bottom() - hs / 2, hs, hs),
            'l': QRectF(r.left() - hs / 2, r.center().y() - hs / 2, hs, hs),
            'r': QRectF(r.right() - hs / 2, r.center().y() - hs / 2, hs, hs),
        }

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.crop_rect.isEmpty():
            pos = event.position()
            handles = self.get_handles()
            for key, h_rect in handles.items():
                if h_rect.contains(pos):
                    self.active_handle = key
                    self.drag_start_pos = pos
                    self.drag_start_crop = QRectF(self.crop_rect)
                    return

            if self.crop_rect.contains(pos):
                self.active_handle = 'move'
                self.drag_start_pos = pos
                self.drag_start_crop = QRectF(self.crop_rect)

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self.active_handle:
            dx = pos.x() - self.drag_start_pos.x()
            dy = pos.y() - self.drag_start_pos.y()
            r = QRectF(self.drag_start_crop)

            if self.active_handle == 'move':
                r.translate(dx, dy)
                self.crop_rect = self.clamp_rect(r)
            else:
                # Handle corner/edge resizing
                if 'r' in self.active_handle:
                    r.setRight(min(self.image_rect.right(), r.right() + dx))
                if 'l' in self.active_handle:
                    r.setLeft(max(self.image_rect.left(), r.left() + dx))
                if 'b' in self.active_handle:
                    r.setBottom(min(self.image_rect.bottom(), r.bottom() + dy))
                if 't' in self.active_handle:
                    r.setTop(max(self.image_rect.top(), r.top() + dy))

                # Normalize in case flipped
                r = r.normalized()
                if self.aspect_ratio is not None:
                    # Enforce aspect ratio
                    if 'r' in self.active_handle or 'l' in self.active_handle:
                        new_h = r.width() / self.aspect_ratio
                        r.setHeight(new_h)
                    else:
                        new_w = r.height() * self.aspect_ratio
                        r.setWidth(new_w)

                self.crop_rect = self.clamp_rect(r)

            self.notify_crop_change()
            self.update()
        else:
            # Update cursor shape based on hover
            handles = self.get_handles()
            for key, h_rect in handles.items():
                if h_rect.contains(pos):
                    cursors = {
                        'tl': Qt.CursorShape.SizeFDiagCursor,
                        'br': Qt.CursorShape.SizeFDiagCursor,
                        'tr': Qt.CursorShape.SizeBDiagCursor,
                        'bl': Qt.CursorShape.SizeBDiagCursor,
                        't': Qt.CursorShape.SizeVerCursor,
                        'b': Qt.CursorShape.SizeVerCursor,
                        'l': Qt.CursorShape.SizeHorCursor,
                        'r': Qt.CursorShape.SizeHorCursor,
                    }
                    self.setCursor(QCursor(cursors.get(key, Qt.CursorShape.ArrowCursor)))
                    return
            if self.crop_rect.contains(pos):
                self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mouseReleaseEvent(self, event):
        self.active_handle = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not hasattr(self, 'display_pixmap') or not self.display_pixmap:
            return

        # Draw the scaled image
        painter.drawPixmap(int(self.image_rect.x()), int(self.image_rect.y()), self.display_pixmap)

        # Draw outer dim mask
        mask_color = QColor(0, 0, 0, 160)
        # Top
        painter.fillRect(QRectF(self.image_rect.left(), self.image_rect.top(),
                                self.image_rect.width(), self.crop_rect.top() - self.image_rect.top()), mask_color)
        # Bottom
        painter.fillRect(QRectF(self.image_rect.left(), self.crop_rect.bottom(),
                                self.image_rect.width(), self.image_rect.bottom() - self.crop_rect.bottom()), mask_color)
        # Left
        painter.fillRect(QRectF(self.image_rect.left(), self.crop_rect.top(),
                                self.crop_rect.left() - self.image_rect.left(), self.crop_rect.height()), mask_color)
        # Right
        painter.fillRect(QRectF(self.crop_rect.right(), self.crop_rect.top(),
                                self.image_rect.right() - self.crop_rect.right(), self.crop_rect.height()), mask_color)

        # Draw crop border in clean crisp white
        border_pen = QPen(QColor(255, 255, 255, 230), 2.0)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.crop_rect)

        # Draw rule of thirds grid lines
        grid_pen = QPen(QColor(255, 255, 255, 60), 1, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        cw, ch = self.crop_rect.width(), self.crop_rect.height()
        cl, ct = self.crop_rect.left(), self.crop_rect.top()
        painter.drawLine(QPointF(cl + cw / 3, ct), QPointF(cl + cw / 3, ct + ch))
        painter.drawLine(QPointF(cl + 2 * cw / 3, ct), QPointF(cl + 2 * cw / 3, ct + ch))
        painter.drawLine(QPointF(cl, ct + ch / 3), QPointF(cl + cw, ct + ch / 3))
        painter.drawLine(QPointF(cl, ct + 2 * ch / 3), QPointF(cl + cw, ct + 2 * ch / 3))

        # Draw handles (clean white corner accents)
        handle_pen = QPen(QColor(0, 0, 0, 160), 1.5)
        handle_brush = QBrush(QColor(255, 255, 255))
        painter.setPen(handle_pen)
        painter.setBrush(handle_brush)
        for h_rect in self.get_handles().values():
            painter.drawRoundedRect(h_rect, 2, 2)

    def crop_and_save(self) -> Optional[str]:
        """Crop original full-res image and save as [Stem] Cropped.[ext]."""
        if not self.original_image or self.crop_rect.isEmpty():
            return None

        orig_w, orig_h = self.original_image.size
        factor_x = orig_w / self.image_rect.width()
        factor_y = orig_h / self.image_rect.height()

        left = int(round((self.crop_rect.left() - self.image_rect.left()) * factor_x))
        top = int(round((self.crop_rect.top() - self.image_rect.top()) * factor_y))
        right = int(round((self.crop_rect.right() - self.image_rect.left()) * factor_x))
        bottom = int(round((self.crop_rect.bottom() - self.image_rect.top()) * factor_y))

        # Clamp bounds
        left = max(0, min(orig_w - 1, left))
        top = max(0, min(orig_h - 1, top))
        right = max(left + 1, min(orig_w, right))
        bottom = max(top + 1, min(orig_h, bottom))

        cropped = self.original_image.crop((left, top, right, bottom))
        
        src_path = Path(self.image_path)
        out_path = src_path.parent / f"{src_path.stem} Cropped{src_path.suffix}"
        
        counter = 1
        while out_path.exists():
            out_path = src_path.parent / f"{src_path.stem} Cropped ({counter}){src_path.suffix}"
            counter += 1

        cropped.save(str(out_path), quality=95)
        return str(out_path)


class CropDialog(QDialog):
    """The modern floating Crop Modal window exactly matching Image 5."""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.cropped_result: Optional[str] = None
        self.aspect_buttons = {}

        self.setWindowTitle("Crop Image")
        self.setMinimumSize(780, 680)
        self.resize(840, 720)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setup_ui()
        self.canvas.load_image(image_path)

    def setup_ui(self):
        # Outer acrylic glass container
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            #container {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(26, 29, 39, 0.98),
                    stop:1 rgba(15, 17, 23, 0.99));
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 20px;
            }
        """)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 16, 20, 20)
        container_layout.setSpacing(14)

        # Header Bar
        header = QHBoxLayout()
        header.setContentsMargins(4, 0, 4, 0)
        header.setSpacing(10)

        icon_pm = get_tool_icon_pixmap('crop', 26)
        if icon_pm:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_pm)
            icon_lbl.setStyleSheet("background: transparent;")
            header.addWidget(icon_lbl)
        
        title = QLabel("Crop Image")
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
        container_layout.addLayout(header)

        # Canvas Preview
        self.canvas = CropCanvas(self)
        self.canvas.cropChanged.connect(self.on_crop_changed)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.setStyleSheet("background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px;")
        container_layout.addWidget(self.canvas)

        # Bottom Controls Panel
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(4, 0, 4, 0)
        controls_layout.setSpacing(12)

        # Aspect Ratio Label
        ar_label = QLabel("Aspect ratio")
        ar_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        ar_label.setStyleSheet("color: #cbd5e1; background: transparent;")
        controls_layout.addWidget(ar_label)

        # Aspect Ratio Pill Buttons
        pill_group = QFrame()
        pill_group.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 18px;
                padding: 2px;
            }
        """)
        pill_layout = QHBoxLayout(pill_group)
        pill_layout.setContentsMargins(3, 3, 3, 3)
        pill_layout.setSpacing(2)

        ratios = [
            ("Free", None),
            ("1:1", 1.0),
            ("16:9", 16.0 / 9.0),
            ("9:16", 9.0 / 16.0),
            ("4:3", 4.0 / 3.0),
            ("3:4", 3.0 / 4.0),
        ]

        for text, ratio_val in ratios:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #cbd5e1;
                    border: none;
                    border-radius: 14px;
                    padding: 0 10px;
                }
                QPushButton:checked {
                    background: #ffffff;
                    color: #0f172a;
                    font-weight: bold;
                }
                QPushButton:hover:!checked {
                    background: rgba(255, 255, 255, 0.15);
                }
            """)
            btn.clicked.connect(lambda checked, r=ratio_val, b=btn: self.on_aspect_selected(r, b))
            pill_layout.addWidget(btn)
            self.aspect_buttons[text] = btn

        self.aspect_buttons["Free"].setChecked(True)
        controls_layout.addWidget(pill_group)

        # Width and Height display inputs (Custom pixel dimensions)
        controls_layout.addSpacing(10)
        w_label = QLabel("W")
        w_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        w_label.setStyleSheet("color: #94a3b8; background: transparent;")
        controls_layout.addWidget(w_label)

        self._updating_inputs = False

        self.w_input = QLineEdit()
        self.w_input.setValidator(QIntValidator(10, 10000, self))
        self.w_input.setFixedWidth(64)
        self.w_input.setFixedHeight(28)
        self.w_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.w_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                color: #f1f5f9;
                font-weight: bold;
                padding: 2px 4px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(255, 255, 255, 0.45);
                background: rgba(255, 255, 255, 0.12);
            }
        """)
        self.w_input.returnPressed.connect(self.on_custom_size_entered)
        self.w_input.editingFinished.connect(self.on_custom_size_entered)
        controls_layout.addWidget(self.w_input)

        h_label = QLabel("H")
        h_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        h_label.setStyleSheet("color: #94a3b8; background: transparent;")
        controls_layout.addWidget(h_label)

        self.h_input = QLineEdit()
        self.h_input.setValidator(QIntValidator(10, 10000, self))
        self.h_input.setFixedWidth(64)
        self.h_input.setFixedHeight(28)
        self.h_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.h_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                color: #f1f5f9;
                font-weight: bold;
                padding: 2px 4px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(255, 255, 255, 0.45);
                background: rgba(255, 255, 255, 0.12);
            }
        """)
        self.h_input.returnPressed.connect(self.on_custom_size_entered)
        self.h_input.editingFinished.connect(self.on_custom_size_entered)
        controls_layout.addWidget(self.h_input)

        controls_layout.addStretch()

        # Reset Button
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedHeight(32)
        reset_btn.setFixedWidth(75)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        reset_btn.setStyleSheet(MODAL_BTN_SECONDARY_STYLE)
        reset_btn.clicked.connect(self.canvas.reset_crop)
        controls_layout.addWidget(reset_btn)

        # Apply Button
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedHeight(32)
        apply_btn.setFixedWidth(85)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        apply_btn.setStyleSheet(MODAL_BTN_PRIMARY_STYLE)
        apply_btn.clicked.connect(self.on_apply)
        controls_layout.addWidget(apply_btn)

        container_layout.addLayout(controls_layout)
        main_layout.addWidget(self.container)

    def showEvent(self, event):
        super().showEvent(event)
        self.canvas.update_geometry()
        self.canvas.reset_crop()

    def on_aspect_selected(self, ratio: Optional[float], active_btn: QPushButton):
        for btn in self.aspect_buttons.values():
            btn.setChecked(btn == active_btn)
        self.canvas.set_aspect_ratio(ratio)

    def on_crop_changed(self, w: int, h: int):
        if not self._updating_inputs:
            self._updating_inputs = True
            self.w_input.setText(str(w))
            self.h_input.setText(str(h))
            self._updating_inputs = False

    def on_custom_size_entered(self):
        if self._updating_inputs:
            return
        try:
            w_str = self.w_input.text().strip()
            h_str = self.h_input.text().strip()
            if w_str and h_str:
                w = int(w_str)
                h = int(h_str)
                if w > 0 and h > 0:
                    self._updating_inputs = True
                    self.canvas.set_custom_size(w, h)
                    self._updating_inputs = False
        except ValueError:
            pass

    def on_apply(self):
        result_path = self.canvas.crop_and_save()
        if result_path:
            self.cropped_result = result_path
            self.accept()
        else:
            QMessageBox.warning(self, "Crop Error", "Failed to crop image.")
