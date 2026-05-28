from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path("/Users/a123/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3")


class NativeV2AssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            [str(PYTHON), "scripts/prepare_native_v2_content.py"],
            cwd=ROOT,
            check=True,
        )

    def test_chart_assets_have_transparent_background(self) -> None:
        for path in (
            ROOT / "weeks/2026-05-25_2026-05-29/work/basic_v0/assets/yield_chart.png",
            ROOT / "weeks/2026-05-25_2026-05-29/work/basic_v0/assets/fund_chart.png",
        ):
            image = Image.open(path).convert("RGBA")
            alpha = image.getchannel("A")
            self.assertEqual(alpha.getextrema()[0], 0, path)
            self.assertEqual(image.getpixel((0, 0))[3], 0, path)

    def test_yield_chart_asset_uses_psd_slot_aspect_ratio(self) -> None:
        path = ROOT / "weeks/2026-05-25_2026-05-29/work/basic_v0/assets/yield_chart.png"

        with Image.open(path) as image:
            self.assertEqual(image.size, (880, 600))

    def test_top_intro_rich_text_asset_is_transparent_and_has_red_text(self) -> None:
        path = ROOT / "weeks/2026-05-25_2026-05-29/work/native_v2/assets/top_intro.png"
        image = Image.open(path).convert("RGBA")
        alpha = image.getchannel("A")
        self.assertEqual(alpha.getextrema()[0], 0)
        red_pixels = sum(
            1
            for r, g, b, a in image.getdata()
            if a > 0 and r > 180 and g < 80 and b < 80
        )
        self.assertGreater(red_pixels, 50)

    def test_native_v2_content_points_to_v2_outputs_and_rich_assets(self) -> None:
        path = ROOT / "weeks/2026-05-25_2026-05-29/work/native_v2/content.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("/outputs/native_v2/", data["output_png"])
        self.assertIn("top_intro", data["rich_text_assets"])
        self.assertTrue(Path(data["rich_text_assets"]["top_intro"]).exists())


if __name__ == "__main__":
    unittest.main()
