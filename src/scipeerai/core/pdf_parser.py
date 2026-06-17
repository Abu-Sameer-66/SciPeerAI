"""
PDF Parser — Entry point for every paper analysis.

Every analysis we do depends on clean text extraction.
If this is wrong, everything downstream is wrong.

SciPeerAI v2.3.1 — Built by Sameer Nadeem
Table extraction + DOI harvesting added.
"""

import re
import hashlib
import fitz
from dataclasses import dataclass
from pathlib import Path


MAX_FILE_SIZE_MB  = 50
MAX_PAGES         = 300
ALLOWED_MIME_HEADER = b"%PDF"


@dataclass
class ParsedPaper:
    title:        str
    full_text:    str
    sections:     dict
    page_count:   int
    has_figures:  bool
    figure_count: int
    metadata:     dict
    tables_text:  str = ""
    dois_found:   list = None

    def __post_init__(self):
        if self.dois_found is None:
            self.dois_found = []


class PDFParser:
    """
    Handles PDF ingestion and structured text extraction.
    v2.3.1 upgrades:
      - Table extraction via PyMuPDF blocks
      - Structured number extraction for GRIM/SPRITE/P-Curve
      - DOI harvesting from full document
      - Section-aware extraction
    """

    def __init__(self):
        self._section_markers = [
            "abstract", "introduction", "methods", "methodology",
            "results", "discussion", "conclusion", "references",
            "related work", "background", "experiments",
            "materials and methods", "statistical analysis",
            "data analysis", "findings", "participants",
        ]
        self._doi_pattern = re.compile(
            r'10\.\d{4,9}/[^\s\],;"\'<>\|\{\}\\]+',
            re.IGNORECASE
        )

    def parse(self, pdf_path: str) -> ParsedPaper:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"Paper not found: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected PDF file, got: {pdf_path.suffix}")
        raw_bytes = pdf_path.read_bytes()
        return self.parse_bytes(raw_bytes, filename=pdf_path.name)

    def parse_bytes(self, file_bytes: bytes, filename: str = "upload.pdf") -> ParsedPaper:
        filename = self._sanitize_filename(filename)
        self._validate_bytes(file_bytes, filename)

        doc = fitz.open(stream=file_bytes, filetype="pdf")

        if len(doc) > MAX_PAGES:
            doc.close()
            raise ValueError(
                f"Paper has {len(doc)} pages. Maximum allowed is {MAX_PAGES}."
            )

        full_text    = self._extract_text(doc)
        tables_text  = self._extract_tables(doc)
        combined     = full_text + "\n\n" + tables_text
        sections     = self._split_into_sections(combined)
        figure_count = self._count_figures(doc)
        title        = self._extract_title(doc, full_text)
        page_count   = len(doc)
        dois_found   = self._extract_dois(combined)

        doc.close()

        return ParsedPaper(
            title        = title,
            full_text    = combined,
            sections     = sections,
            page_count   = page_count,
            has_figures  = figure_count > 0,
            figure_count = figure_count,
            dois_found   = dois_found,
            tables_text  = tables_text,
            metadata     = {
                "filename":    filename,
                "file_size_kb": round(len(file_bytes) / 1024, 2),
                "sha256":      hashlib.sha256(file_bytes).hexdigest(),
            },
        )

    def _validate_bytes(self, file_bytes: bytes, filename: str) -> None:
        if len(file_bytes) == 0:
            raise ValueError("Uploaded file is empty.")
        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            size_mb = round(len(file_bytes) / 1024 / 1024, 1)
            raise ValueError(
                f"File too large: {size_mb} MB. Maximum: {MAX_FILE_SIZE_MB} MB."
            )
        if not file_bytes.startswith(ALLOWED_MIME_HEADER):
            raise ValueError("Invalid file. Only real PDF files are accepted.")

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        name = Path(filename).name
        if not name.lower().endswith(".pdf"):
            raise ValueError(f"Expected a PDF filename, got: {filename}")
        return name

    def _extract_text(self, doc: fitz.Document) -> str:
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        return "\n".join(pages)

    def _extract_tables(self, doc: fitz.Document) -> str:
        """
        Extract structured table content from PDF using block-level parsing.
        This is critical for GRIM/SPRITE/P-Curve modules to find
        means, SDs, sample sizes, and p-values that live inside tables.
        """
        table_parts = []

        for page_num, page in enumerate(doc):
            blocks = page.get_text("blocks")

            rows = []
            for block in blocks:
                if block[6] != 0:
                    continue
                text = block[4].strip()
                if not text:
                    continue
                rows.append((block[1], text))

            rows.sort(key=lambda x: x[0])

            for _, text in rows:
                if any(char.isdigit() for char in text):
                    clean = " ".join(text.split())
                    table_parts.append(clean)

        if not table_parts:
            return ""

        return "\nTABLE_DATA:\n" + "\n".join(table_parts)

    def _split_into_sections(self, text: str) -> dict:
        sections  = {}
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
        total = 0
        for page in doc:
            total += len(page.get_images())
        return total

    def _extract_title(self, doc: fitz.Document, full_text: str) -> str:
        meta = doc.metadata
        if meta and meta.get("title"):
            return meta["title"].strip()
        for line in full_text.split("\n"):
            line = line.strip()
            if len(line) > 10:
                return line
        return "Unknown Title"

    def _extract_dois(self, text: str) -> list:
        """
        Extract all DOIs from full document text including tables and headers.
        Uses broad pattern to catch DOIs in any format.
        """
        dois = []
        for m in self._doi_pattern.finditer(text):
            doi = m.group(0).rstrip('.,;)')
            doi_clean = doi.lower()
            if doi_clean not in dois:
                dois.append(doi_clean)
        return dois[:50]