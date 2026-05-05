"""
PDF Parser — Entry point for every paper analysis.

Every analysis we do depends on clean text extraction.
If this is wrong, everything downstream is wrong.
So we isolate it, test it, make it bulletproof.

SciPeerAI v1.5.0 — Built by Sameer Nadeem
"""

import hashlib
import fitz  # PyMuPDF
from dataclasses import dataclass
from pathlib import Path


# ── Security constants ────────────────────────────────────────────
MAX_FILE_SIZE_MB = 50
MAX_PAGES = 300
ALLOWED_MIME_HEADER = b"%PDF"  # Every real PDF starts with %PDF


@dataclass
class ParsedPaper:
    """
    Clean data container for an extracted paper.
    Dataclass = no boilerplate, auto __repr__, clear structure.
    """
    title: str
    full_text: str
    sections: dict
    page_count: int
    has_figures: bool
    figure_count: int
    metadata: dict


class PDFParser:
    """
    Handles PDF ingestion and structured text extraction.
    Supports both file-path parsing and raw-bytes parsing (API uploads).

    Security hardened:
    - Magic byte validation (rejects fake PDFs)
    - File size limit (50 MB)
    - Page count limit (300 pages)
    - Filename sanitization
    - SHA-256 fingerprint per upload
    """

    def __init__(self):
        self._section_markers = [
            "abstract", "introduction", "methods", "methodology",
            "results", "discussion", "conclusion", "references",
            "related work", "background", "experiments"
        ]

    # ── Public: parse from disk path ─────────────────────────────

    def parse(self, pdf_path: str) -> ParsedPaper:
        """
        Parse from a file path on disk.
        Used internally and in tests.
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"Paper not found: {pdf_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected PDF file, got: {pdf_path.suffix}")

        raw_bytes = pdf_path.read_bytes()
        return self.parse_bytes(raw_bytes, filename=pdf_path.name)

    # ── Public: parse from raw bytes (API upload) ─────────────────

    def parse_bytes(self, file_bytes: bytes, filename: str = "upload.pdf") -> ParsedPaper:
        """
        Parse a PDF from raw bytes — used when file arrives through API.
        FastAPI UploadFile → await file.read() → pass here.

        Security checks run before any parsing begins.
        """
        filename = self._sanitize_filename(filename)

        self._validate_bytes(file_bytes, filename)

        doc = fitz.open(stream=file_bytes, filetype="pdf")

        if len(doc) > MAX_PAGES:
            doc.close()
            raise ValueError(
                f"Paper has {len(doc)} pages. "
                f"Maximum allowed is {MAX_PAGES} pages."
            )

        full_text = self._extract_text(doc)
        sections = self._split_into_sections(full_text)
        figure_count = self._count_figures(doc)
        title = self._extract_title(doc, full_text)
        page_count = len(doc)

        doc.close()

        return ParsedPaper(
            title=title,
            full_text=full_text,
            sections=sections,
            page_count=page_count,
            has_figures=figure_count > 0,
            figure_count=figure_count,
            metadata={
                "filename": filename,
                "file_size_kb": round(len(file_bytes) / 1024, 2),
                "sha256": hashlib.sha256(file_bytes).hexdigest(),
            },
        )

    # ── Security helpers ──────────────────────────────────────────

    def _validate_bytes(self, file_bytes: bytes, filename: str) -> None:
        """
        Three security checks before we touch the file:
        1. Not empty
        2. Under size limit
        3. Real PDF magic bytes — not a renamed .exe or .zip
        """
        if len(file_bytes) == 0:
            raise ValueError("Uploaded file is empty.")

        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            size_mb = round(len(file_bytes) / 1024 / 1024, 1)
            raise ValueError(
                f"File too large: {size_mb} MB. "
                f"Maximum allowed: {MAX_FILE_SIZE_MB} MB."
            )

        if not file_bytes.startswith(ALLOWED_MIME_HEADER):
            raise ValueError(
                "Invalid file. Only real PDF files are accepted. "
                "Renamed or corrupted files are rejected."
            )

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Strip path traversal characters and enforce .pdf extension.
        Prevents directory traversal attacks like ../../etc/passwd.pdf
        """
        name = Path(filename).name  # strips any directory component
        if not name.lower().endswith(".pdf"):
            raise ValueError(f"Expected a PDF filename, got: {filename}")
        return name

    # ── Private: extraction logic ─────────────────────────────────

    def _extract_text(self, doc: fitz.Document) -> str:
        """Extract all text from every page."""
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        return "\n".join(pages)

    def _split_into_sections(self, text: str) -> dict:
        """
        Split paper into named sections by common academic headers.
        Not perfect — PDFs are messy — but good enough for downstream analysis.
        """
        sections = {}
        text_lower = text.lower()

        for i, marker in enumerate(self._section_markers):
            start_idx = text_lower.find(marker)
            if start_idx == -1:
                continue

            end_idx = len(text)
            for next_marker in self._section_markers[i + 1:]:
                next_idx = text_lower.find(next_marker, start_idx + 1)
                if next_idx != -1:
                    end_idx = next_idx
                    break

            sections[marker] = text[start_idx:end_idx].strip()

        return sections

    def _count_figures(self, doc: fitz.Document) -> int:
        """Count image/figure objects across all pages."""
        total = 0
        for page in doc:
            total += len(page.get_images())
        return total

    def _extract_title(self, doc: fitz.Document, full_text: str) -> str:
        """
        Try PDF metadata first, fall back to first meaningful line of text.
        """
        meta = doc.metadata
        if meta and meta.get("title"):
            return meta["title"].strip()

        for line in full_text.split("\n"):
            line = line.strip()
            if len(line) > 10:
                return line

        return "Unknown Title"