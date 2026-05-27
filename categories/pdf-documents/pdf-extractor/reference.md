# reference.md

## Output format

### Text files (`page-N.md`)

Each page's extracted text is written as plain UTF-8 Markdown. If a page contains no extractable text, the file will contain an empty line.

### Table files (`page-N-table-M.csv`)

Each detected table is written as a standard CSV file (RFC 4180). Null/None cells are replaced with empty strings. The first row is typically the header row if the PDF table contains headers.

### OCR output (`ocr/` directory, `--ocr` flag only)

When `--ocr` is used, page images are saved as `ocr/page-N.png` and OCR text is written to `ocr/page-N.md`. If `pytesseract` is not installed, only the PNG images are saved.

## Tesseract installation

### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
```

Additional language packs: `tesseract-ocr-deu` (German), `tesseract-ocr-fra` (French), etc.

### macOS

```bash
brew install tesseract
```

Additional languages: `brew install tesseract-lang`

### Windows

1. Download the installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
2. Add the Tesseract installation directory to your `PATH`.
3. Verify: `tesseract --version`

### Verify installation

```bash
tesseract --version
tesseract --list-langs
```

## Python package notes

- **pdfplumber** (`>=0.10`): Used for native text and table extraction. Parses PDF structure directly — no external dependencies for basic text extraction.
- **pdf2image** (`>=1.16`): Wrapper around `poppler-utils` (`pdftoppm`). Converts PDF pages to PIL images. Requires the `poppler-utils` system package on Linux:

  ```bash
  sudo apt-get install -y poppler-utils
  ```

  On macOS: `brew install poppler`

- **Pillow** (`>=10.0`): Python imaging library, required by pdf2image.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Error (missing file, extraction failure, unhandled exception) |
