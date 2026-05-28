from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path("/Users/a123/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3")


class NativeV3EditableTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            [str(PYTHON), "scripts/prepare_native_v3_content.py"],
            cwd=ROOT,
            check=True,
        )

    def test_v3_uses_native_text_blocks_not_rich_text_images(self) -> None:
        path = ROOT / "weeks/2026-05-25_2026-05-29/work/native_v3/content.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("/outputs/native_v3/", data["output_png"])
        self.assertNotIn("rich_text_assets", data)
        self.assertIn("native_text_blocks", data)
        self.assertIn("top_intro", data["native_text_blocks"])

    def test_text_blocks_are_single_paragraph_layers_with_style_ranges(self) -> None:
        path = ROOT / "weeks/2026-05-25_2026-05-29/work/native_v3/content.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        top_intro = data["native_text_blocks"]["top_intro"]
        colors = {tuple(style["color"]) for style in top_intro["style_ranges"]}
        self.assertIn((232, 31, 31), colors)
        self.assertIn((24, 22, 20), colors)
        self.assertEqual(top_intro["render_strategy"], "paragraph_text_style_ranges")
        self.assertNotIn("runs", top_intro)
        self.assertTrue(top_intro["font"].startswith("SourceHanSansCN-"))
        self.assertGreater(len(top_intro["text"]), 0)
        self.assertGreater(len(top_intro["style_ranges"]), 1)

    def test_key_blocks_have_no_overflow_flag(self) -> None:
        path = ROOT / "weeks/2026-05-25_2026-05-29/work/native_v3/content.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("top_intro", "funding", "risk_preference", "outlook", "strategy"):
            with self.subTest(key=key):
                self.assertFalse(data["native_text_blocks"][key]["overflow"])

    def test_strategy_preserves_numbering_and_plus_sign(self) -> None:
        path = ROOT / "weeks/2026-05-25_2026-05-29/work/native_v3/content.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        text = data["native_text_blocks"]["strategy"]["text"]
        self.assertIn("1.", text)
        self.assertIn("2.", text)
        self.assertIn("固收+", text)


if __name__ == "__main__":
    unittest.main()
