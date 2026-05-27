# pdf-extractor

Extract text, tables, and images from PDF documents using `pdfplumber` with optional `tesseract` OCR.

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Extract text and tables from a PDF
python scripts/pdf_extractor.py --input path/to/document.pdf

# With OCR (requires tesseract)
python scripts/pdf_extractor.py --input path/to/document.pdf --ocr
```

## Installation

### Python dependencies

```bash
pip install -r requirements.txt
```

### OCR support (optional)

To use the `--ocr` flag you must install `tesseract` separately:

| OS | Command |
|---|---|
| Ubuntu / Debian | `sudo apt-get install -y tesseract-ocr` |
| macOS | `brew install tesseract` |
| Windows | Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) |

Without `tesseract`, the `--ocr` flag prints a warning and falls back to native text extraction.

## Usage

```
usage: pdf_extractor.py [-h] --input INPUT [--output-dir OUTPUT_DIR] [--ocr]

Extract text, tables, and images from a PDF.

options:
  -h, --help            show this help message and exit
  --input INPUT         Path to the input PDF file (required)
  --output-dir OUTPUT_DIR
                        Output directory (default: <input_basename>_extracted)
  --ocr                 Enable OCR via pdf2image + tesseract
```

See `reference.md` for detailed output format information.

## Running tests

```bash
cd categories/pdf-documents/pdf-extractor
pip install -r requirements.txt
pytest -q
```

All tests use `tmp_path` fixtures and do **not** require internet access or a real PDF.

## Validation

From the repository root:

```bash
python scripts/validate-skill.py categories/pdf-documents/pdf-extractor
```

This checks frontmatter structure, script↔test mapping, and directory layout.

## Project structure

```
categories/pdf-documents/pdf-extractor/
├── SKILL.md              # Skill definition (frontmatter + user docs)
├── README.md             # This file — install/usage/test instructions
├── reference.md          # Deep documentation (output formats, OCR setup)
├── requirements.txt      # Python dependencies
├── scripts/
│   └── pdf_extractor.py # CLI entry point
└── tests/
    ├── __init__.py       # Package marker
    └── test_pdf_extractor.py  # Unit tests
```
