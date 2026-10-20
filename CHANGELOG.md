# 📋 Changelog

All notable changes to **Dragter** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-20 — Initial Production Release

*Founded and Architected by **Annamalai KM***

### 🚀 Highlights
- **Universal Shift+Drag Trigger**: Hold <kbd>Shift</kbd> while dragging any file to summon the radial HUD.
- **Hardware-Polled Click Defense**: Integrated direct `GetAsyncKeyState` querying with a 10px Euclidean movement threshold, eliminating false triggers on ordinary clicks and cursor micro-jitter.
- **11 Integrated Dark Glass Tools**: Annotate, Crop, Compress, Edit, Metadata, QR Studio, OCR Text, Watermark, Palette, Add BG, and Redact.
- **Zero-Latency Canvas**: Offscreen double-buffered `QPixmap` rendering engine in the Annotation tool (0.007ms segment blit speed).
- **Offline Multi-Format Converter**: Instant conversions for PNG, JPG, WEBP, PDF, DOCX, TXT, HEIC, AVIF, TIFF, BMP, ICO, and GIF without sending data over the network.
- **Cascading Radial Sub-Tiers**: Sub-option menus fan out seamlessly in curved annular sectors upon hovering parent slices.
- **Real Icon Integration**: Bundled with 11 custom-crafted 512×512 PNG assets, pre-cached with zero runtime disk I/O and zero emoji fallback latency.
- **System Tray Integration**: Background daemon support with pause/resume hooks and fast launcher shortcuts (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>D</kbd>).
- **Official Windows Installer**: Inno Setup 6 packaging with custom shortcuts and autostart configuration.
