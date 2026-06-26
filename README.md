# PDF → Markdown Converter

Auto-converts scanned and text-based PDFs to clean Markdown (`.md`) files.

- **Scanned PDFs** → OCR via Tesseract + pdf2image
- **Text PDFs** → Fast direct extraction via pymupdf
- **Folder watcher** → Drop a PDF in, get a `.md` out automatically

---

## Setup

### 1. Install Tesseract OCR engine

**Windows:**
Download the installer from https://github.com/UB-Mannheim/tesseract/wiki
→ Install and add to PATH (or set path in your script)

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install tesseract-ocr
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Option A — Convert a single PDF

```bash
python converter.py my_document.pdf
# Output: my_document.md  (same folder as PDF)

python converter.py my_document.pdf output/result.md   # custom output path
python converter.py my_document.pdf --ocr              # force OCR
python converter.py my_document.pdf --lang=fra         # French OCR
python converter.py my_document.pdf --lang=eng+fra     # English + French
```

### Option B — Folder watcher (unlimited, automatic)

```bash
python watcher.py
```

This creates:
```
input_pdfs/     ← drop PDFs here
output_md/      ← .md files appear here automatically
```

**Custom folders:**
```bash
python watcher.py /path/to/pdfs /path/to/output
```

**Also convert PDFs already in the folder:**
```bash
python watcher.py --convert-existing
```

**Force OCR + custom language:**
```bash
python watcher.py --ocr --lang=eng+fra
```

---

## File Structure

```
pdf-to-md/
├── converter.py      # Core PDF → Markdown logic
├── watcher.py        # Folder watcher (drop PDF → get .md)
├── requirements.txt  # Python dependencies
└── README.md
```

---

## How it works

1. **Auto-detect** — tries fast text extraction first (pymupdf).
2. **Scanned fallback** — if the page has less than 50 chars, switches to OCR.
3. **Clean output** — removes junk characters, normalizes whitespace, adds basic heading detection.
4. **Page markers** — each page is marked with `**Page N**` in the output.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `tesseract not found` | Install Tesseract and add to PATH |
| `pdf2image` error on Windows | Install Poppler: https://github.com/oschwartz10612/poppler-windows |
| Low OCR quality | Increase DPI: edit `dpi=300` → `dpi=400` in converter.py |
| Wrong language | Use `--lang=<code>` (e.g. `hin` for Hindi, `tam` for Tamil) |

---

## Supported Languages

Tesseract supports 100+ languages. Install language packs:

**Linux:** `sudo apt install tesseract-ocr-hin` (Hindi example)  
**Windows/Mac:** Download from https://github.com/tesseract-ocr/tessdata
