"""
PDF Parser — Entry point for every paper analysis.

Every analysis we do depends on clean text extraction.
If this is wrong, everything downstream is wrong.
So we isolate it, test it, make it bulletproof.
"""

import fitz  # PyMuPDF
from dataclasses import dataclass, field
from pathlib import Path


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
    Class-based because later we may need configuration,
    different format handling, and caching.
    """

    def __init__(self):
        self._section_markers = [
            "abstract", "introduction", "methods", "methodology",
            "results", "discussion", "conclusion", "references",
            "related work", "background", "experiments"
        ]

    def parse(self, pdf_path: str) -> ParsedPaper:
        """
        Main entry point.
        Takes a PDF path, returns a structured ParsedPaper object.
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"Paper not found: {pdf_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected PDF file, got: {pdf_path.suffix}")

        doc = fitz.open(str(pdf_path))

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
            metadata=self._extract_metadata(pdf_path),
        )

    def _extract_text(self, doc: fitz.Document) -> str:
        """Extract all text from every page."""
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        return "\n".join(pages)

    def _split_into_sections(self, text: str) -> dict:
        """
        Split paper into named sections by common academic headers.
        Not perfect — PDFs are messy — but good enough for analysis.
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
        Try PDF metadata first, fall back to first meaningful line.
        """
        meta = doc.metadata
        if meta and meta.get("title"):
            return meta["title"].strip()

        for line in full_text.split("\n"):
            line = line.strip()
            if len(line) > 10:
                return line

        return "Unknown Title"

    def _extract_metadata(self, pdf_path: Path) -> dict:
        return {
            "filename": pdf_path.name,
            "file_size_kb": round(pdf_path.stat().st_size / 1024, 2),
        }