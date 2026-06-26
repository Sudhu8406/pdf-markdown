"""
converter.py  —  PDF → Markdown converter
Handles:
  • Scanned PDFs  → OCR via pytesseract + pdf2image
  • Text PDFs     → direct extraction via pymupdf (fast, no OCR needed)
Auto-detects which method to use per page.
"""

import os
import re
import sys
from pathlib import Path

try:
    import fitz  # pymupdf
except ImportError:
    fitz = None

try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


# ── helpers ──────────────────────────────────────────────────────────────────

def _clean_text(text: str) -> str:
    """Remove junk, normalize whitespace, keep paragraph breaks."""
    # Remove non-printable chars except newlines
    text = re.sub(r'[^\x09\x0A\x0D\x20-\x7E -￿]', '', text)
    # Collapse 3+ blank lines → 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _text_to_md(text: str, page_num: int) -> str:
    """Very light heuristic markdown formatting for a block of raw text."""
    lines = text.splitlines()
    md_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            md_lines.append('')
            continue
        # Heuristic: short ALL-CAPS or title-case lines → heading
        if len(stripped) < 80 and stripped == stripped.upper() and len(stripped) > 3:
            md_lines.append(f'\n## {stripped.title()}\n')
        else:
            md_lines.append(stripped)
    return '\n'.join(md_lines)


# ── extraction strategies ─────────────────────────────────────────────────────

def extract_text_pymupdf(pdf_path: str) -> list[dict]:
    """Extract text from each page using pymupdf. Returns list of {page, text}."""
    if fitz is None:
        raise RuntimeError("pymupdf not installed. Run: pip install pymupdf")
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text")
        pages.append({"page": i, "text": text, "method": "pymupdf"})
    doc.close()
    return pages


def extract_text_ocr(pdf_path: str, dpi: int = 300, lang: str = "eng") -> list[dict]:
    """Convert each PDF page to image then OCR. Returns list of {page, text}."""
    if not OCR_AVAILABLE:
        raise RuntimeError(
            "OCR libraries not installed. Run:\n"
            "  pip install pdf2image pytesseract pillow\n"
            "  Also install Tesseract: https://github.com/tesseract-ocr/tesseract"
        )
    images = convert_from_path(pdf_path, dpi=dpi)
    pages = []
    for i, img in enumerate(images, start=1):
        print(f"  OCR page {i}/{len(images)}...", end="\r", flush=True)
        text = pytesseract.image_to_string(img, lang=lang)
        pages.append({"page": i, "text": text, "method": "ocr"})
    print()  # newline after progress
    return pages


def _is_scanned(page_data: list[dict], threshold: int = 50) -> bool:
    """Return True if the PDF appears to be scanned (little/no selectable text)."""
    total_chars = sum(len(p["text"].strip()) for p in page_data)
    return total_chars < threshold * len(page_data)


# ── main converter ────────────────────────────────────────────────────────────

def pdf_to_markdown(
    pdf_path: str,
    output_path: str | None = None,
    dpi: int = 300,
    lang: str = "eng",
    force_ocr: bool = False,
) -> str:
    """
    Convert a PDF to Markdown.

    Parameters
    ----------
    pdf_path   : path to the input PDF
    output_path: where to save the .md file (default: same dir as PDF)
    dpi        : DPI for OCR rendering (higher = better quality, slower)
    lang       : Tesseract language code (e.g. 'eng', 'fra', 'deu+eng')
    force_ocr  : always use OCR even if text is selectable

    Returns
    -------
    Path to the generated .md file
    """
    pdf_path = str(pdf_path)
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    stem = Path(pdf_path).stem
    if output_path is None:
        output_path = str(Path(pdf_path).parent / f"{stem}.md")

    print(f"Converting: {pdf_path}")

    # Step 1: try fast text extraction first
    pages = []
    if not force_ocr and fitz is not None:
        pages = extract_text_pymupdf(pdf_path)

    # Step 2: if scanned (or forced), fall back to OCR
    if force_ocr or not pages or _is_scanned(pages):
        print("  → Scanned PDF detected, using OCR...")
        pages = extract_text_ocr(pdf_path, dpi=dpi, lang=lang)

    # Step 3: assemble Markdown
    title = stem.replace("_", " ").replace("-", " ").title()
    md_parts = [f"# {title}\n"]

    for p in pages:
        text = _clean_text(p["text"])
        if not text:
            continue
        md_parts.append(f"\n---\n\n**Page {p['page']}**\n\n")
        md_parts.append(_text_to_md(text, p["page"]))
        md_parts.append("\n")

    markdown = "\n".join(md_parts)

    # Step 4: write file
    Path(output_path).write_text(markdown, encoding="utf-8")
    print(f"  ✓ Saved: {output_path}")
    return output_path


# ── CLI usage ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python converter.py <file.pdf> [output.md] [--ocr] [--lang=eng]")
        sys.exit(1)

    pdf = sys.argv[1]
    out = None
    force = False
    lang = "eng"

    for arg in sys.argv[2:]:
        if arg == "--ocr":
            force = True
        elif arg.startswith("--lang="):
            lang = arg.split("=", 1)[1]
        elif not arg.startswith("--"):
            out = arg

    pdf_to_markdown(pdf, output_path=out, force_ocr=force, lang=lang)
