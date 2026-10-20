"""Background Designer Tool (Solid & Gradient backdrops, padding, rounded corners, soft shadows, and aspect ratios)."""

from pathlib import Path
from typing import Optional, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QColorDialog, QSlider, QSizePolicy
)
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from dragter.ui.theme import MODAL_BTN_PRIMARY_STYLE, MODAL_BTN_SECONDARY_STYLE, get_tool_icon_pixmap


class AddBgDialog(QDialog):
    """
    Background Designer matching Requirement D:
    - Solid colors and gradient-style background choices
    - Background color presets
    - Padding adjustment
    - Rounded corners
    - Shadow adjustment
    - Aspect-ratio choices: Auto, 1:1, 16:9, and 4:5
    - Save with Background
    """

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.bg_result: Optional[str] = None

        # State
        self.bg_mode = 'gradient'   # 'solid' | 'gradient'
        self.current_solid = (24, 24, 27)  # Dark default
        self.current_gradient = ((15, 23, 42), (43, 88, 118))  # Midnight ocean default
        self.padding = 48           # Pixels
        self.corner_radius = 16     # Pixels
        self.shadow_intensity = 45  # Percent 0 - 100
        self.aspect_ratio = 'auto'  # 'auto' | '1:1' | '16:9' | '4:5'

        # Load image
        with Image.open(image_path) as img:
            self.original_img = img.convert('RGBA')

        self.setWindowTitle("Background Designer")
        self.setMinimumSize(920, 750)
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
                    stop:0 rgba(24, 27, 36, 0.98),
                    stop:1 rgba(14, 16, 22, 0.99));
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 20px;
            }
        """)
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(22, 18, 22, 22)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        icon_pm = get_tool_icon_pixmap('add_bg', 26)
        if icon_pm:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_pm)
            icon_lbl.setStyleSheet("background: transparent;")
            header.addWidget(icon_lbl)
        title = QLabel("Background Designer")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #f1f5f9; background: transparent;")
        header.addWidget(title)

        sub_title = QLabel("• Social posts, screenshots & product backdrops")
        sub_title.setFont(QFont("Segoe UI", 10))
        sub_title.setStyleSheet("color: #94a3b8; background: transparent;")
        header.addWidget(sub_title)
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

        # Preview Area
        self.preview_lbl = QLabel()
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_lbl.setStyleSheet("""
            background: rgba(0, 0, 0, 0.40);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
        """)
        layout.addWidget(self.preview_lbl, stretch=1)

        # Control Panel: Background Selection
        bg_bar = QHBoxLayout()
        bg_bar.setSpacing(10)

        type_lbl = QLabel("Type:")
        type_lbl.setStyleSheet("color: #cbd5e1; font-weight: bold; background: transparent;")
        bg_bar.addWidget(type_lbl)

        # Type Pills: Solid / Gradient
        self.solid_btn = QPushButton("Solid")
        self.solid_btn.setCheckable(True)
        self.solid_btn.setFixedHeight(28)
        self.solid_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.solid_btn.setStyleSheet(self._pill_style())
        self.solid_btn.clicked.connect(lambda: self.set_bg_mode('solid'))
        bg_bar.addWidget(self.solid_btn)

        self.grad_btn = QPushButton("Gradient")
        self.grad_btn.setCheckable(True)
        self.grad_btn.setChecked(True)
        self.grad_btn.setFixedHeight(28)
        self.grad_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.grad_btn.setStyleSheet(self._pill_style())
        self.grad_btn.clicked.connect(lambda: self.set_bg_mode('gradient'))
        bg_bar.addWidget(self.grad_btn)

        bg_bar.addSpacing(12)

        # Preset Container (swapped based on mode)
        self.presets_frame = QFrame()
        self.presets_frame.setStyleSheet("background: transparent; border: none;")
        self.presets_layout = QHBoxLayout(self.presets_frame)
        self.presets_layout.setContentsMargins(0, 0, 0, 0)
        self.presets_layout.setSpacing(6)
        bg_bar.addWidget(self.presets_frame)

        self._refresh_presets_ui()

        custom_btn = QPushButton("Custom...")
        custom_btn.setFixedHeight(28)
        custom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        custom_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 14px;
                color: #cbd5e1;
                padding: 0 10px;
                font-weight: 500;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.16); color: white; }
        """)
        custom_btn.clicked.connect(self.choose_custom_color)
        bg_bar.addWidget(custom_btn)

        bg_bar.addStretch()
        layout.addLayout(bg_bar)

        # Adjustments Panel: Aspect Ratio, Padding, Rounded Corners, Shadow
        adj_bar = QHBoxLayout()
        adj_bar.setSpacing(14)

        # Aspect Ratio Pills
        ar_lbl = QLabel("Ratio:")
        ar_lbl.setStyleSheet("color: #cbd5e1; font-weight: bold; background: transparent;")
        adj_bar.addWidget(ar_lbl)

        self.ar_buttons = {}
        for ar_key, ar_label in [('auto', 'Auto'), ('1:1', '1:1'), ('16:9', '16:9'), ('4:5', '4:5')]:
            btn = QPushButton(ar_label)
            btn.setCheckable(True)
            btn.setChecked(ar_key == 'auto')
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._pill_style())
            btn.clicked.connect(lambda checked, k=ar_key: self.set_aspect_ratio(k))
            adj_bar.addWidget(btn)
            self.ar_buttons[ar_key] = btn

        adj_bar.addSpacing(10)

        # Padding Slider
        self.pad_lbl = QLabel("Padding: 48px")
        self.pad_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
        adj_bar.addWidget(self.pad_lbl)
        self.pad_slider = self._create_slider(0, 180, 48, self.on_padding_changed)
        adj_bar.addWidget(self.pad_slider)

        adj_bar.addSpacing(10)

        # Corners Slider
        self.corner_lbl = QLabel("Corners: 16px")
        self.corner_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
        adj_bar.addWidget(self.corner_lbl)
        self.corner_slider = self._create_slider(0, 80, 16, self.on_corners_changed)
        adj_bar.addWidget(self.corner_slider)

        adj_bar.addSpacing(10)

        # Shadow Slider
        self.shadow_lbl = QLabel("Shadow: 45%")
        self.shadow_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
        adj_bar.addWidget(self.shadow_lbl)
        self.shadow_slider = self._create_slider(0, 100, 45, self.on_shadow_changed)
        adj_bar.addWidget(self.shadow_slider)

        layout.addLayout(adj_bar)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet("color: #64748b; font-size: 11px; background: transparent;")
        bottom_bar.addWidget(self.info_lbl)

        bottom_bar.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(85, 34)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(MODAL_BTN_SECONDARY_STYLE)
        cancel_btn.clicked.connect(self.reject)
        bottom_bar.addWidget(cancel_btn)

        save_btn = QPushButton("Save with Background")
        save_btn.setFixedHeight(34)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(MODAL_BTN_PRIMARY_STYLE)
        save_btn.clicked.connect(self.on_apply)
        bottom_bar.addWidget(save_btn)

        layout.addLayout(bottom_bar)
        main_layout.addWidget(self.container)

    def _pill_style(self) -> str:
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 14px;
                color: #cbd5e1;
                padding: 0 10px;
                font-weight: 500;
            }
            QPushButton:checked {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid rgba(255, 255, 255, 0.4);
                font-weight: bold;
            }
            QPushButton:hover:!checked {
                background: rgba(255, 255, 255, 0.15);
                color: white;
            }
        """

    def _create_slider(self, min_v: int, max_v: int, default_v: int, callback) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(default_v)
        slider.setFixedWidth(80)
        slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; background: rgba(255, 255, 255, 0.12); border-radius: 3px; }
            QSlider::sub-page:horizontal { background: rgba(255, 255, 255, 0.5); border-radius: 3px; }
            QSlider::handle:horizontal { background: #ffffff; border: 2px solid rgba(0, 0, 0, 0.2); width: 14px; margin: -4px 0; border-radius: 7px; }
        """)
        slider.valueChanged.connect(callback)
        return slider

    def _refresh_presets_ui(self):
        # Clear existing buttons
        while self.presets_layout.count():
            item = self.presets_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.bg_mode == 'solid':
            presets = [
                ("White", (255, 255, 255)),
                ("Dark", (24, 24, 27)),
                ("Obsidian", (15, 23, 42)),
                ("Slate", (71, 85, 105)),
                ("Platinum", (203, 213, 225)),
                ("Coral", (244, 63, 94)),
                ("Emerald", (16, 185, 129)),
                ("Amber", (245, 158, 11)),
            ]
            for name, rgb in presets:
                btn = QPushButton(name)
                btn.setFixedHeight(28)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgb{rgb};
                        color: {'#18181b' if sum(rgb) > 380 else '#ffffff'};
                        border: 1px solid rgba(255, 255, 255, 0.25);
                        border-radius: 14px;
                        padding: 0 9px;
                        font-size: 11px;
                        font-weight: 500;
                    }}
                """)
                btn.clicked.connect(lambda checked, c=rgb: self.set_solid_color(c))
                self.presets_layout.addWidget(btn)
        else:
            grad_presets = [
                ("Sunset", ((255, 94, 98), (255, 153, 102))),
                ("Titanium", ((45, 55, 72), (26, 32, 44))),
                ("Midnight", ((15, 23, 42), (30, 41, 59))),
                ("Graphite", ((55, 65, 81), (17, 24, 39))),
                ("Roseate", ((138, 35, 135), (233, 64, 87))),
                ("Emerald", ((17, 153, 142), (56, 239, 125))),
            ]
            for name, (c1, c2) in grad_presets:
                btn = QPushButton(name)
                btn.setFixedHeight(28)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 rgb{c1}, stop:1 rgb{c2});
                        color: white;
                        border: 1px solid rgba(255, 255, 255, 0.25);
                        border-radius: 14px;
                        padding: 0 9px;
                        font-size: 11px;
                        font-weight: bold;
                    }}
                """)
                btn.clicked.connect(lambda checked, pair=(c1, c2): self.set_gradient_colors(pair))
                self.presets_layout.addWidget(btn)

    def set_bg_mode(self, mode: str):
        self.bg_mode = mode
        self.solid_btn.setChecked(mode == 'solid')
        self.grad_btn.setChecked(mode == 'gradient')
        self._refresh_presets_ui()
        self.update_preview()

    def set_solid_color(self, rgb: Tuple[int, int, int]):
        self.current_solid = rgb
        self.update_preview()

    def set_gradient_colors(self, pair: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        self.current_gradient = pair
        self.update_preview()

    def set_aspect_ratio(self, ratio_key: str):
        self.aspect_ratio = ratio_key
        for k, btn in self.ar_buttons.items():
            btn.setChecked(k == ratio_key)
        self.update_preview()

    def on_padding_changed(self, val: int):
        self.padding = val
        self.pad_lbl.setText(f"Padding: {val}px")
        self.update_preview()

    def on_corners_changed(self, val: int):
        self.corner_radius = val
        self.corner_lbl.setText(f"Corners: {val}px")
        self.update_preview()

    def on_shadow_changed(self, val: int):
        self.shadow_intensity = val
        self.shadow_lbl.setText(f"Shadow: {val}%")
        self.update_preview()

    def choose_custom_color(self):
        col = QColorDialog.getColor()
        if col.isValid():
            self.set_bg_mode('solid')
            self.set_solid_color((col.red(), col.green(), col.blue()))

    def generate_image(self) -> Image.Image:
        """Render high-resolution composite background, shadow, and rounded foreground."""
        fg = self.original_img.copy()
        fw, fh = fg.size

        # 1. Apply rounded corners to foreground
        if self.corner_radius > 0:
            mask = Image.new('L', (fw, fh), 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle([0, 0, fw, fh], radius=self.corner_radius, fill=255)
            if fg.mode == 'RGBA':
                fg.putalpha(ImageChops.multiply(fg.split()[-1], mask))
            else:
                fg.putalpha(mask)

        # 2. Determine Canvas Size with Aspect Ratio and Padding
        min_canvas_w = fw + self.padding * 2
        min_canvas_h = fh + self.padding * 2

        if self.aspect_ratio == '1:1':
            side = max(min_canvas_w, min_canvas_h)
            cw, ch = side, side
        elif self.aspect_ratio == '16:9':
            target_ratio = 16.0 / 9.0
            if min_canvas_w / min_canvas_h >= target_ratio:
                cw = min_canvas_w
                ch = int(cw / target_ratio)
            else:
                ch = min_canvas_h
                cw = int(ch * target_ratio)
        elif self.aspect_ratio == '4:5':
            target_ratio = 4.0 / 5.0
            if min_canvas_w / min_canvas_h >= target_ratio:
                cw = min_canvas_w
                ch = int(cw / target_ratio)
            else:
                ch = min_canvas_h
                cw = int(ch * target_ratio)
        else:
            # Auto
            cw, ch = min_canvas_w, min_canvas_h

        # 3. Create Background
        if self.bg_mode == 'solid':
            canvas = Image.new('RGB', (cw, ch), self.current_solid)
        else:
            # Diagonal gradient interpolation
            c1, c2 = self.current_gradient
            small = Image.new('RGB', (2, 2))
            small.putpixel((0, 0), c1)
            mid = ((c1[0] + c2[0]) // 2, (c1[1] + c2[1]) // 2, (c1[2] + c2[2]) // 2)
            small.putpixel((1, 0), mid)
            small.putpixel((0, 1), mid)
            small.putpixel((1, 1), c2)
            canvas = small.resize((cw, ch), Image.Resampling.BICUBIC)

        # 4. Foreground placement coordinates (centered)
        fx = (cw - fw) // 2
        fy = (ch - fh) // 2

        # 5. Drop Shadow
        if self.shadow_intensity > 0:
            shadow_canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
            shadow_alpha = int(self.shadow_intensity * 1.8)
            blur_r = int(6 + self.shadow_intensity * 0.28)
            offset_y = int(3 + self.shadow_intensity * 0.16)

            # Build shadow silhouette
            fg_alpha = fg.split()[-1]
            shadow_shape = Image.new('RGBA', (fw, fh), (0, 0, 0, shadow_alpha))
            shadow_shape.putalpha(fg_alpha)

            shadow_canvas.paste(shadow_shape, (fx, fy + offset_y), mask=fg_alpha)
            shadow_blurred = shadow_canvas.filter(ImageFilter.GaussianBlur(blur_r))
            canvas.paste(shadow_blurred, (0, 0), mask=shadow_blurred)

        # 6. Paste Foreground Image
        canvas.paste(fg, (fx, fy), mask=fg.split()[-1] if fg.mode == 'RGBA' else None)
        return canvas

    def update_preview(self):
        img = self.generate_image()
        self.info_lbl.setText(f"Output Dimensions: {img.width} x {img.height} px • Aspect: {self.aspect_ratio.upper()}")

        avail_w = max(100, self.preview_lbl.width() - 24)
        avail_h = max(100, self.preview_lbl.height() - 24)
        preview_copy = img.copy()
        preview_copy.thumbnail((avail_w, avail_h), Image.Resampling.LANCZOS)

        data = preview_copy.tobytes("raw", "RGB")
        qimg = QImage(data, preview_copy.width, preview_copy.height, preview_copy.width * 3, QImage.Format.Format_RGB888)
        self.preview_lbl.setPixmap(QPixmap.fromImage(qimg))

    def on_apply(self):
        """Save with Background beside the original file."""
        try:
            result_img = self.generate_image()
            src_path = Path(self.image_path)
            out_path = src_path.parent / f"{src_path.stem} Background.png"
            counter = 1
            while out_path.exists():
                out_path = src_path.parent / f"{src_path.stem} Background ({counter}).png"
                counter += 1

            result_img.save(str(out_path), 'PNG', optimize=True)
            self.bg_result = str(out_path)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to save background image: {e}")
