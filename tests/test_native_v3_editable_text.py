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

    def test_text_runs_are_editable_source_han_sans_layers_with_red_and_black(self) -> None:
        path = ROOT / "weeks/2026-05-25_2026-05-29/work/native_v3/content.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        top_intro = data["native_text_blocks"]["top_intro"]
        colors = {tuple(run["color"]) for run in top_intro["runs"]}
        self.assertIn((232, 31, 31), colors)
        self.assertIn((24, 22, 20), colors)
        self.assertTrue(all(run["kind"] == "text" for run in top_intro["runs"]))
        self.assertTrue(all(run["font"].startswith("SourceHanSansCN-") for run in top_intro["runs"]))
        self.assertTrue(all("image" not in run for run in top_intro["runs"]))

    def test_key_blocks_have_no_overflow_flag(self) -> None:
        path = ROOT / "weeks/2026-05-25_2026-05-29/work/native_v3/content.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("top_intro", "funding", "risk_preference", "outlook", "strategy"):
            with self.subTest(key=key):
                self.assertFalse(data["native_text_blocks"][key]["overflow"])

    def test_strategy_preserves_numbering_and_plus_sign(self) -> None:
        path = ROOT / "weeks/2026-05-25_2026-05-29/work/native_v3/content.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        text = "".join(run["text"] for run in data["native_text_blocks"]["strategy"]["runs"])
        self.assertIn("1.", text)
        self.assertIn("2.", text)
        self.assertIn("固收+", text)


if __name__ == "__main__":
    unittest.main()
