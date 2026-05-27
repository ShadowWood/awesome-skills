---
name: pdf-extractor
description: Extract text, tables, and images from PDF files using pdfplumber with optional OCR via pdf2image and tesseract.
---

# pdf-extractor

## What it does

`pdf-extractor` extracts structured content from PDF documents. It supports:

- **Text extraction** — per-page plain text output (Markdown format).
- **Table extraction** — detects and extracts tabular data into CSV files, one per page per table.
- **Image extraction (optional)** — converts PDF pages to images via `pdf2image` and applies OCR using `tesseract`.

The tool is designed for batch and automated workflows: it runs from the command line, accepts a single input PDF, and writes all output to a configurable directory.

## When to use

Use `pdf-extractor` when you need to:

- Programmatically extract text from PDF invoices, reports, or articles.
- Convert tabular PDF data into machine-readable CSV files.
- OCR scanned documents (requires `tesseract` installed separately).
- Build an automated document-processing pipeline.

Do **not** use `pdf-extractor` when:

- You need interactive PDF editing or form filling.
- The PDF contains only vector graphics with no text layer (consider a dedicated OCR tool).
- You require extraction of embedded file attachments or annotations.

## How to use

### Prerequisites

- Python 3.10+
- `pip` dependencies (see `requirements.txt`)

### Installation

```bash
pip install -r requirements.txt
```

For OCR support, you also need `tesseract` on your system:

- **Ubuntu/Debian**: `sudo apt-get install -y tesseract-ocr`
- **macOS (Homebrew)**: `brew install tesseract`
- **Windows**: Download from [GitHub UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

### Basic usage

Extract text and tables from a PDF:

```bash
python scripts/pdf_extractor.py --input document.pdf
```

This creates a directory `document_extracted/` containing:

- `page-1.md`, `page-2.md`, … — extracted text per page
- `page-1-table-1.csv`, … — extracted tables per page

### OCR mode

Convert pages to images and run OCR (requires `tesseract`):

```bash
python scripts/pdf_extractor.py --input document.pdf --ocr
```

### Custom output directory

```bash
python scripts/pdf_extractor.py --input document.pdf --output-dir /tmp/my_extract
```

## Examples

### Extract a quarterly report

```bash
python scripts/pdf_extractor.py \
  --input quarterly-report.pdf \
  --output-dir ./q1-2025-extracted
```

Expected output:

```
q1-2025-extracted/
├── page-1.md
├── page-1-table-1.csv
├── page-2.md
├── page-3.md
└── page-3-table-1.csv
```

### OCR a scanned contract

```bash
python scripts/pdf_extractor.py \
  --input scanned-contract.pdf \
  --ocr
```

When `--ocr` is enabled, the script first attempts to extract text natively with `pdfplumber`. If a page has no extractable text, it falls back to OCR. If `tesseract` is not installed, the script prints a warning and continues without OCR.

### Check exit codes

```bash
python scripts/pdf_extractor.py --input missing.pdf
echo $?   # non-zero: error message written to stderr
```

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| *(none)* | — | No environment variables are required. All configuration is via CLI arguments. |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success — all content extracted |
| 1 | Error — missing input file, read failure, or extraction error |
