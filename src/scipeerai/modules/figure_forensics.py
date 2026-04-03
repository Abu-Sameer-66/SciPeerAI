# Figure Forensics Module
# -----------------------
# Scientific image manipulation is one of the hardest
# fraud types to catch manually. A reviewer comparing
# 40 gel images across a paper would need hours.
# We do it in milliseconds.
#
# Three things we check:
#   1. Duplicate/recycled figures (perceptual hashing)
#   2. Signs of digital editing (Error Level Analysis)
#   3. Unnatural brightness uniformity (contrast flattening)

import io
import math
from dataclasses import dataclass, field
from pathlib import Path

import fitz          # PyMuPDF — extract images from PDF
import imagehash     # perceptual hashing
import numpy as np
from PIL import Image, ImageFilter


# ── data structures ──────────────────────────────────────────────────────────

@dataclass
class ExtractedFigure:
    page_number: int
    figure_index: int
    width: int
    height: int
    image: Image.Image   # actual PIL image object


@dataclass
class ForensicFlag:
    flag_type: str
    severity: str
    description: str
    evidence: str
    figures_involved: list


@dataclass
class FigureForensicsResult:
    figures_found: int
    flags: list
    duplicate_pairs: list       # list of (fig_a, fig_b) index pairs
    risk_score: float
    risk_level: str
    summary: str


# ── main class ────────────────────────────────────────────────────────────────

class FigureForensicsEngine:
    """
    Extracts figures from a PDF and runs forensic analysis on each one.

    Why class-based: we'll want to tune sensitivity thresholds
    per domain — medical imaging needs stricter checks than
    social science bar charts.
    """

    # two images with hash distance <= this are "suspiciously similar"
    DUPLICATE_HASH_THRESHOLD = 8

    # images smaller than this are likely icons/logos — skip them
    MIN_FIGURE_SIZE = (50, 50)

    def __init__(self):
        pass

    # ── public method ─────────────────────────────────────────────────────────

    def analyze(self, pdf_path: str) -> FigureForensicsResult:
        """
        Full forensic pipeline for a PDF file.
        Extract → Hash → Compare → Analyze → Report
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        figures = self._extract_figures(pdf_path)

        if not figures:
            return FigureForensicsResult(
                figures_found=0,
                flags=[],
                duplicate_pairs=[],
                risk_score=0.0,
                risk_level="low",
                summary="No figures found in this document.",
            )

        flags = []
        duplicate_pairs = []

        dup_flags, dup_pairs = self._check_duplicates(figures)
        flags.extend(dup_flags)
        duplicate_pairs.extend(dup_pairs)

        ela_flags = self._check_ela_anomalies(figures)
        flags.extend(ela_flags)

        brightness_flags = self._check_brightness_uniformity(figures)
        flags.extend(brightness_flags)

        risk_score = self._calculate_risk(flags)
        risk_level = self._get_risk_level(risk_score)

        return FigureForensicsResult(
            figures_found=len(figures),
            flags=flags,
            duplicate_pairs=duplicate_pairs,
            risk_score=round(risk_score, 3),
            risk_level=risk_level,
            summary=self._write_summary(len(figures), flags, risk_level),
        )

    # ── extraction ────────────────────────────────────────────────────────────

    def _extract_figures(self, pdf_path: Path) -> list:
        """
        Pull every image out of the PDF, skip tiny ones
        that are probably decorative elements.
        """
        figures = []
        doc = fitz.open(str(pdf_path))

        for page_num, page in enumerate(doc):
            image_list = page.get_images(full=True)

            for img_idx, img_ref in enumerate(image_list):
                xref = img_ref[0]
                try:
                    base_image = doc.extract_image(xref)
                    img_bytes = base_image["image"]
                    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

                    # skip tiny decorative images
                    if img.width < self.MIN_FIGURE_SIZE[0]:
                        continue
                    if img.height < self.MIN_FIGURE_SIZE[1]:
                        continue

                    figures.append(ExtractedFigure(
                        page_number=page_num + 1,
                        figure_index=len(figures),
                        width=img.width,
                        height=img.height,
                        image=img,
                    ))

                except Exception:
                    # corrupted or unreadable image — skip, don't crash
                    continue

        doc.close()
        return figures

    # ── forensic checks ───────────────────────────────────────────────────────

    def _check_duplicates(self, figures: list) -> tuple:
        """
        Perceptual hashing — convert each image to a 64-bit hash
        that represents its visual "fingerprint."

        Unlike MD5 (which changes completely with one pixel edit),
        perceptual hash stays similar if images are visually similar.
        This catches: same image re-saved at different quality,
        cropped versions, brightness-adjusted copies.
        """
        flags = []
        duplicate_pairs = []

        # compute hash for every figure
        hashes = []
        for fig in figures:
            h = imagehash.phash(fig.image)
            hashes.append(h)

        # compare every pair — O(n²) but papers rarely have >50 figures
        for i in range(len(figures)):
            for j in range(i + 1, len(figures)):
                distance = hashes[i] - hashes[j]

                if distance <= self.DUPLICATE_HASH_THRESHOLD:
                    pair = (figures[i].figure_index, figures[j].figure_index)
                    duplicate_pairs.append(pair)

                    severity = "high" if distance <= 4 else "medium"
                    flags.append(ForensicFlag(
                        flag_type="duplicate_figures",
                        severity=severity,
                        description=(
                            f"Figure on page {figures[i].page_number} and "
                            f"figure on page {figures[j].page_number} are "
                            f"visually identical or near-identical "
                            f"(hash distance: {distance}/64)."
                        ),
                        evidence=f"Hash distance: {distance}. Threshold: {self.DUPLICATE_HASH_THRESHOLD}",
                        figures_involved=[
                            figures[i].figure_index,
                            figures[j].figure_index
                        ],
                    ))

        return flags, duplicate_pairs

    def _check_ela_anomalies(self, figures: list) -> list:
        """
        Error Level Analysis (ELA) — when an image is edited and
        re-saved as JPEG, the edited regions compress differently
        from the original. This creates visible "error level" patterns.

        High variance in ELA output = suspicious editing.
        """
        flags = []

        for fig in figures:
            ela_score = self._compute_ela_score(fig.image)

            if ela_score > 35.0:
                flags.append(ForensicFlag(
                    flag_type="ela_anomaly",
                    severity="high" if ela_score > 50 else "medium",
                    description=(
                        f"Figure on page {fig.page_number} shows unusual "
                        f"compression artifacts consistent with digital editing. "
                        f"ELA score: {round(ela_score, 2)}"
                    ),
                    evidence=f"ELA variance score: {round(ela_score, 2)} (threshold: 35.0)",
                    figures_involved=[fig.figure_index],
                ))

        return flags

    def _check_brightness_uniformity(self, figures: list) -> list:
        """
        Legitimately captured images (microscopy, gels, photos)
        have natural brightness variation. An image with extremely
        uniform brightness across all regions suggests artificial
        contrast adjustment or digital fabrication.
        """
        flags = []

        for fig in figures:
            uniformity_score = self._compute_brightness_uniformity(fig.image)

            # very high uniformity = suspiciously "perfect" image
            if uniformity_score > 0.92:
                flags.append(ForensicFlag(
                    flag_type="unnatural_brightness_uniformity",
                    severity="medium",
                    description=(
                        f"Figure on page {fig.page_number} has unusually "
                        f"uniform brightness distribution "
                        f"(uniformity: {round(uniformity_score * 100, 1)}%). "
                        f"Natural images rarely exceed 85% uniformity."
                    ),
                    evidence=f"Uniformity score: {round(uniformity_score, 4)}",
                    figures_involved=[fig.figure_index],
                ))

        return flags

    # ── computation helpers ───────────────────────────────────────────────────

    def _compute_ela_score(self, image: Image.Image) -> float:
        """
        Save image at low quality, compare to original.
        Edited regions show higher difference = higher ELA score.
        """
        # save at low quality to JPEG (amplifies compression artifacts)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=75)
        buffer.seek(0)
        compressed = Image.open(buffer).convert("RGB")

        # pixel-wise difference
        orig_arr = np.array(image, dtype=np.float32)
        comp_arr = np.array(compressed, dtype=np.float32)
        diff = np.abs(orig_arr - comp_arr)

        # standard deviation of the difference — high = suspicious
        return float(np.std(diff))

    def _compute_brightness_uniformity(self, image: Image.Image) -> float:
        """
        Convert to grayscale, measure how "flat" the histogram is.
        A very flat histogram = artificially processed image.
        """
        gray = np.array(image.convert("L"), dtype=np.float32)
        std_dev = np.std(gray)

        # normalize: low std_dev = high uniformity score
        # 128 is half of 255 — a natural image usually has std > 40
        uniformity = 1.0 - min(std_dev / 128.0, 1.0)
        return float(uniformity)

    # ── scoring ───────────────────────────────────────────────────────────────

    def _calculate_risk(self, flags: list) -> float:
        weights = {"high": 0.40, "medium": 0.20, "low": 0.08}
        score = sum(weights.get(f.severity, 0) for f in flags)
        return min(score, 1.0)

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.7:
            return "critical"
        elif score >= 0.4:
            return "high"
        elif score >= 0.2:
            return "medium"
        return "low"

    def _write_summary(self, fig_count: int, flags: list, risk_level: str) -> str:
        if not flags:
            return (
                f"Analyzed {fig_count} figure(s). "
                f"No forensic anomalies detected."
            )

        high = sum(1 for f in flags if f.severity == "high")
        med  = sum(1 for f in flags if f.severity == "medium")
        parts = []
        if high:
            parts.append(f"{high} high-severity issue{'s' if high > 1 else ''}")
        if med:
            parts.append(f"{med} medium-severity concern{'s' if med > 1 else ''}")

        return (
            f"Analyzed {fig_count} figure(s). "
            f"Figure forensics flagged {', '.join(parts)}. "
            f"Risk level: {risk_level.upper()}."
        )