from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class EngineeringContractTests(unittest.TestCase):
    def test_engineering_spec_records_native_v3_policy(self) -> None:
        text = (ROOT / "docs/engineering_spec.md").read_text(encoding="utf-8")

        self.assertIn("native_v3", text)
        self.assertIn("复用原 PSD", text)
        self.assertIn("schemas/psd_layer_map.json", text)

    def test_layout_constants_centralize_common_canvas_and_spacing_values(self) -> None:
        text = (ROOT / "scripts/layout_constants.jsx").read_text(encoding="utf-8")

        self.assertIn("var CANVAS_WIDTH", text)
        self.assertIn("var CONTENT_LEFT", text)
        self.assertIn("var SECTION_GAP", text)
        self.assertIn("function measureLayerHeight", text)

    def test_psd_layer_map_has_canvas_text_and_image_sections(self) -> None:
        data = json.loads((ROOT / "schemas/psd_layer_map.json").read_text(encoding="utf-8"))

        self.assertEqual(data["canvas"]["width"], 1125)
        self.assertEqual(data["canvas"]["x0"], 3042)
        self.assertIn("text_layers", data)
        self.assertIn("image_layers", data)
        self.assertEqual(data["image_layers"]["table"]["target_layer_name"], "表1")

    def test_word_extraction_records_external_excel_chart_source(self) -> None:
        import extract_word_psd_content

        docx_path = ROOT / "weeks/2026-05-25_2026-05-29/inputs/word/variants/债市周观察原版.docx"
        workbooks = extract_word_psd_content.external_chart_workbooks(docx_path)

        self.assertEqual(len(workbooks), 2)
        self.assertTrue(all(item["target_mode"] == "External" for item in workbooks))
        self.assertTrue(all("金葵花-数据底表.xlsx" in item["target"] for item in workbooks))

        rules = json.loads((ROOT / "schemas/red_rules.json").read_text(encoding="utf-8"))
        data = extract_word_psd_content.build_variant("原版", docx_path, rules)
        self.assertEqual(data["assets"]["chart_external_workbooks"], workbooks)


if __name__ == "__main__":
    unittest.main()
