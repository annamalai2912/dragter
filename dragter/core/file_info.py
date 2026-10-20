import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

IMAGE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif',
    '.ico', '.gif', '.avif', '.heic'
}

DOCUMENT_EXTENSIONS = {
    '.pdf', '.docx', '.doc', '.txt', '.rtf', '.md', '.markdown'
}

# 7 Core Quick Tools
IMAGE_TOOLS = [
    {'id': 'crop',     'label': 'CROP',     'hint': 'Crop with aspect ratios'},
    {'id': 'compress', 'label': 'COMPRESS', 'hint': 'Reduce image file size'},
    {'id': 'metadata', 'label': 'METADATA', 'hint': 'View and strip EXIF data'},
    {'id': 'edit',     'label': 'EDIT',     'hint': 'Adjust brightness, contrast, rotate'},
    {'id': 'annotate', 'label': 'ANNOTATE', 'hint': 'Markup, highlight, draw'},
    {'id': 'add_bg',   'label': 'ADD BG',   'hint': 'Place image on designed background'},
    {'id': 'redact',   'label': 'REDACT',   'hint': 'Blur or censor sensitive areas'},
    {'id': 'qr',       'label': 'QR CODE',  'hint': 'Scan & generate QR codes'},
]

PDF_TOOLS = [
    {'id': 'compress', 'label': 'COMPRESS', 'hint': 'Compress PDF pages'},
    {'id': 'redact',   'label': 'REDACT',   'hint': 'Censor sensitive content'},
    {'id': 'crop',     'label': 'CROP',     'hint': 'Crop PDF page as image'},
    {'id': 'metadata', 'label': 'METADATA', 'hint': 'Inspect and strip document info'},
    {'id': 'annotate', 'label': 'ANNOTATE', 'hint': 'Annotate first page'},
    {'id': 'qr',       'label': 'QR CODE',  'hint': 'Generate QR for document text'},
]

def format_file_size(size_bytes: int) -> str:
    """Format bytes into human-readable string (KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


_CLIP_CACHE: Tuple[float, Optional[str]] = (0.0, None)


def get_clipboard_file(cache_ttl: float = 0.3) -> Optional[str]:
    """Instant non-blocking query for files copied in Windows Explorer or Desktop."""
    global _CLIP_CACHE
    now = time.time()
    if now - _CLIP_CACHE[0] < cache_ttl:
        return _CLIP_CACHE[1]

    res = None
    try:
        import win32clipboard, win32con
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                if files and len(files) > 0:
                    p = Path(files[0])
                    if p.exists():
                        res = str(p.resolve())
        finally:
            win32clipboard.CloseClipboard()
    except Exception:
        pass

    _CLIP_CACHE = (now, res)
    return res


def get_active_explorer_selection(cache_ttl: float = 0.3) -> Optional[str]:
    """Safely return currently selected/copied file without blocking or deadlocking COM."""
    return get_clipboard_file(cache_ttl=cache_ttl)


FORMAT_SELECTOR_ITEMS = [
    {'label': 'PDF',        'format': 'PDF'},
    {'label': 'DOCX',       'format': 'DOCX'},
    {'label': 'TXT',        'format': 'TXT'},
    {'label': 'JPG / JPEG', 'format': 'JPG'},
    {'label': 'PNG',        'format': 'PNG'},
    {'label': 'WEBP',       'format': 'WEBP'},
    {'label': 'HEIC',       'format': 'HEIC'},
    {'label': 'TIFF',       'format': 'TIFF'},
    {'label': 'BMP',        'format': 'BMP'},
    {'label': 'AVIF',       'format': 'AVIF'},
]


def get_hierarchical_wheel(file_path: Optional[str]) -> Dict[str, Any]:
    """
    Build the circular format selector (10 formats) and tools radial menu (7 tools).
    """
    return {
        'format_items': list(FORMAT_SELECTOR_ITEMS),
        'tool_items': list(IMAGE_TOOLS),
        'root_items': list(FORMAT_SELECTOR_ITEMS),
    }


def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get metadata and category info for a single file."""
    path = Path(file_path)
    if not path.exists():
        return {
            'path': file_path,
            'name': path.name,
            'ext': path.suffix.lower(),
            'size': 0,
            'size_str': '0 B',
            'category': 'unknown',
            'hierarchy': get_hierarchical_wheel(None)
        }

    stat = path.stat()
    size = stat.st_size
    size_str = format_file_size(size)
    ext = path.suffix.lower()

    if ext in IMAGE_EXTENSIONS:
        category = 'image'
    elif ext == '.pdf':
        category = 'pdf'
    elif ext in {'.docx', '.doc'}:
        category = 'docx'
    elif ext in {'.txt', '.md', '.rtf'}:
        category = 'txt'
    else:
        category = 'generic'

    return {
        'path': str(path.resolve()),
        'name': path.name,
        'stem': path.stem,
        'dir': str(path.parent),
        'ext': ext,
        'size': size,
        'size_str': size_str,
        'category': category,
        'hierarchy': get_hierarchical_wheel(str(path.resolve()))
    }
