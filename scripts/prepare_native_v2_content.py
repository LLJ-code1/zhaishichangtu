from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from project_paths import OUTPUT_DIR, PSD_TEMPLATE, ROOT, WORK_DIR as WEEK_WORK_DIR


PSD = PSD_TEMPLATE
WORK_DIR = WEEK_WORK_DIR / "native_v2"
ASSET_DIR = WORK_DIR / "assets"
OUT_DIR = OUTPUT_DIR / "native_v2"
PSD_CONTENT_JSON = WEEK_WORK_DIR / "psd_content" / "原版.json"
RULES_PATH = ROOT / "schemas" / "red_rules.json"

FONT_HEITI = "/System/Library/Fonts/STHeiti Medium.ttc"

BLACK = (24, 22, 20, 255)
RED = (232, 31, 31, 255)
GREY = (92, 92, 92, 255)


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_HEITI, size)


def color_for(name: str) -> tuple[int, int, int, int]:
    return RED if name == "red" else BLACK


def text_width(draw: ImageDraw.ImageDraw, text: str, ft: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(text, font=ft)


def wrap_segments(
    segments: list[dict],
    ft: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[list[tuple[str, tuple[int, int, int, int]]]]:
    measure = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines: list[list[tuple[str, tuple[int, int, int, int]]]] = []
    line: list[tuple[str, tuple[int, int, int, int]]] = []
    line_width = 0.0

    for segment in segments:
        color = color_for(segment.get("color", "black"))
        for ch in segment["text"]:
            if ch == "\n":
                lines.append(line)
                line = []
                line_width = 0.0
                continue

            width = text_width(measure, ch, ft)
            if line and line_width + width > max_width:
                lines.append(line)
                line = []
                line_width = 0.0
            line.append((ch, color))
            line_width += width

    if line:
        lines.append(line)
    return lines


def measure_height(segments: list[dict], size: int, max_width: int, line_height: int) -> int:
    return len(wrap_segments(segments, font(size), max_width)) * line_height


def render_rich_text(
    path: Path,
    segments: list[dict],
    box: tuple[int, int],
    font_size: int,
    line_height: int,
    min_font_size: int = 22,
    fill: tuple[int, int, int, int] | None = None,
) -> None:
    width, height = box
    size = font_size
    leading_ratio = line_height / font_size

    while size > min_font_size:
        candidate_line_height = round(size * leading_ratio)
        if measure_height(segments, size, width, candidate_line_height) <= height:
            line_height = candidate_line_height
            break
        size -= 1

    ft = font(size)
    lines = wrap_segments(segments, ft, width)
    image = Image.new("RGBA", (width, height), fill or (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    y = 0
    for line in lines:
        x = 0
        run = ""
        run_color: tuple[int, int, int, int] | None = None
        run_x = 0.0

        def flush() -> None:
            nonlocal run, run_color, run_x
            if not run:
                return
            draw.text((round(run_x), y), run, font=ft, fill=run_color or BLACK)
            run = ""
            run_color = None

        for ch, color in line:
            if run_color is None:
                run_color = color
                run_x = x
            elif color != run_color:
                flush()
                run_color = color
                run_x = x
            run += ch
            x += text_width(draw, ch, ft)
        flush()
        y += line_height

    image.save(path)


def split_rich_text(text: str, phrases: list[str]) -> list[dict]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from extract_word_psd_content import split_rich_text as split

    return split(text, phrases)


def numbered_funding(text: str) -> str:
    first = "央行在公开市场操作上净投放1490亿元。"
    if text.startswith(first):
        return text.replace(first, f"1、{first}\n2、", 1)
    return f"1、{text}"


def numbered_risk_preference(text: str) -> str:
    text = text.replace("权益方面，", "1、权益方面，", 1)
    text = text.replace("商品方面，", "\n2、商品方面，", 1)
    return text


def render_text_assets(content: dict, rules: dict) -> dict[str, str]:
    fields = content["fields"]
    rich = content["rich_text"]
    field_rules = rules["field_rules"]

    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    asset_specs = {
        "top_intro": (rich["top_intro"], (901, 624), 36, 56),
        "market_sentence": (rich["market_sentence"], (915, 52), 34, 48),
        "funding": (
            split_rich_text(numbered_funding(fields["funding"]), field_rules["funding"]),
            (576, 292),
            36,
            54,
        ),
        "fund_chart_title": (rich["fund_chart_title"], (445, 87), 30, 40),
        "risk_preference": (
            split_rich_text(numbered_risk_preference(fields["risk_preference"]), field_rules["risk_preference"]),
            (587, 292),
            36,
            54,
        ),
        "outlook": (rich["outlook"], (889, 292), 34, 52),
        "strategy": (rich["strategy"], (899, 355), 36, 56),
    }

    rendered = {}
    for name, (segments, box, size, line_height) in asset_specs.items():
        path = ASSET_DIR / f"{name}.png"
        render_rich_text(path, segments, box, size, line_height)
        rendered[name] = str(path)

    return rendered


def main() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import extract_word_psd_content
    import prepare_basic_v0_assets

    # Rebuild upstream JSON and chart assets so v2 always reflects current Word inputs.
    prepare_basic_v0_assets.main()
    extract_word_psd_content.main()

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    content = json.loads(PSD_CONTENT_JSON.read_text(encoding="utf-8"))
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    fields = content["fields"]
    meta = content["meta"]

    rich_text_assets = render_text_assets(content, rules)

    data = {
        "original_psd": str(PSD),
        "output_psd": str(OUT_DIR / "金葵花债市周观察20260521_原生组件v2.psd"),
        "output_png": str(OUT_DIR / "金葵花债市周观察20260521_原生组件v2.png"),
        "x0": 3042,
        "width": 1125,
        "height": 7037,
        "date": meta["date"],
        "top_title": fields["top_title"],
        "source_risk": f"{fields['source']}\n{fields['risk_warning']}",
        "psd_content_json": str(PSD_CONTENT_JSON),
        "assets": {
            "table": str(WEEK_WORK_DIR / "basic_v0" / "assets" / "yield_table.png"),
            "yield_chart": str(WEEK_WORK_DIR / "basic_v0" / "assets" / "yield_chart.png"),
            "fund_chart": str(WEEK_WORK_DIR / "basic_v0" / "assets" / "fund_chart.png"),
        },
        "rich_text_assets": rich_text_assets,
        "notes": [
            "v2 renders red-emphasis paragraphs as transparent text assets, then places them into the original PSD text-layer bounds.",
            "Line charts are regenerated with transparent backgrounds, so the original PSD card background remains visible.",
            "This avoids clipping from single fixed Photoshop text layers, but these rich paragraphs are raster assets in the PSD.",
        ],
    }

    out = WORK_DIR / "content.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    print(data["output_png"])


if __name__ == "__main__":
    main()
