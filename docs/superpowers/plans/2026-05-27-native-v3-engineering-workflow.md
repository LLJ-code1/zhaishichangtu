# Native V3 Engineering Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing `native_v3` Photoshop long-image flow into a parameterized, documented, schema-checked workflow that can regenerate the original PSD and produce variant-ready content plans.

**Architecture:** Keep `native_v3` as the production line because it preserves original PSD components and editable text. Add a canonical engineering spec, centralized layout constants, a PSD layer map, Python-side layout planning helpers, and tests that lock down variant selection, layer-map integrity, and generated output metadata.

**Tech Stack:** Python 3 with `python-docx`, Pillow, unittest; Photoshop ExtendScript JSX; JSON schema-style local validation; existing weekly directory structure under `weeks/<date-range>/`.

---

### Task 1: Capture The Engineering Contract

**Files:**
- Create: `docs/engineering_spec.md`
- Create: `scripts/layout_constants.jsx`
- Create: `schemas/psd_layer_map.json`

- [ ] **Step 1: Add engineering spec**

Create `docs/engineering_spec.md` from the supplied engineering brief, adapted to state that `native_v3` keeps original PSD components and applies flow-layout rules by moving/resizing mapped PSD groups rather than redrawing the whole body.

- [ ] **Step 2: Add JSX layout constants**

Create `scripts/layout_constants.jsx` from the supplied constants file. Keep constants global so Photoshop JSX can include it later.

- [ ] **Step 3: Add PSD semantic layer map**

Create `schemas/psd_layer_map.json` with semantic keys used by `prepare_native_v3_content.py` and `build_native_psd_v3.jsx`:

```json
{
  "schema_version": "1.0",
  "canvas": {"x0": 3042, "width": 1125, "height": 7037},
  "text_layers": {
    "date": {"match": {"type": "exact", "text": "2026-5-18"}, "strategy": "replace_text"},
    "top_title": {"match": {"type": "exact", "text": "国债收益率窄幅震荡，曲线走平"}, "strategy": "replace_text"},
    "top_intro": {"match": {"type": "prefix", "text": "上周债券收益率窄幅震荡"}, "strategy": "paragraph_rich_text", "box": {"width": 901, "height": 624}},
    "market_sentence": {"match": {"type": "prefix", "text": "5月8日-5月14日"}, "strategy": "paragraph_rich_text", "box": {"width": 915, "height": 52}},
    "funding": {"match": {"type": "prefix", "text": "1、央行在公开市场操作上净回笼500亿元"}, "strategy": "paragraph_rich_text", "box": {"width": 576, "height": 292}},
    "fund_chart_title": {"match": {"type": "prefix", "text": "DR001/DR007上周情况"}, "strategy": "paragraph_rich_text", "box": {"width": 445, "height": 87}},
    "risk_preference": {"match": {"type": "prefix", "text": "1、特朗普访华落地"}, "strategy": "paragraph_rich_text", "box": {"width": 587, "height": 292}},
    "outlook": {"match": {"type": "prefix", "text": "展望后市，重点关注特朗普访华进展"}, "strategy": "paragraph_rich_text", "box": {"width": 889, "height": 292}},
    "strategy": {"match": {"type": "contains", "text": "境内债券市场"}, "strategy": "paragraph_rich_text", "box": {"width": 899, "height": 355}},
    "source_risk": {"match": {"type": "prefix", "text": "数据来源：wind"}, "strategy": "replace_text"}
  },
  "image_layers": {
    "table": {"target_layer_name": "表1"},
    "yield_chart": {"target_layer_name": "图片1"},
    "fund_chart": {"target_layer_name": "图片2"}
  }
}
```

### Task 2: Write Failing Tests For Parameterized Native V3

**Files:**
- Modify: `tests/test_native_v3_editable_text.py`
- Create: `tests/test_native_v3_workflow_contract.py`

- [ ] **Step 1: Add tests for CLI variant support**

Add a unittest that runs:

```bash
/Users/a123/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/prepare_native_v3_content.py --variant 固收+
```

Expected after implementation: output JSON points to `psd_content/固收+.json`, output PNG filename contains `固收+`, and `variant` equals `固收+`.

- [ ] **Step 2: Add tests for layer-map usage**

Add a unittest that loads `schemas/psd_layer_map.json` and asserts all native text block keys have `match`, `box.width`, and `box.height`.

- [ ] **Step 3: Verify red**

Run:

```bash
/Users/a123/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_native_v3_workflow_contract -v
```

Expected: failures because `--variant` and layer-map driven output are not implemented yet.

### Task 3: Implement Native V3 Variant And Layer-Map Support

**Files:**
- Modify: `scripts/prepare_native_v3_content.py`
- Modify: `scripts/build_native_psd_v3.jsx`

- [ ] **Step 1: Add CLI args to Python**

Add `argparse` support:

```python
parser.add_argument("--variant", choices=("原版", "固收+", "债市"), default="原版")
parser.add_argument("--content-json", type=Path)
```

Use `psd_content/<variant>.json` unless `--content-json` is supplied.

- [ ] **Step 2: Load PSD layer map**

Add `LAYER_MAP_PATH = ROOT / "schemas" / "psd_layer_map.json"` and use it for `canvas`, native text block `match`, and `box` values. Keep font sizes and line heights in Python for now.

- [ ] **Step 3: Add variant metadata to generated content**

The generated `work/native_v3/content.json` must include:

```json
{
  "variant": "原版",
  "psd_layer_map": ".../schemas/psd_layer_map.json",
  "layout_policy": "preserve_original_psd_components_then_replace_mapped_content"
}
```

- [ ] **Step 4: Parameterize output filenames**

Use filenames:

```text
金葵花债市周观察20260521_<variant>_原生文本v3.psd
金葵花债市周观察20260521_<variant>_原生文本v3.png
```

For backward compatibility, when variant is `原版`, also keep the existing original output names in generated metadata if the Photoshop script consumes them.

- [ ] **Step 5: Teach JSX exact matching**

Update `build_native_psd_v3.jsx` so `findTextLayerByMatch` supports `exact`, `prefix`, and `contains`. Use the generated JSON matches instead of hard-coded date/title prefixes for native text blocks.

### Task 4: Add Contract Tests And Existing Regression Coverage

**Files:**
- Modify: `tests/test_native_v3_editable_text.py`
- Create: `tests/test_engineering_contract.py`

- [ ] **Step 1: Test generated original content still uses editable runs**

Keep existing assertions for Source Han Sans, red/black colors, no image runs, and no overflow.

- [ ] **Step 2: Test engineering docs exist**

Assert these files exist and include the expected core phrases:

```text
docs/engineering_spec.md
scripts/layout_constants.jsx
schemas/psd_layer_map.json
```

- [ ] **Step 3: Test layer map and native text block keys stay aligned**

Assert the generated JSON has native blocks for all layer-map entries with `strategy = paragraph_rich_text`.

### Task 5: Generate Original Native V3 PSD

**Files:**
- Generated: `weeks/2026-05-25_2026-05-29/work/native_v3/content.json`
- Generated: `weeks/2026-05-25_2026-05-29/outputs/native_v3/金葵花债市周观察20260521_原版_原生文本v3.psd`
- Generated: `weeks/2026-05-25_2026-05-29/outputs/native_v3/金葵花债市周观察20260521_原版_原生文本v3.png`

- [ ] **Step 1: Run Python content preparation**

Run:

```bash
/Users/a123/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/prepare_native_v3_content.py --variant 原版
```

Expected: exits 0 and prints `work/native_v3/content.json`.

- [ ] **Step 2: Run Photoshop JSX**

Run the already approved Photoshop AppleScript command:

```bash
osascript -e 'tell application "Adobe Photoshop 2025" to do javascript file "/Users/a123/Downloads/债市周观察/债市周观察/scripts/build_native_psd_v3.jsx"'
```

Expected: exits 0 and writes the original PSD/PNG paths from generated JSON.

- [ ] **Step 3: Inspect generated PSD text layers**

Run the existing inspection JSX and confirm `work/native_v3/text_layers.tsv` contains Photoshop `TEXT` rows with Source Han Sans CN and red/black colors.

### Task 6: Verify

**Files:**
- Modify only if tests expose defects.

- [ ] **Step 1: Run full unittest suite**

Run:

```bash
/Users/a123/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Check git diff**

Run:

```bash
git status --short
git diff --stat
```

Expected: only planned docs, schema, scripts, tests, and generated native_v3 outputs changed.
