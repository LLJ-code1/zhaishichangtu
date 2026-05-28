from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path("/Users/a123/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3")


class NativeV3WorkflowContractTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        subprocess.run(
            [str(PYTHON), "scripts/prepare_native_v3_content.py", "--variant", "原版"],
            cwd=ROOT,
            check=True,
        )

    def test_prepare_native_v3_accepts_variant_and_records_source_json(self) -> None:
        subprocess.run(
            [str(PYTHON), "scripts/prepare_native_v3_content.py", "--variant", "固收+"],
            cwd=ROOT,
            check=True,
        )

        path = ROOT / "weeks/2026-05-25_2026-05-29/work/native_v3/content.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(data["variant"], "固收+")
        self.assertTrue(data["psd_content_json"].endswith("work/psd_content/固收+.json"))
        self.assertIn("固收+_原生文本v3", data["output_png"])
        self.assertEqual(
            data["layout_policy"],
            "preserve_original_psd_components_then_replace_mapped_content",
        )

    def test_psd_layer_map_declares_native_text_boxes(self) -> None:
        path = ROOT / "schemas/psd_layer_map.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        native_keys = [
            key
            for key, item in data["text_layers"].items()
            if item["strategy"] == "paragraph_rich_text"
        ]

        self.assertEqual(
            native_keys,
            [
                "top_intro",
                "market_sentence",
                "funding",
                "fund_chart_title",
                "risk_preference",
                "outlook",
                "strategy",
            ],
        )
        for key in native_keys:
            with self.subTest(key=key):
                item = data["text_layers"][key]
                self.assertIn(item["match"]["type"], {"prefix", "contains", "exact"})
                self.assertGreater(item["box"]["width"], 0)
                self.assertGreater(item["box"]["height"], 0)

    def test_generated_native_blocks_follow_layer_map_keys(self) -> None:
        subprocess.run(
            [str(PYTHON), "scripts/prepare_native_v3_content.py", "--variant", "原版"],
            cwd=ROOT,
            check=True,
        )

        layer_map = json.loads((ROOT / "schemas/psd_layer_map.json").read_text(encoding="utf-8"))
        generated = json.loads(
            (ROOT / "weeks/2026-05-25_2026-05-29/work/native_v3/content.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            key
            for key, item in layer_map["text_layers"].items()
            if item["strategy"] == "paragraph_rich_text"
        }
        self.assertEqual(set(generated["native_text_blocks"].keys()), expected)

    def test_manual_target_profile_compacts_hero_text_and_canvas_height(self) -> None:
        subprocess.run(
            [str(PYTHON), "scripts/prepare_native_v3_content.py", "--variant", "原版"],
            cwd=ROOT,
            check=True,
        )

        generated = json.loads(
            (ROOT / "weeks/2026-05-25_2026-05-29/work/native_v3/content.json").read_text(
                encoding="utf-8"
            )
        )
        top_intro_text = generated["native_text_blocks"]["top_intro"]["text"]

        self.assertIn("5月LPR利率公布，维持不变。", top_intro_text)
        self.assertNotIn("权益方面", top_intro_text)
        risk_text = generated["native_text_blocks"]["risk_preference"]["text"]
        self.assertIn("受到美伊停战协议传出进展", risk_text)
        self.assertNotIn("黄金收于4500上方", risk_text)
        self.assertEqual(generated["height"], 6893)
        self.assertEqual(generated["layout_adjustments"]["shift_y"], -144)
        self.assertEqual(generated["layout_adjustments"]["shift_after_y"], 1958)

    def test_prepare_native_v3_accepts_date_overrides_for_manual_target(self) -> None:
        subprocess.run(
            [
                str(PYTHON),
                "scripts/prepare_native_v3_content.py",
                "--variant",
                "原版",
                "--display-date",
                "2026-5-27",
                "--source-date",
                "2026年5月22日",
            ],
            cwd=ROOT,
            check=True,
        )

        generated = json.loads(
            (ROOT / "weeks/2026-05-25_2026-05-29/work/native_v3/content.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(generated["date"], "2026-5-27")
        self.assertIn("截至2026年5月22日", generated["source_risk"])

    def test_layout_shift_moves_layer_sets_as_groups(self) -> None:
        script = (ROOT / "scripts/build_native_psd_v3.jsx").read_text(encoding="utf-8")

        self.assertIn("function shiftVisibleLayersBelow", script)
        self.assertIn('layer.typename === "LayerSet"', script)
        self.assertNotIn("function shiftVisibleArtLayersBelow", script)

    def test_layout_shift_catches_components_spanning_the_boundary(self) -> None:
        layer_map = json.loads((ROOT / "schemas/psd_layer_map.json").read_text(encoding="utf-8"))
        adjustments = layer_map["layout_adjustments"]
        script = (ROOT / "scripts/build_native_psd_v3.jsx").read_text(encoding="utf-8")

        self.assertEqual(adjustments["shift_when"], "bottom_after_boundary")
        self.assertLessEqual(adjustments["max_shift_layer_height"], 2600)
        self.assertEqual(adjustments["min_shift_layer_top"], 1200)
        self.assertIn("box.bottom > shiftAfterY", script)

    def test_manual_target_profile_declares_targeted_offsets(self) -> None:
        layer_map = json.loads((ROOT / "schemas/psd_layer_map.json").read_text(encoding="utf-8"))
        adjustments = layer_map["layout_adjustments"]
        script = (ROOT / "scripts/build_native_psd_v3.jsx").read_text(encoding="utf-8")

        names = {item["layer_name"] for item in adjustments["targeted_offsets"]}
        self.assertIn("图层 168", names)
        self.assertIn("版块1标题卡", names)
        self.assertIn("applyTargetedOffsets", script)
        self.assertIn("matchesTargetedOffset", script)

    def test_dynamic_gap_profile_flows_sections_after_content_is_placed(self) -> None:
        layer_map = json.loads((ROOT / "schemas/psd_layer_map.json").read_text(encoding="utf-8"))
        dynamic = layer_map["layout_adjustments"]["dynamic_gaps"]
        script = (ROOT / "scripts/build_native_psd_v3.jsx").read_text(encoding="utf-8")

        self.assertTrue(dynamic["enabled"])
        self.assertEqual(
            [section["name"] for section in dynamic["sections"]],
            ["hero", "market", "analysis", "outlook", "strategy"],
        )
        self.assertEqual(dynamic["sections"][0]["background"]["bottom_gap"], 61)
        self.assertEqual(dynamic["sections"][2]["background"]["bottom_gap"], 184)
        self.assertIn("function applyDynamicGaps", script)
        self.assertIn("shiftLayersTopAtOrAfter", script)
        self.assertIn("markLinkedLayerSet", script)
        self.assertIn("processedLayerIds", script)

    def test_builder_uses_single_paragraph_rich_text_layers(self) -> None:
        script = (ROOT / "scripts/build_native_psd_v3.jsx").read_text(encoding="utf-8")

        self.assertIn("styleTextLayerWithRanges", script)
        self.assertIn("TextType.PARAGRAPHTEXT", script)
        self.assertIn("style_ranges", script)
        self.assertNotIn("function createTextRun", script)


if __name__ == "__main__":
    unittest.main()
