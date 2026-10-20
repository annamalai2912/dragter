"""Image and Document Annotation Tool (Pen, Highlighter, Rectangles) — Zero-latency buffered canvas."""

from pathlib import Path
from typing import Optional, List
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QFont, QPainterPath
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFrame, QMessageBox
)
from dragter.ui.theme import MODAL_BTN_PRIMARY_STYLE, MODAL_BTN_SECONDARY_STYLE, get_tool_icon_pixmap


class AnnotateCanvas(QWidget):
    """Zero-latency buffered canvas supporting butter-smooth freehand pen, highlighter, and rectangles."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap: Optional[QPixmap] = None
        self.image_path: Optional[str] = None
        self.display_pixmap: Optional[QPixmap] = None
        self.drawing_layer: Optional[QPixmap] = None
        self.undo_stack: List[QPixmap] = []

        self.current_tool = 'pen'  # 'pen' | 'highlighter' | 'rect'
        self.current_color = QColor(255, 255, 255)  # Crisp white
        self.drawing = False
        self.last_pos: Optional[QPointF] = None
        self.start_pos: Optional[QPointF] = None
        self.current_rect: Optional[QRectF] = None
        self.image_rect = QRectF()

        # Stroke history for full-resolution save export
        self.export_strokes: List[dict] = []
        self._current_stroke_pts: List[QPointF] = []

    def load_image(self, path: str):
        self.image_path = path
        self.pixmap = QPixmap(path)
        self.export_strokes.clear()
        self.undo_stack.clear()
        self.drawing_layer = None
        self.update_geometry()
        self.update()

    def update_geometry(self):
        if not self.pixmap or self.pixmap.isNull() or self.width() <= 20 or self.height() <= 20:
            return
        w, h = self.width() - 40, self.height() - 40
        self.display_pixmap = self.pixmap.scaled(
            int(w), int(h),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        x = (self.width() - self.display_pixmap.width()) / 2
        y = (self.height() - self.display_pixmap.height()) / 2
        new_rect = QRectF(x, y, self.display_pixmap.width(), self.display_pixmap.height())

        if new_rect != self.image_rect or not self.drawing_layer:
            self.image_rect = new_rect
            layer = QPixmap(int(self.image_rect.width()), int(self.image_rect.height()))
            layer.fill(Qt.GlobalColor.transparent)
            if self.drawing_layer and not self.drawing_layer.isNull():
                p = QPainter(layer)
                p.drawPixmap(0, 0, self.drawing_layer.scaled(
                    layer.size(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                p.end()
            self.drawing_layer = layer

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_geometry()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.image_rect.contains(event.position()):
            self.drawing = True
            pos_in_img = event.position() - self.image_rect.topLeft()
            self.last_pos = pos_in_img
            self.start_pos = pos_in_img
            self._current_stroke_pts = [pos_in_img]
            self.current_rect = None

            # Push current layer snapshot to undo stack
            if self.drawing_layer:
                if len(self.undo_stack) >= 30:
                    self.undo_stack.pop(0)
                self.undo_stack.append(self.drawing_layer.copy())

    def mouseMoveEvent(self, event):
        if not self.drawing or not self.drawing_layer:
            return

        pos_in_img = event.position() - self.image_rect.topLeft()
        self._current_stroke_pts.append(pos_in_img)

        if self.current_tool in ('pen', 'highlighter'):
            # Direct incremental line drawing onto offscreen layer: 0ms latency, zero re-traversal!
            painter = QPainter(self.drawing_layer)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            width = 16.0 if self.current_tool == 'highlighter' else 3.5
            pen_color = QColor(self.current_color.red(), self.current_color.green(), self.current_color.blue(), 100) if self.current_tool == 'highlighter' else self.current_color
            cap = Qt.PenCapStyle.RoundCap
            join = Qt.PenJoinStyle.RoundJoin
            pen = QPen(pen_color, width, Qt.PenStyle.SolidLine, cap, join)
            painter.setPen(pen)

            painter.drawLine(self.last_pos, pos_in_img)
            painter.end()

            self.last_pos = pos_in_img
            self.update()

        elif self.current_tool == 'rect':
            self.current_rect = QRectF(self.start_pos, pos_in_img).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.drawing and event.button() == Qt.MouseButton.LeftButton:
            if self.current_tool == 'rect' and self.current_rect and self.drawing_layer:
                painter = QPainter(self.drawing_layer)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                pen = QPen(self.current_color, 3.0, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(self.current_rect, 4.0, 4.0)
                painter.end()
                self.current_rect = None

            # Record stroke for full-res export
            if len(self._current_stroke_pts) >= 2 or self.current_tool == 'rect':
                self.export_strokes.append({
                    'tool': self.current_tool,
                    'color': QColor(self.current_color),
                    'points': list(self._current_stroke_pts)
                })

            self.drawing = False
            self.update()

    def undo(self):
        if self.undo_stack:
            self.drawing_layer = self.undo_stack.pop()
            if self.export_strokes:
                self.export_strokes.pop()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.display_pixmap or self.display_pixmap.isNull():
            return

        ix = int(self.image_rect.x())
        iy = int(self.image_rect.y())
        painter.drawPixmap(ix, iy, self.display_pixmap)

        if self.drawing_layer and not self.drawing_layer.isNull():
            painter.drawPixmap(ix, iy, self.drawing_layer)

        # Temporary interactive preview for rectangle
        if self.drawing and self.current_tool == 'rect' and self.current_rect:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(self.current_color, 3.0, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r = self.current_rect.translated(ix, iy)
            painter.drawRoundedRect(r, 4.0, 4.0)

    def save_annotated(self) -> Optional[str]:
        if not self.image_path or self.image_rect.width() <= 0 or self.image_rect.height() <= 0:
            return None

        # Render full original resolution
        orig = QPixmap(self.image_path)
        if orig.isNull():
            return None

        painter = QPainter(orig)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        scale_x = orig.width() / self.image_rect.width()
        scale_y = orig.height() / self.image_rect.height()
        scale_avg = (scale_x + scale_y) / 2.0

        for stroke in self.export_strokes:
            tool = stroke['tool']
            color = stroke['color']
            pts = stroke['points']
            if not pts:
                continue

            scaled_pts = [
                QPointF(p.x() * scale_x, p.y() * scale_y)
                for p in pts
            ]

            if tool in ('pen', 'highlighter'):
                width = (16.0 if tool == 'highlighter' else 3.5) * scale_avg
                pen_color = QColor(color.red(), color.green(), color.blue(), 100) if tool == 'highlighter' else color
                pen = QPen(pen_color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                path = QPainterPath()
                path.moveTo(scaled_pts[0])
                for pt in scaled_pts[1:]:
                    path.lineTo(pt)
                painter.drawPath(path)

            elif tool == 'rect':
                pen = QPen(color, 3.0 * scale_avg, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                r = QRectF(scaled_pts[0], scaled_pts[-1]).normalized()
                painter.drawRoundedRect(r, 4.0 * scale_x, 4.0 * scale_y)

        painter.end()

        src_path = Path(self.image_path)
        out_path = src_path.parent / f"{src_path.stem} Annotated{src_path.suffix}"
        counter = 1
        while out_path.exists():
            out_path = src_path.parent / f"{src_path.stem} Annotated ({counter}){src_path.suffix}"
            counter += 1

        orig.save(str(out_path))
        return str(out_path)


class AnnotateDialog(QDialog):
    """The Annotate tool modal window."""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.annotated_result: Optional[str] = None

        self.setWindowTitle("Annotate Image")
        self.setMinimumSize(820, 680)
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
        icon_pm = get_tool_icon_pixmap('annotate', 24)
        if icon_pm:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_pm)
            icon_lbl.setStyleSheet("background: transparent;")
            header.addWidget(icon_lbl)
        title = QLabel("Annotate & Markup")
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
            QPushButton:hover { background: rgba(239, 68, 68, 0.85); color: white; }
        """)
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Canvas
        self.canvas = AnnotateCanvas(self)
        self.canvas.setStyleSheet("background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px;")
        layout.addWidget(self.canvas)

        # Controls
        controls = QHBoxLayout()
        controls.setSpacing(10)

        TOOL_BTN_STYLE = """
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 16px;
                color: #cbd5e1;
                font-weight: 500;
                padding: 0 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
                color: white;
            }
            QPushButton:checked {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid rgba(255, 255, 255, 0.4);
                font-weight: bold;
            }
        """

        self.tool_buttons = {}
        # Clean typography without emoji symbols
        for tool_id, label in [('pen', 'Pen'), ('highlighter', 'Highlight'), ('rect', 'Box')]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(TOOL_BTN_STYLE)
            btn.clicked.connect(lambda checked, t=tool_id, b=btn: self._on_tool_clicked(t, b))
            controls.addWidget(btn)
            self.tool_buttons[tool_id] = btn

        # Select pen by default
        self.tool_buttons['pen'].setChecked(True)

        controls.addSpacing(15)
        # Colors (Monochrome white + primary highlighting colors)
        for col_name, qc in [("White", QColor(255, 255, 255)), ("Yellow", QColor(250, 204, 21)), ("Red", QColor(239, 68, 68)), ("Emerald", QColor(34, 197, 94))]:
            c_btn = QPushButton()
            c_btn.setFixedSize(22, 22)
            c_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            c_btn.setStyleSheet(f"background: {qc.name()}; border-radius: 11px; border: 2px solid rgba(255,255,255,0.7);")
            c_btn.clicked.connect(lambda checked, c=qc: self.set_color(c))
            controls.addWidget(c_btn)

        controls.addStretch()

        undo_btn = QPushButton("Undo")
        undo_btn.setFixedSize(80, 32)
        undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        undo_btn.setStyleSheet(MODAL_BTN_SECONDARY_STYLE)
        undo_btn.clicked.connect(self.canvas.undo)
        controls.addWidget(undo_btn)

        apply_btn = QPushButton("Save Markup")
        apply_btn.setFixedSize(120, 32)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet(MODAL_BTN_PRIMARY_STYLE)
        apply_btn.clicked.connect(self.on_apply)
        controls.addWidget(apply_btn)

        layout.addLayout(controls)
        main_layout.addWidget(self.container)

    def _on_tool_clicked(self, tool: str, active_btn: QPushButton):
        """Update tool selection with exclusive active state."""
        for t, b in self.tool_buttons.items():
            b.setChecked(t == tool)
        self.canvas.current_tool = tool

    def set_tool(self, tool: str):
        self.canvas.current_tool = tool

    def set_color(self, qc: QColor):
        self.canvas.current_color = qc

    def on_apply(self):
        res = self.canvas.save_annotated()
        if res:
            self.annotated_result = res
            self.accept()
        else:
            QMessageBox.warning(self, "Annotate Error", "Failed to save annotated image.")
