"""Offline conversion engine supporting Images, PDF, DOCX, and Text across all major formats."""

import os
from pathlib import Path
from typing import List, Optional
from PIL import Image
import pymupdf  # PyMuPDF
import docx
from docx.shared import Inches

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


class ConversionError(Exception):
    """Exception raised when a conversion fails."""
    pass


def get_unique_output_path(target_path: Path) -> Path:
    """Generate a non-colliding destination path if a file already exists."""
    if not target_path.exists():
        return target_path
    stem = target_path.stem
    ext = target_path.suffix
    parent = target_path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){ext}"
        if not candidate.exists():
            return candidate
        counter += 1


def convert_image_to_image(src_path: Path, target_ext: str, out_dir: Path) -> List[Path]:
    """Convert between image formats (PNG, JPG, WEBP, HEIC, TIFF, BMP, AVIF, ICO, etc.)."""
    target_ext = target_ext.lower().lstrip('.')
    if target_ext in ('jpg', 'jpeg'):
        target_ext = 'jpeg'
        dest_ext = '.jpg'
    else:
        dest_ext = f".{target_ext}"

    dest_path = get_unique_output_path(out_dir / f"{src_path.stem}{dest_ext}")

    with Image.open(src_path) as img:
        # Handle format specific requirements
        if target_ext in ('jpeg', 'bmp'):
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a crisp white background for transparent images
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                background.save(dest_path, quality=95, optimize=True)
            else:
                img.convert('RGB').save(dest_path, quality=95, optimize=True)

        elif target_ext in ('heic', 'heif'):
            rgb_img = img.convert('RGB')
            try:
                rgb_img.save(dest_path, format='HEIF', quality=90)
            except Exception:
                # If HEIF export fails, save as high quality WebP
                dest_path = get_unique_output_path(out_dir / f"{src_path.stem}.webp")
                rgb_img.save(dest_path, 'WEBP', quality=95)

        elif target_ext == 'ico':
            ico_img = img.convert('RGBA')
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            ico_img.save(dest_path, format='ICO', sizes=sizes)

        elif target_ext == 'avif':
            try:
                img.save(dest_path, 'AVIF', quality=90)
            except Exception:
                # Fallback to WEBP
                dest_path = get_unique_output_path(out_dir / f"{src_path.stem}.webp")
                img.save(dest_path, 'WEBP', quality=90)

        elif target_ext == 'webp':
            img.save(dest_path, 'WEBP', quality=90, lossless=False)

        elif target_ext == 'png':
            img.save(dest_path, 'PNG', optimize=True)

        elif target_ext in ('tiff', 'tif'):
            img.save(dest_path, 'TIFF', compression='tiff_deflate')

        else:
            img.save(dest_path)

    return [dest_path]


def convert_image_to_pdf(src_path: Path, out_dir: Path) -> List[Path]:
    """Convert an image into a clean single-page PDF."""
    dest_path = get_unique_output_path(out_dir / f"{src_path.stem}.pdf")
    with Image.open(src_path) as img:
        rgb_img = img.convert('RGB')
        rgb_img.save(dest_path, 'PDF', resolution=100.0)
    return [dest_path]


def convert_image_to_docx(src_path: Path, out_dir: Path) -> List[Path]:
    """Insert an image into a styled Word DOCX document."""
    dest_path = get_unique_output_path(out_dir / f"{src_path.stem}.docx")
    word_doc = docx.Document()
    word_doc.add_heading(src_path.stem, level=0)
    try:
        word_doc.add_picture(str(src_path), width=Inches(5.5))
    except Exception:
        # If direct image insertion fails (e.g. uncompressed format), convert to temp PNG
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
            temp_png = tf.name
        with Image.open(src_path) as img:
            img.convert('RGB').save(temp_png, 'PNG')
        word_doc.add_picture(temp_png, width=Inches(5.5))
        try:
            os.remove(temp_png)
        except OSError:
            pass

    word_doc.save(str(dest_path))
    return [dest_path]


def convert_image_to_txt(src_path: Path, out_dir: Path) -> List[Path]:
    """Extract metadata, properties, and EXIF tags from image into a readable text document."""
    dest_path = get_unique_output_path(out_dir / f"{src_path.stem}.txt")
    lines = [
        f"File: {src_path.name}",
        f"Source Path: {src_path.resolve()}",
    ]
    try:
        with Image.open(src_path) as img:
            lines.append(f"Dimensions: {img.width} x {img.height} pixels")
            lines.append(f"Format: {img.format}")
            lines.append(f"Color Mode: {img.mode}")
            exif = img.getexif()
            if exif:
                lines.append("\n--- EXIF Metadata ---")
                from PIL import ExifTags
                for k, v in exif.items():
                    tag = ExifTags.TAGS.get(k, str(k))
                    lines.append(f"{tag}: {v}")
    except Exception as e:
        lines.append(f"Error reading image details: {e}")

    dest_path.write_text("\n".join(lines), encoding='utf-8')
    return [dest_path]


def convert_pdf_to_images(src_path: Path, target_fmt: str, out_dir: Path) -> List[Path]:
    """Convert PDF pages to image files (JPG, PNG, WEBP, TIFF, BMP, HEIC, AVIF)."""
    target_fmt = target_fmt.lower().lstrip('.')
    dest_ext = '.jpg' if target_fmt in ('jpg', 'jpeg') else f".{target_fmt}"

    results = []
    doc = pymupdf.open(str(src_path))
    num_pages = len(doc)

    for i in range(num_pages):
        page = doc.load_page(i)
        pix = page.get_pixmap(dpi=150)

        if num_pages == 1:
            candidate = out_dir / f"{src_path.stem}{dest_ext}"
        else:
            candidate = out_dir / f"{src_path.stem}_Page_{i+1:03d}{dest_ext}"

        dest_path = get_unique_output_path(candidate)

        if target_fmt in ('heic', 'heif'):
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(dest_path, format='HEIF', quality=90)
        elif target_fmt == 'avif':
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            try:
                img.save(dest_path, 'AVIF', quality=90)
            except Exception:
                img.save(dest_path.with_suffix('.webp'), 'WEBP', quality=90)
                dest_path = dest_path.with_suffix('.webp')
        else:
            pix.save(str(dest_path))

        results.append(dest_path)

    doc.close()
    return results


def convert_pdf_to_docx(src_path: Path, out_dir: Path) -> List[Path]:
    """Extract text from PDF and compile into a Word DOCX document."""
    dest_path = get_unique_output_path(out_dir / f"{src_path.stem}.docx")
    doc = pymupdf.open(str(src_path))
    word_doc = docx.Document()
    word_doc.add_heading(src_path.stem, level=0)

    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            if i > 0:
                word_doc.add_page_break()
            for line in text.splitlines():
                line = line.strip()
                if line:
                    word_doc.add_paragraph(line)

    doc.close()
    word_doc.save(str(dest_path))
    return [dest_path]


def convert_pdf_to_txt(src_path: Path, out_dir: Path) -> List[Path]:
    """Extract text from PDF and save as plain text."""
    dest_path = get_unique_output_path(out_dir / f"{src_path.stem}.txt")
    doc = pymupdf.open(str(src_path))
    full_text = []
    for page in doc:
        full_text.append(page.get_text())
    doc.close()

    dest_path.write_text("\n\n--- Page Break ---\n\n".join(full_text), encoding='utf-8')
    return [dest_path]


def convert_docx_to_txt(src_path: Path, out_dir: Path) -> List[Path]:
    """Extract text paragraphs from DOCX to TXT."""
    dest_path = get_unique_output_path(out_dir / f"{src_path.stem}.txt")
    doc = docx.Document(str(src_path))
    text = "\n".join(p.text for p in doc.paragraphs if p.text)
    dest_path.write_text(text, encoding='utf-8')
    return [dest_path]


def convert_txt_to_docx(src_path: Path, out_dir: Path) -> List[Path]:
    """Convert text file to DOCX."""
    dest_path = get_unique_output_path(out_dir / f"{src_path.stem}.docx")
    word_doc = docx.Document()
    lines = src_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    for line in lines:
        word_doc.add_paragraph(line)
    word_doc.save(str(dest_path))
    return [dest_path]


def convert_txt_to_pdf(src_path: Path, out_dir: Path) -> List[Path]:
    """Convert plain text to a neat PDF document using PyMuPDF."""
    dest_path = get_unique_output_path(out_dir / f"{src_path.stem}.pdf")
    doc = pymupdf.open()
    text = src_path.read_text(encoding='utf-8', errors='ignore')

    lines = text.splitlines()
    page_size = 50
    chunks = [lines[i:i + page_size] for i in range(0, max(1, len(lines)), page_size)]

    for chunk in chunks:
        page = doc.new_page(width=595, height=842)  # A4
        page_text = "\n".join(chunk)
        page.insert_text((50, 60), page_text, fontsize=11, fontname="helv")

    doc.save(str(dest_path))
    doc.close()
    return [dest_path]


def convert_file(file_path: str, target_format: str, output_dir: Optional[str] = None) -> List[str]:
    """
    Main dispatch function: converts file_path to target_format.
    Saves in the same directory as file_path by default.
    Returns list of paths of newly created files.
    """
    src = Path(file_path).resolve()
    if not src.exists():
        raise ConversionError(f"Source file not found: {file_path}")

    out_dir = Path(output_dir).resolve() if output_dir else src.parent
    target_format = target_format.upper().strip()
    ext = src.suffix.lower()

    IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif', '.ico', '.gif', '.avif', '.heic', '.heif')

    try:
        # 1. Image source conversions
        if ext in IMAGE_EXTS:
            if target_format == 'PDF':
                created = convert_image_to_pdf(src, out_dir)
            elif target_format == 'DOCX':
                created = convert_image_to_docx(src, out_dir)
            elif target_format == 'TXT':
                created = convert_image_to_txt(src, out_dir)
            else:
                created = convert_image_to_image(src, target_format, out_dir)
            return [str(p) for p in created]

        # 2. PDF source conversions
        elif ext == '.pdf':
            if target_format in ('JPG', 'JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF', 'HEIC', 'AVIF'):
                created = convert_pdf_to_images(src, target_format, out_dir)
            elif target_format == 'DOCX':
                created = convert_pdf_to_docx(src, out_dir)
            elif target_format == 'TXT':
                created = convert_pdf_to_txt(src, out_dir)
            elif target_format == 'PDF':
                # Already PDF - duplicate as copy
                dest = get_unique_output_path(out_dir / f"{src.stem}_copy.pdf")
                dest.write_bytes(src.read_bytes())
                return [str(dest)]
            else:
                raise ConversionError(f"Unsupported PDF target format: {target_format}")
            return [str(p) for p in created]

        # 3. DOCX source conversions
        elif ext in ('.docx', '.doc'):
            if target_format == 'TXT':
                created = convert_docx_to_txt(src, out_dir)
            elif target_format == 'PDF':
                txts = convert_docx_to_txt(src, out_dir)
                created = convert_txt_to_pdf(txts[0], out_dir)
                txts[0].unlink(missing_ok=True)
            elif target_format in ('JPG', 'JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF', 'HEIC', 'AVIF'):
                txts = convert_docx_to_txt(src, out_dir)
                pdfs = convert_txt_to_pdf(txts[0], out_dir)
                txts[0].unlink(missing_ok=True)
                created = convert_pdf_to_images(pdfs[0], target_format, out_dir)
                pdfs[0].unlink(missing_ok=True)
            elif target_format == 'DOCX':
                dest = get_unique_output_path(out_dir / f"{src.stem}_copy.docx")
                dest.write_bytes(src.read_bytes())
                return [str(dest)]
            else:
                raise ConversionError(f"Unsupported DOCX target format: {target_format}")
            return [str(p) for p in created]

        # 4. Text source conversions
        elif ext in ('.txt', '.md', '.rtf'):
            if target_format == 'DOCX':
                created = convert_txt_to_docx(src, out_dir)
            elif target_format == 'PDF':
                created = convert_txt_to_pdf(src, out_dir)
            elif target_format in ('JPG', 'JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF', 'HEIC', 'AVIF'):
                pdfs = convert_txt_to_pdf(src, out_dir)
                created = convert_pdf_to_images(pdfs[0], target_format, out_dir)
                pdfs[0].unlink(missing_ok=True)
            elif target_format == 'TXT':
                dest = get_unique_output_path(out_dir / f"{src.stem}_copy.txt")
                dest.write_bytes(src.read_bytes())
                return [str(dest)]
            else:
                raise ConversionError(f"Unsupported TXT target format: {target_format}")
            return [str(p) for p in created]

        else:
            raise ConversionError(f"Unsupported source file format: {ext}")

    except Exception as e:
        raise ConversionError(f"Conversion failed ({src.name} -> {target_format}): {str(e)}") from e
