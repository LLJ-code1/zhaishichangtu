# Photoshop 基础长图 v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one original-version Photoshop long image from the modified Word content without using a full-image overlay.

**Architecture:** Python prepares structured JSON plus table/chart/image assets. Photoshop JSX opens the original PSD, hides old body content, creates a new `基础长图v0_主体` group with editable text layers and image layers, exports a PNG preview, and saves a new PSD.

**Tech Stack:** Python 3, python-docx, Pillow, Photoshop ExtendScript JSX.

---

### Task 1: Prepare Structured Content And Assets

**Files:**
- Create: `scripts/prepare_basic_v0_assets.py`
- Output: `work/basic_v0/content.json`
- Output: `work/basic_v0/assets/*.png`

- [ ] Parse `金葵花债市周度复盘20260521 - 修改版本.docx`.
- [ ] Extract title, date, intro, bond performance text, yield table, outlook, source, and strategy text.
- [ ] Extract chart series from DOCX chart XML.
- [ ] Generate table, yield chart, fund chart, and hero image assets.
- [ ] Validate output files exist and image dimensions are readable.

### Task 2: Build Photoshop JSX

**Files:**
- Create: `scripts/build_basic_long_image_v0.jsx`
- Output: `长图/基础长图v0/金葵花债市周观察20260521_基础v0.psd`
- Output: `长图/基础长图v0/金葵花债市周观察20260521_基础v0.png`

- [ ] Open the original PSD.
- [ ] Hide the old body text/chart/card layers that occupy the long image right side.
- [ ] Create `基础长图v0_主体`.
- [ ] Add section title bars and card backgrounds as raster layers.
- [ ] Add editable Photoshop text layers for all body text.
- [ ] Place prepared table/chart/hero image assets as image layers.
- [ ] Use y-position accumulation so cards do not overlap.
- [ ] Save PSD and export PNG preview.

### Task 3: Verify

**Files:**
- Check: `长图/基础长图v0/金葵花债市周观察20260521_基础v0.png`
- Check: `长图/基础长图v0/金葵花债市周观察20260521_基础v0.psd`

- [ ] Confirm PSD and PNG exist.
- [ ] Confirm PNG dimensions.
- [ ] Open the PNG visually and inspect top, middle, and bottom crops.
- [ ] Confirm no full-image overlay layer is used.
- [ ] Record remaining issues if any.
