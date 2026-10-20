# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

project_dir = Path.cwd()

datas = [
    (str(project_dir / 'icons' / '*.png'), 'icons'),
    (str(project_dir / 'assets' / '*.*'), 'assets'),
]

hiddenimports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'cv2',
    'qrcode',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFilter',
    'PIL.ImageEnhance',
    'PIL.ImageOps',
    'PIL.ImageChops',
    'pymupdf',
    'fitz',
    'docx',
    'pynput',
    'pynput.mouse',
    'pynput.keyboard',
    'pynput.mouse._win32',
    'pynput.keyboard._win32',
    'win32gui',
    'win32con',
    'win32api',
    'win32process',
    'ctypes',
    'ctypes.wintypes',
]

a = Analysis(
    ['main.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'torch', 'transformers', 'mediapipe', 'spacy', 'tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 1. Directory distribution (for fast Inno Setup packaging)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Dragter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_dir / 'assets' / 'app_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Dragter',
)
