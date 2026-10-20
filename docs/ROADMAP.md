# 🗺 Dragter: Future Scope & Strategic Roadmap

*Authored by Founder & Lead Architect: **Annamalai KM***  
*Document Version: 1.0.0 | Target Lifecycle: 2026 – 2028*

---

## 🌟 Executive Vision

**Dragter** v1.0.0 established the fastest, zero-latency radial file transformation engine for Windows. The long-term vision is to establish Dragter as the **universal cursor-level operating layer for Windows power users, designers, engineers, and privacy-conscious professionals** — expanding beyond single-image transformations into high-throughput batch processing, offline on-device AI pipelines, rich media encoding, and a vibrant community plugin ecosystem.

---

## 🚀 Strategic Phases & Roadmap

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                               PHASE 1                                  │
  │                  Batch Processing & Multi-File Queues                  │
  │  • Multi-file drag ingestion (10+ files simultaneously)                │
  │  • Multi-threaded asynchronous conversion queues                       │
  │  • PDF Merge & Split radial actions                                    │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                               PHASE 2                                  │
  │                     Media & Audio/Video Expansion                      │
  │  • Lightweight embedded FFmpeg pipeline (MP4 ↔ WebM ↔ GIF)             │
  │  • 1-Click Audio Extractor (Video to MP3 / AAC / WAV)                  │
  │  • Video Trimmer & Clip Optimizer                                      │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                               PHASE 3                                  │
  │                   100% Offline On-Device AI Vision                     │
  │  • Local AI Background Removal (RMBG-1.4 / ONNX Runtime)               │
  │  • 2x & 4x AI Image Upscaling (Real-ESRGAN Compact)                   │
  │  • Multi-Language Offline OCR (PaddleOCR / TrOCR)                      │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                               PHASE 4                                  │
  │                Ecosystem, Plugins & Package Distribution               │
  │  • Community Python Plugin SDK (`@dragter.action`)                     │
  │  • Windows Package Manager (`winget install AnnamalaiKM.Dragter`)      │
  │  • Windows 11 Native Context Menu Integration                          │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 📌 Detailed Enhancement Pillars

### 1. Multi-File Batch Processing & Ingestion
- **Multi-File Drag Support**: Allow dragging 5, 50, or 100 files simultaneously.
  - When multiple files are dragged, the center hub displays `14 FILES SELECTED`.
  - Dropping onto a format (e.g. `WEBP`) processes all files in parallel via a worker thread pool (`concurrent.futures.ThreadPoolExecutor`), saving transformed assets beside originals with live progress bars.
- **Multi-PDF Merging & Assembly**: Dragging multiple PDFs directly offers a **Merge PDFs** radial slice, compiling them sequentially into a single unified document in seconds.
- **PDF Splitting**: One-click extraction of every PDF page into separate numbered documents or images.

---

### 2. Rich Media & Audio/Video Pipeline
- **Video to Optimized GIF**: Instant conversion from MP4/MOV to high-quality compressed animated GIFs with custom FPS (15/30/60) and palette optimization.
- **Video Compression**: Quick preset compression (Discord 25MB limit, WhatsApp 16MB limit, Web-optimized 1080p/720p).
- **Audio Extraction**: Drag a video file and drop onto `AUDIO (MP3)` to extract soundtracks, voiceovers, or podcasts instantly.
- **Audio Format Converter**: Lossless conversion between WAV, FLAC, MP3, OGG, and AAC.

---

### 3. On-Device AI Vision (Zero Cloud / 100% Privacy)
All AI features in Dragter will strictly run on **local hardware** via DirectML / ONNX Runtime, preserving Dragter's core commitment to absolute privacy:
- **Instant AI Background Removal**:
  - One-click transparent PNG generator using lightweight on-device models (e.g., RMBG-1.4 or BiRefNet).
  - Eliminates the need to upload confidential product photography or personal headshots to web services.
- **AI Super-Resolution (Upscaler)**:
  - 2x and 4x sharpening and texture enhancement using compact local neural networks (Real-ESRGAN / ESRGAN-NCNN).
- **Smart Multilingual OCR**:
  - Deep-learning text recognition supporting handwritten text, multi-column documents, receipts, and multilingual character sets (CJK, Cyrillic, Arabic).

---

### 4. Developer & Power-User Tools
- **Base64 Data URI Encoder**: Drag an image or SVG $\rightarrow$ drop on `BASE64` $\rightarrow$ copies `data:image/png;base64,...` directly to clipboard.
- **SVG Vector Optimization**: Integrated SVGO wrapper that strips redundant XML metadata, precision floats, and editor tags, reducing SVG sizes by up to 60%.
- **Hash & Checksum Verifier**: Instant SHA-256 / MD5 calculation and clipboard copying for downloaded binaries and ISO files.
- **JSON / CSV / XLSX Converter**: Drag data files to convert tabular data between CSV, JSON, and Excel formats offline.

---

### 5. Open Plugin Architecture & Community SDK
Create a modular extension system allowing third-party developers to contribute specialized tools and actions:
```python
# Example community plugin: dragter-plugins/tinypng.py
import dragter

@dragter.register_action(
    id="custom_watermark",
    label="Brand Stamp",
    category="image",
    icon="assets/brand.png"
)
def apply_custom_brand(file_path: str, options: dict) -> str:
    # Custom automated processing
    return output_path
```
- **Custom Radial Wheels**: Users can configure custom quick-launch rings (e.g., "Developer Ring", "Photographer Ring", "Office Ring").
- **Script Triggering**: Allow binding custom `.bat`, `.ps1`, or `.py` scripts to custom radial slices.

---

### 6. System Integration & Distribution Channels
- **Windows Package Manager (`winget`)**:
  - Direct installation via command line:
    ```powershell
    winget install AnnamalaiKM.Dragter
    ```
- **Windows 11 Native Context Menu**:
  - Register Dragter in the modern Windows 11 context menu (`IExplorerCommand` sparse package) as a right-click alternative to the drag gesture.
- **Auto-Updater Engine**:
  - Lightweight, non-intrusive update checker that queries GitHub Releases and offers 1-click silent in-place upgrades.
- **Per-Monitor V2 DPI Scaling**:
  - Seamless fractional scaling (125%, 150%, 175%, 200%) across mixed-DPI multi-monitor workstations.

---

## 📈 Milestone Timeline

| Version | Target Horizon | Strategic Focus |
| :--- | :---: | :--- |
| **v1.0.0** | **Current** | Production Release: Multi-ring radial HUD, 11 quick tools, zero-latency canvas, full Inno Setup installer. |
| **v1.1.0** | **Q1 2027** | Batch multi-file drag ingestion, multi-threaded conversion queue, WinGet packaging. |
| **v1.2.0** | **Q2 2027** | Audio/video engine (MP4 to GIF, audio extraction, video compression presets). |
| **v1.5.0** | **Q3 2027** | Local AI Vision (On-device background removal & super-resolution via ONNX/DirectML). |
| **v2.0.0** | **2028** | Public Plugin API, custom wheel creator, and complete workflow automation engine. |
