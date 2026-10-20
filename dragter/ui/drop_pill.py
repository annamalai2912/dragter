"""Floating Desktop Drop Zone Widget (A discreet desktop pill that accepts drops anytime)."""

from pathlib import Path
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PyQt6.QtWidgets import QWidget, QApplication


class DropPillWidget(QWidget):
    """A floating frosted glass pill on the desktop to drop files onto."""
    fileDropped = pyqtSignal(str, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(170, 48)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

        self.is_drag_over = False
        self._dragging_window = False
        self._drag_start_pos = QPoint()

        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            self.move(geom.right() - 200, geom.bottom() - 90)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.is_drag_over = True
            self.update()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.is_drag_over = False
        self.update()

    def dropEvent(self, event):
        self.is_drag_over = False
        self.update()
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if path and Path(path).exists():
                    event.acceptProposedAction()
                    center = self.mapToGlobal(self.rect().center())
                    self.fileDropped.emit(path, center.x(), center.y())
                    return
        event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging_window = True
            self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._dragging_window:
            self.move(event.globalPosition().toPoint() - self._drag_start_pos)

    def mouseReleaseEvent(self, event):
        self._dragging_window = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(2, 2, -2, -2)
        r = rect.height() / 2

        if self.is_drag_over:
            grad = QLinearGradient(0, 0, self.width(), self.height())
            grad.setColorAt(0, QColor(255, 255, 255, 55))
            grad.setColorAt(1, QColor(255, 255, 255, 25))
            painter.setBrush(QBrush(grad))
            painter.setPen(QPen(QColor(255, 255, 255, 180), 1.6))
            painter.setPen(QColor(255, 255, 255))
        else:
            grad = QLinearGradient(0, 0, 0, self.height())
            grad.setColorAt(0, QColor(28, 32, 42, 240))
            grad.setColorAt(1, QColor(18, 20, 26, 250))
            painter.setBrush(QBrush(grad))
            painter.setPen(QPen(QColor(255, 255, 255, 30), 1.2))
            painter.setPen(QColor(226, 232, 240))

        painter.drawRoundedRect(rect, r, r)

        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        text = "Drop to Convert" if self.is_drag_over else "Dragter (Shift+Drag)"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
