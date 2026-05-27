#!/usr/bin/env python3
"""Extract text, tables, and images from PDF files.

Usage:
    python pdf_extractor.py --input <pdf_path> [--output-dir <dir>] [--ocr]
"""

import argparse
import csv
import os
import sys


def extract_pdf(input_path, output_dir, ocr=False):
    """Extract text and tables from a PDF using pdfplumber.

    Args:
        input_path: Path to the input PDF file.
        output_dir: Directory to write extracted content into.
        ocr: If True, attempt OCR via pdf2image + tesseract.

    Returns:
        Exit code (0 = success, 1 = error).
    """
    if not os.path.isfile(input_path):
        print(f"Error: file not found — {input_path}", file=sys.stderr)
        return 1

    try:
        pdfplumber = __import__("pdfplumber")
    except ImportError:
        print(
            "Error: pdfplumber is not installed. Run: pip install pdfplumber",
            file=sys.stderr,
        )
        return 1

    os.makedirs(output_dir, exist_ok=True)

    try:
        with pdfplumber.open(input_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # ── Text extraction ──────────────────────────────────
                text = page.extract_text() or ""
                text_path = os.path.join(output_dir, f"page-{page_num}.md")
                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(text.strip() + "\n")

                # ── Table extraction ─────────────────────────────────
                tables = page.extract_tables() or []
                for table_idx, table in enumerate(tables, start=1):
                    csv_path = os.path.join(
                        output_dir, f"page-{page_num}-table-{table_idx}.csv"
                    )
                    with open(csv_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        for row in table:
                            # Replace None with empty string for CSV
                            writer.writerow([cell or "" for cell in row])

        # ── OCR mode (pdf2image + tesseract) ────────────────────
        if ocr:
            _run_ocr(input_path, output_dir)

        return 0

    except Exception as exc:
        print(f"Error extracting PDF: {exc}", file=sys.stderr)
        return 1


def _run_ocr(input_path, output_dir):
    """Convert PDF pages to images and run OCR.

    Falls back gracefully if pdf2image or tesseract is unavailable.
    """
    try:
        pdf2image = __import__("pdf2image")
        import PIL

        images = pdf2image.convert_from_path(input_path)
        ocr_dir = os.path.join(output_dir, "ocr")
        os.makedirs(ocr_dir, exist_ok=True)

        try:
            import pytesseract
        except ImportError:
            print(
                "Warning: pytesseract not installed. OCR images saved "
                "but no text recognition was performed.",
                file=sys.stderr,
            )
            for page_num, img in enumerate(images, start=1):
                img_path = os.path.join(ocr_dir, f"page-{page_num}.png")
                img.save(img_path)
            return

        for page_num, img in enumerate(images, start=1):
            text = pytesseract.image_to_string(img)
            ocr_text_path = os.path.join(ocr_dir, f"page-{page_num}.md")
            with open(ocr_text_path, "w", encoding="utf-8") as f:
                f.write(text.strip() + "\n")

    except ImportError:
        print(
            "Warning: pdf2image not installed. Skipping OCR.",
            file=sys.stderr,
        )
    except Exception as exc:
        print(f"Warning: OCR processing failed: {exc}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text, tables, and images from a PDF."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input PDF file (required)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: <input_basename>_extracted)",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Enable OCR via pdf2image + tesseract",
    )
    args = parser.parse_args()

    if args.output_dir is None:
        base = os.path.splitext(os.path.basename(args.input))[0]
        args.output_dir = f"{base}_extracted"

    sys.exit(extract_pdf(args.input, args.output_dir, ocr=args.ocr))


if __name__ == "__main__":
    main()
