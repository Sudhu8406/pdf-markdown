"""
watcher.py  —  Folder watcher: auto-converts any PDF dropped in a folder to .md
Usage:
    python watcher.py                        # watches ./input_pdfs/  →  ./output_md/
    python watcher.py /path/to/pdfs          # custom input folder
    python watcher.py /path/to/pdfs /out     # custom input + output folder
    python watcher.py --ocr --lang=fra .     # force OCR, French language
"""

import sys
import time
import argparse
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from converter import pdf_to_markdown


# ── event handler ──────────────────────────────────────────────────────────────

class PDFHandler(FileSystemEventHandler):
    def __init__(self, input_dir: Path, output_dir: Path, force_ocr: bool, lang: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.force_ocr = force_ocr
        self.lang = lang
        self._processing: set[str] = set()

    def on_created(self, event):
        self._handle(event)

    def on_moved(self, event):
        """Handle files moved/renamed into the watched folder."""
        self._handle(event, path_attr="dest_path")

    def _handle(self, event, path_attr: str = "src_path"):
        if event.is_directory:
            return
        path = Path(getattr(event, path_attr))
        if path.suffix.lower() != ".pdf":
            return
        if str(path) in self._processing:
            return

        self._processing.add(str(path))
        print(f"\n📄 New PDF detected: {path.name}")

        # Small delay to ensure file is fully written before we read it
        time.sleep(1.5)
        try:
            out = self.output_dir / (path.stem + ".md")
            pdf_to_markdown(
                str(path),
                output_path=str(out),
                force_ocr=self.force_ocr,
                lang=self.lang,
            )
        except Exception as e:
            print(f"  ✗ Error converting {path.name}: {e}")
        finally:
            self._processing.discard(str(path))


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Watch a folder and auto-convert PDFs to Markdown"
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        default="input_pdfs",
        help="Folder to watch for PDFs (default: ./input_pdfs)",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=None,
        help="Folder to save .md files (default: ./output_md)",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Always use OCR even for text-based PDFs",
    )
    parser.add_argument(
        "--lang",
        default="eng",
        help="Tesseract language code (default: eng). Use '+' for multiple, e.g. eng+fra",
    )
    parser.add_argument(
        "--convert-existing",
        action="store_true",
        help="Also convert PDFs already present in the input folder on startup",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else input_dir.parent / "output_md"

    # Create folders if they don't exist
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  PDF → Markdown  Folder Watcher")
    print("=" * 60)
    print(f"  Watching : {input_dir}")
    print(f"  Output   : {output_dir}")
    print(f"  OCR mode : {'forced' if args.ocr else 'auto-detect'}")
    print(f"  Language : {args.lang}")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    # Optionally convert existing PDFs first
    if args.convert_existing:
        existing = list(input_dir.glob("*.pdf"))
        if existing:
            print(f"\nConverting {len(existing)} existing PDF(s)...")
            for pdf in existing:
                out = output_dir / (pdf.stem + ".md")
                if out.exists():
                    print(f"  ⏭  Skipping (already converted): {pdf.name}")
                    continue
                try:
                    pdf_to_markdown(
                        str(pdf),
                        output_path=str(out),
                        force_ocr=args.ocr,
                        lang=args.lang,
                    )
                except Exception as e:
                    print(f"  ✗ Error: {e}")

    # Start watching
    handler = PDFHandler(input_dir, output_dir, args.ocr, args.lang)
    observer = Observer()
    observer.schedule(handler, str(input_dir), recursive=False)
    observer.start()

    print(f"\n👀 Watching for new PDFs in: {input_dir}\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping watcher...")
        observer.stop()
    observer.join()
    print("Done.")


if __name__ == "__main__":
    main()
