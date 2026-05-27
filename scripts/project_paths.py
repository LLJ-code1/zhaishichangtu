from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURRENT_WEEK = "2026-05-25_2026-05-29"
WEEK_DIR = ROOT / "weeks" / CURRENT_WEEK

INPUT_DIR = WEEK_DIR / "inputs"
WORD_DIR = INPUT_DIR / "word"
RAW_WORD_DIR = WORD_DIR / "raw"
EDITED_WORD_DIR = WORD_DIR / "edited"
VARIANT_WORD_DIR = WORD_DIR / "variants"
PSD_DIR = INPUT_DIR / "psd"
REFERENCE_LONG_IMAGE_DIR = INPUT_DIR / "reference_long_images"

OUTPUT_DIR = WEEK_DIR / "outputs"
WORK_DIR = WEEK_DIR / "work"

RAW_DOCX = RAW_WORD_DIR / "金葵花债市周度复盘20260521.docx"
EDITED_DOCX = EDITED_WORD_DIR / "金葵花债市周度复盘20260521 - 修改版本.docx"
PSD_TEMPLATE = PSD_DIR / "债市周报.psd"
