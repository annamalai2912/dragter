import sys
import argparse
from pathlib import Path

import traceback

# Route pythonw.exe stdout/stderr to dragter.log for diagnostics
log_file = Path(__file__).parent / "dragter.log"
if sys.stdout is None:
    sys.stdout = open(log_file, "a", encoding="utf-8", buffering=1)
if sys.stderr is None:
    sys.stderr = open(log_file, "a", encoding="utf-8", buffering=1)

def handle_exception(exc_type, exc_value, exc_traceback):
    with open(log_file, "a", encoding="utf-8") as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
sys.excepthook = handle_exception

import ctypes

_single_instance_mutex = None

def ensure_single_instance(mutex_name: str = "Local\\DragterSingleInstance_UniqueAppLock"):
    """Prevent multiple conflicting instances of Dragter from running concurrently."""
    global _single_instance_mutex
    _single_instance_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183
    if last_error == ERROR_ALREADY_EXISTS:
        print("[Dragter] Another instance is already running. Exiting.")
        sys.exit(0)
    return _single_instance_mutex

from PyQt6.QtWidgets import QApplication

from dragter.app import DragterApplication
from dragter.ui.radial_window import RadialWindow
from dragter.ui.tools import (
    CropDialog, CompressDialog, MetadataDialog,
    RedactDialog, EditDialog, AddBgDialog, AnnotateDialog, QrDialog
)


def main():
    parser = argparse.ArgumentParser(description="Dragter: Shift+Drag Instant File Converter & Quick Actions")
    parser.add_argument("--file", "-f", help="Directly open Radial HUD with specified file")
    parser.add_argument("--crop", help="Directly open Crop Dialog for an image")
    parser.add_argument("--compress", help="Directly open Compress Dialog for a file")
    parser.add_argument("--add-bg", help="Directly open Background Designer Dialog for an image")
    parser.add_argument("--annotate", help="Directly open Annotate Dialog for an image")
    parser.add_argument("--redact", help="Directly open Redact Dialog for an image")
    parser.add_argument("--edit", help="Directly open Edit Dialog for an image")
    parser.add_argument("--metadata", help="Directly open Metadata Dialog for a file")
    parser.add_argument("--qr", help="Directly open QR Code Studio")
    parser.add_argument("--test", action="store_true", help="Run self-diagnostic test")
    args = parser.parse_args()

    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

    if args.test:
        print("Running Dragter self-test...")
        from dragter.core.converter import convert_file
        from dragter.core.file_info import get_file_info
        assert callable(convert_file) and callable(get_file_info)
        print("[OK] Modules and dependencies loaded successfully!")
        return 0

    app = QApplication.instance() or QApplication(sys.argv)

    if args.crop:
        dlg = CropDialog(args.crop)
        dlg.exec()
        return 0

    if args.compress:
        dlg = CompressDialog(args.compress)
        dlg.exec()
        return 0

    if args.add_bg:
        dlg = AddBgDialog(args.add_bg)
        dlg.exec()
        return 0

    if args.annotate:
        dlg = AnnotateDialog(args.annotate)
        dlg.exec()
        return 0

    if args.redact:
        dlg = RedactDialog(args.redact)
        dlg.exec()
        return 0

    if args.edit:
        dlg = EditDialog(args.edit)
        dlg.exec()
        return 0

    if args.metadata:
        dlg = MetadataDialog(args.metadata)
        dlg.exec()
        return 0

    if args.qr:
        dlg = QrDialog(args.qr)
        dlg.exec()
        return 0

    if args.file:
        win = RadialWindow()
        win.show_at(500, 400, file_path=args.file)
        return app.exec()

    # Normal mode: Run background daemon with hook, tray, and single-instance lock
    ensure_single_instance()
    dragter_app = DragterApplication(sys.argv)
    return dragter_app.start()


if __name__ == "__main__":
    sys.exit(main())
