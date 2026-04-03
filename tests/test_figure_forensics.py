# tests/test_figure_forensics.py
#
# Testing figure forensics without real PDFs.
# We test the core algorithms directly — hash comparison,
# ELA computation, brightness analysis.

import io
import pytest
import numpy as np
from PIL import Image

from src.scipeerai.modules.figure_forensics import (
    FigureForensicsEngine,
    ExtractedFigure,
    FigureForensicsResult,
)


@pytest.fixture
def engine():
    return FigureForensicsEngine()


def make_figure(color=(128, 64, 32), size=(100, 100), page=1, idx=0):
    """Helper — create a fake ExtractedFigure with a solid color image."""
    img = Image.new("RGB", size, color=color)
    return ExtractedFigure(
        page_number=page,
        figure_index=idx,
        width=size[0],
        height=size[1],
        image=img,
    )


# ── duplicate detection ───────────────────────────────────────────────────────

def test_identical_images_flagged_as_duplicates(engine):
    # same image twice — must be caught
    fig_a = make_figure(color=(200, 100, 50), idx=0, page=1)
    fig_b = make_figure(color=(200, 100, 50), idx=1, page=3)

    flags, pairs = engine._check_duplicates([fig_a, fig_b])

    assert len(pairs) == 1
    assert any(f.flag_type == "duplicate_figures" for f in flags)


def test_different_images_not_flagged(engine):
    # solid colors fool phash — real figures have texture and detail
    # so we test with noise-based images, which represent actual paper figures
    import numpy as np

    rng = np.random.default_rng(seed=42)
    arr_a = rng.integers(0, 255, (100, 100, 3), dtype=np.uint8)
    arr_b = rng.integers(0, 128, (100, 100, 3), dtype=np.uint8)
    arr_b[:, :, 0] = 255 - arr_b[:, :, 0]  # invert red channel — maximally different

    img_a = Image.fromarray(arr_a, "RGB")
    img_b = Image.fromarray(arr_b, "RGB")

    fig_a = ExtractedFigure(1, 0, 100, 100, img_a)
    fig_b = ExtractedFigure(2, 1, 100, 100, img_b)

    flags, pairs = engine._check_duplicates([fig_a, fig_b])
    assert len(pairs) == 0


# ── brightness uniformity ──────────────────────────────────────────────────────

def test_flat_image_high_uniformity(engine):
    # solid color = perfectly uniform = suspicious
    fig = make_figure(color=(128, 128, 128))
    score = engine._compute_brightness_uniformity(fig.image)
    assert score > 0.90


def test_noisy_image_low_uniformity(engine):
    # random noise = natural-looking variation
    noise_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    noisy_img = Image.fromarray(noise_array, "RGB")
    fig = ExtractedFigure(1, 0, 100, 100, noisy_img)
    score = engine._compute_brightness_uniformity(fig.image)
    assert score < 0.70


# ── ela computation ────────────────────────────────────────────────────────────

def test_ela_returns_float(engine):
    fig = make_figure()
    score = engine._compute_ela_score(fig.image)
    assert isinstance(score, float)
    assert score >= 0.0


# ── result structure ───────────────────────────────────────────────────────────

def test_no_figures_returns_clean_result(engine, tmp_path):
    # create minimal valid PDF with no images
    import fitz
    pdf_path = tmp_path / "empty.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This paper has no figures.")
    doc.save(str(pdf_path))
    doc.close()

    result = engine.analyze(str(pdf_path))
    assert isinstance(result, FigureForensicsResult)
    assert result.figures_found == 0
    assert result.risk_level == "low"
    assert result.risk_score == 0.0