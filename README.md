<div align="center">

# ⚡ Dragter

**Ultra-Fast, Offline Radial Utility HUD & File Transformation Suite for Windows**

*Created by **Annamalai KM***

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg?style=for-the-badge)](https://github.com/annamalai2912/dragter/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D6.svg?style=for-the-badge&logo=windows)](https://microsoft.com/windows)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB.svg?style=for-the-badge&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Frame Rate](https://img.shields.io/badge/rendering-120%20FPS%20Butter-success.svg?style=for-the-badge)]()

<br/>

> **Dragter** turns any file drag on Windows into an instant, zero-latency radial menu.  
> Simply drag any file with your mouse and hold **Shift** — an executive dark titanium HUD blooms at your cursor, giving you 1-click format conversions, image manipulation, OCR, QR generation, metadata stripping, annotation, and redaction in microseconds.

</div>

---

## 👨‍💻 Creator & Leadership

- **Creator & Lead Architect:** **Annamalai KM** ([@annamalai2912](https://github.com/annamalai2912))
- **Email:** annamalai2912002@gmail.com
- **Project Repository:** [github.com/annamalai2912/dragter](https://github.com/annamalai2912/dragter)

---

## 🎯 How It Works

```
   [ Select Any File in Explorer or Desktop ]
                      │
                      ▼
         [ Drag with Left Mouse Button ]
                      │
                      ▼
             [ Hold Shift Key ]
                      │
                      ▼
 ┌──────────────────────────────────────────────┐
 │     ⚡ Executive Dark Titanium Radial HUD     │
 │                                              │
 │  • Outer Ring: Multi-Format Conversions      │
 │  • Cascading Sub-Tiers: Quick Tools & Formats│
 │  • Inner Ring: 6 Orbit Shortcut Buttons      │
 │  • Center Hub: File Type & Page Navigation   │
 └──────────────────────┬───────────────────────┘
                        │
                        ▼
       [ Drop on Target Slice to Execute ]
```

1. **Grab ANY File**: Left-click and drag any file from Windows File Explorer, Desktop, or open dialogs.
2. **Hold <kbd>Shift</kbd>**: The instant you move your cursor past 10 pixels, Dragter's dark glass radial dial blooms centered right at your mouse.
3. **Drop to Execute**:
   - Drop onto a **Format Slice** (`PDF`, `WEBP`, `PNG`, `JPG`, `DOCX`, etc.) to convert offline instantly.
   - Drop onto a **Tool Slice** or sub-option to launch a modal tool.
4. **Instant Summoning Shortcut**: Press <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>D</kbd> or <kbd>Alt</kbd> + <kbd>D</kbd> anywhere to trigger the HUD at your current cursor position.

---

## ✨ Core Features

### 1. 🍩 Multi-Format Offline Conversion Engine
- **Supported Formats**: `PNG`, `JPG / JPEG`, `WEBP`, `PDF`, `DOCX`, `TXT`, `HEIC`, `AVIF`, `TIFF`, `BMP`, `ICO`, `GIF`.
- **100% Offline & Private**: Zero data sent to the cloud. All conversions run locally using Pillow, PyMuPDF, and python-docx.
- **Smart Quality Control**: Instant sub-tier presets for WebP (lossless, 90%, 75%) and JPG (95% HQ, 80% Balanced, 65% Web, Monochrome B&W).
- **PDF Multi-Tooling**: Extract all pages to individual PNG images or extract text to TXT in one click.

### 2. 🛠 11 Integrated Quick Action Tools
Dragter comes bundled with 11 custom-crafted dark titanium tools:

| Tool | Icon Asset | Capabilities |
| :--- | :---: | :--- |
| **Annotate & Markup** | `notes.png` | Zero-latency buffered canvas (0.007ms per segment), freehand pen, highlighter, rounded boxes, 30-level undo, and vector-scaled original resolution export. |
| **Crop Studio** | `crop.png` | Draggable rule-of-thirds grid, custom pixel dimensions (W/H), presets (`Free`, `1:1`, `16:9`, `9:16`, `4:3`, `3:4`). |
| **Smart Compression** | `data-compression.png` | Lossless and lossy compression slider for images and PDFs with live size estimation and savings calculator. |
| **Edit & Adjust** | `color-wheel.png` | Brightness, contrast, 90° rotation, horizontal/vertical flips, inversion, and monochrome conversion. |
| **Metadata Inspector** | `metadata.png` | Deep EXIF tag viewer, GPS location auditor, and 1-click privacy sanitizer (strips all tracking/device tags). |
| **QR Code Studio** | `qr-code.png` | Ultra-fast computer-vision QR decoding from images, plus custom high-resolution QR generator with live preview and clipboard copy. |
| **Extract Text (OCR)** | `ocr.png` | Fast local text extraction from images and PDF documents with word/character counts and 1-click clipboard copy. |
| **Watermark & Stamp** | `watermark.png` | Custom text or logo branding stamp with live opacity, scaling, and positioning. |
| **Palette Extractor** | `color-wheel.png` | K-means color clustering extracting dominant palette swatches with 1-click HEX/RGB clipboard copy. |
| **Background Designer** | `generative-image.png` | Backdrops for screenshots & social media posts. Solid presets, multi-color gradients, adjustable padding, corner rounding, and soft shadows. |
| **Sensitive Redaction** | `text-recognising.png` | Interactive canvas to blackout or Gaussian-blur confidential information on documents and screenshots. |

---

## ⚡ Performance Engineering

Dragter was engineered from the ground up for instantaneous responsiveness:

- **Zero-Latency Drawing Canvas**: Uses an offscreen double-buffered `QPixmap` layer. Mouse move events record incremental line segments in **0.007 milliseconds**, bypassing the $O(N \times M)$ overhead of recalculating historic paths.
- **Authoritative Click vs. Drag Engine**: Low-level Windows hook queries `GetAsyncKeyState` directly, completely preventing stuck keys and false triggers on stationary clicks or micro-jitter (10px Euclidean threshold).
- **Zero Emoji Latency**: Completely eliminates Windows DirectWrite emoji fallback lookup pauses by rendering clean typography and hardware-accelerated icon blits.
- **Magnetic Ferrofluid Center Hub**: Smooth spring-damper physics pull the center hub toward the active hover direction, displaying file metadata, size, and real-time status.

---

## ⌨ Shortcuts & Navigation

| Action | Input / Gesture |
| :--- | :--- |
| **Summon Radial Dial** | Drag file + hold <kbd>Shift</kbd> (moved > 10px) |
| **Global Hotkey** | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>D</kbd> or <kbd>Alt</kbd> + <kbd>D</kbd> |
| **Flip Pages (Formats ↔ Tools)** | Mouse Wheel Scroll / Click Center Hub / Press <kbd>Tab</kbd> / <kbd>→</kbd> / <kbd>←</kbd> |
| **Open Sub-Tier Menu** | Hover over any slice with outward arrow indicator (`TOOLS`, `JPG`, `PDF`, etc.) |
| **Close HUD** | Press <kbd>Esc</kbd> / Click outside / Click `✕` Satellite Button |
| **Copy File Path** | Click `COPY` Satellite Button |
| **Reveal in Explorer** | Click `DIR` Satellite Button |

---

## 📦 Installation & Setup

### Option 1: Official Windows Installer (Recommended)
Download and run the official setup wizard:
1. Download **`Dragter-Setup-v1.0.0.exe`** from [Releases](https://github.com/annamalai2912/dragter/releases).
2. Follow the setup wizard to install Dragter with optional desktop shortcut and autostart on Windows boot.

### Option 2: Portable Executable
1. Download **`Dragter.exe`**.
2. Run anywhere without administrator privileges.

### Option 3: Run from Source

#### Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.10, 3.11, 3.12, or 3.13

#### Clone & Install
```bash
# Clone the repository
git clone https://github.com/annamalai2912/dragter.git
cd dragter

# Install required dependencies
pip install -r requirements.txt

# Launch Dragter
python main.py
```

---

## 🏗 Architecture & Project Structure

```
dragter/
├── assets/                  # High-resolution application icons and brand graphics
│   └── app_icon.ico         # Multi-size Windows application icon (16x16 - 256x256)
├── dragter/                 # Main Python package
│   ├── app.py               # Application orchestrator, single-instance mutex, hotkeys
│   ├── core/                # System & engine layer
│   │   ├── converter.py     # Offline conversion engine (Pillow, PyMuPDF, docx)
│   │   ├── file_info.py     # File metadata inspector and caching
│   │   └── hook.py          # Low-level Windows mouse & keyboard hook (Shift+Drag)
│   └── ui/                  # User interface & visual presentation layer
│       ├── donut_geometry.py# Annular math, arc sectors, liquid spring geometry
│       ├── drop_pill.py     # Compact fallback drag target pill
│       ├── radial_window.py # Multi-ring radial HUD with 60-120 FPS physics
│       ├── theme.py         # Dark titanium theme, icon loader, pre-cached pixmaps
│       ├── tools/           # 11 Modal tool dialogs
│       │   ├── add_bg_dialog.py
│       │   ├── annotate_dialog.py
│       │   ├── compress_dialog.py
│       │   ├── crop_dialog.py
│       │   ├── edit_dialog.py
│       │   ├── metadata_dialog.py
│       │   ├── ocr_dialog.py
│       │   ├── palette_dialog.py
│       │   ├── qr_dialog.py
│       │   ├── redact_dialog.py
│       │   └── watermark_dialog.py
│       └── tray.py          # Windows notification area system tray integration
├── icons/                   # 11 transparent 512x512 PNG tool icon assets
├── installer/               # Inno Setup 6 packaging scripts
│   └── Dragter_Setup.iss
├── main.py                  # Application entry point & CLI diagnostics
├── requirements.txt         # Pinned production dependencies
├── LICENSE                  # MIT License (Annamalai KM)
└── README.md                # Comprehensive documentation
```

---

## 🔨 Building the Installer from Source

To compile the standalone Windows executable and the setup wizard:

```powershell
# 1. Build the standalone executable with PyInstaller
python -m PyInstaller dragter.spec --noconfirm

# 2. Compile the Windows Setup installer with Inno Setup 6
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\Dragter_Setup.iss
```

The compiled installer will be generated in `dist/Dragter-Setup-v1.0.0.exe`.

---

## 🔮 Future Scope & Roadmap

Dragter is continuously evolving with high-impact features planned across upcoming releases:

- **Phase 1: Multi-File Batch Queues**: Drag and batch-convert dozens of files simultaneously with parallel thread workers; PDF merge and split suites.
- **Phase 2: Video & Audio Engine**: Instant video-to-GIF converter, lossless video compression presets (Discord/WhatsApp), and 1-click audio extraction.
- **Phase 3: 100% Offline AI Vision**: Local neural networks (ONNX/DirectML) for 1-click on-device AI background removal, 4x super-resolution upscaling, and handwriting OCR.
- **Phase 4: Ecosystem & Plugins**: Python plugin SDK (`@dragter.action`), custom radial wheel configurator, WinGet package distribution (`winget install AnnamalaiKM.Dragter`), and Windows 11 context menu integration.

👉 **Read the full engineering roadmap in [docs/ROADMAP.md](docs/ROADMAP.md).**

---

## 📄 License

This project is open-source software licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for complete details.

**Copyright (c) 2026 Annamalai KM.** All rights reserved.
