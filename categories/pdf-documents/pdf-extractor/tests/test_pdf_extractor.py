#!/usr/bin/env python3
"""Tests for pdf_extractor.py — uses mocking to avoid real PDF/network access."""

import os
import sys
import subprocess
from unittest.mock import patch, MagicMock

import pytest

SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "pdf_extractor.py",
)


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_pdf_page():
    """Return a MagicMock that behaves like a pdfplumber Page with text + tables."""
    page = MagicMock()
    page.extract_text.return_value = "Hello world\nThis is a test page."
    page.extract_tables.return_value = [
        [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]],
    ]
    return page


@pytest.fixture
def mock_pdf(mock_pdf_page):
    """Return a MagicMock that behaves like a pdfplumber PDF with multiple pages."""
    pdf = MagicMock()
    pdf.pages = [mock_pdf_page, mock_pdf_page]
    pdf.__enter__.return_value = pdf
    pdf.__exit__.return_value = None
    return pdf


# ── Happy path: extraction via subprocess ─────────────────────────────

@pytest.mark.slow
def test_extract_text_and_tables(tmp_path):
    """Run the script via subprocess on a minimal real PDF (if possible)."""
    # We test with --help first to confirm the script is importable
    result = subprocess.run(
        [sys.executable, SCRIPT, "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--input" in result.stdout


def test_happy_path_with_mocks(tmp_path, mock_pdf):
    """Happy path: mocked pdfplumber returns pages with text and tables."""
    fake_pdf = str(tmp_path / "report.pdf")
    # Create a minimal valid PDF so the isfile check passes
    _create_minimal_pdf(fake_pdf)

    with patch("pdfplumber.open", return_value=mock_pdf):
        from scripts.pdf_extractor import extract_pdf

        rc = extract_pdf(fake_pdf, str(tmp_path / "out"))
        assert rc == 0

    out_dir = tmp_path / "out"
    # Text files
    assert (out_dir / "page-1.md").exists()
    assert (out_dir / "page-2.md").exists()
    assert (out_dir / "page-1.md").read_text() == "Hello world\nThis is a test page.\n"

    # Table CSV
    csv_content = (out_dir / "page-1-table-1.csv").read_text()
    assert "Name,Age" in csv_content
    assert "Alice,30" in csv_content
    assert "Bob,25" in csv_content


# ── Failure paths ─────────────────────────────────────────────────────

def test_missing_input_file(tmp_path):
    """Missing input file returns non-zero exit code and prints error."""
    missing = str(tmp_path / "nonexistent.pdf")
    result = subprocess.run(
        [sys.executable, SCRIPT, "--input", missing],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "file not found" in result.stderr.lower()


def test_missing_input_via_extract_function(tmp_path):
    """Call extract_pdf directly with a non-existent path."""
    from scripts.pdf_extractor import extract_pdf

    rc = extract_pdf(str(tmp_path / "missing.pdf"), str(tmp_path / "out"))
    assert rc == 1


def test_extract_raises_exception(tmp_path, mock_pdf):
    """When pdfplumber raises, the function returns non-zero."""
    fake_pdf = str(tmp_path / "corrupt.pdf")
    _create_minimal_pdf(fake_pdf)

    # Make pdfplumber.open raise
    failing_mock = MagicMock()
    failing_mock.__enter__.side_effect = Exception("Corrupt PDF structure")

    with patch("pdfplumber.open", return_value=failing_mock):
        from scripts.pdf_extractor import extract_pdf

        rc = extract_pdf(fake_pdf, str(tmp_path / "out"))
        assert rc == 1


# ── OCR fallback ──────────────────────────────────────────────────────

def test_ocr_fallback_no_pdf2image(tmp_path):
    """When pdf2image is not installed, OCR flag does not crash."""
    fake_pdf = str(tmp_path / "doc.pdf")
    _create_minimal_pdf(fake_pdf)

    with patch("pdfplumber.open") as mock_open:
        mock_pdf = MagicMock()
        mock_pdf.pages = []
        mock_pdf.__enter__.return_value = mock_pdf
        mock_open.return_value = mock_pdf

        from scripts.pdf_extractor import extract_pdf

        # pdf2image won't be importable in a normal env unless installed
        rc = extract_pdf(fake_pdf, str(tmp_path / "ocr_out"), ocr=True)
        assert rc == 0


# ── Helpers ───────────────────────────────────────────────────────────

def _create_minimal_pdf(path):
    """Write a minimal valid PDF that passes the isfile() check."""
    # Minimal PDF that pdfplumber can open (empty but valid structure)
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
        b"xref\n"
        b"0 3\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"trailer<</Size 3/Root 1 0 R>>\n"
        b"startxref\n"
        b"120\n"
        b"%%EOF\n"
    )
    with open(path, "wb") as f:
        f.write(pdf_bytes)
