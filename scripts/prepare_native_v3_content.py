from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from project_paths import OUTPUT_DIR, PSD_TEMPLATE, ROOT, WORK_DIR as WEEK_WORK_DIR


PSD = PSD_TEMPLATE
WORK_DIR = WEEK_WORK_DIR / "native_v3"
OUT_DIR = OUTPUT_DIR / "native_v3"
PSD_CONTENT_JSON = WEEK_WORK_DIR / "psd_content" / "原版.json"
RULES_PATH = ROOT / "schemas" / "red_rules.json"

FONT_PATHS = {
    "regular": "/Users/a123/Library/Fonts/SourceHanSansCN-Regular.otf",
    "medium": "/Users/a123/Library/Fonts/SourceHanSansCN-Medium.otf",
    "bold": "/Users/a123/Library/Fonts/SourceHanSansCN-Bold.otf",
}

FONT_POSTSCRIPT = {
    "regular": "SourceHanSansCN-Regular",
    "medium": "SourceHanSansCN-Medium",
    "bold": "SourceHanSansCN-Bold",
}

BLACK = (24, 22, 20)
RED = (232, 31, 31)


def font(size: int, weight: str) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATHS[weight], size)


def text_width(draw: ImageDraw.ImageDraw, text: str, ft: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(text, font=ft)


def color_for(name: str) -> tuple[int, int, int]:
    return RED if name == "red" else BLACK


TOKEN_RE = re.compile(
    r"\d+月[A-Za-z]+|[A-Za-z]+[A-Za-z0-9.+%/-]*|[-+]?\d+(?:\.\d+)?%?|[.+%/+-]|[\u4e00-\u9fff]+|[^\u4e00-\u9fffA-Za-z0-9.+%/-]"
)


def iter_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_RE.finditer(text):
        value = match.group(0)
        if value == "\n":
            tokens.append(value)
        elif re.fullmatch(r"[\u4e00-\u9fff]+", value):
            tokens.extend(value)
        else:
            tokens.append(value)
    return tokens


def wrap_segments(
    segments: list[dict],
    ft: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[list[tuple[str, tuple[int, int, int]]]]:
    measure = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines: list[list[tuple[str, tuple[int, int, int]]]] = []
    line: list[tuple[str, tuple[int, int, int]]] = []
    line_width = 0.0

    for segment in segments:
        color = color_for(segment.get("color", "black"))
        for token in iter_tokens(segment["text"]):
            if token == "\n":
                lines.append(line)
                line = []
                line_width = 0.0
                continue

            width = text_width(measure, token, ft)
            if width > max_width:
                token_parts = list(token)
            else:
                token_parts = [token]

            for part in token_parts:
                width = text_width(measure, part, ft)
                if line and line_width + width > max_width:
                    lines.append(line)
                    line = []
                    line_width = 0.0
                line.append((part, color))
                line_width += width

    if line:
        lines.append(line)
    return lines


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


def build_native_text_block(
    key: str,
    match: dict,
    segments: list[dict],
    box: tuple[int, int],
    font_size: int,
    line_height: int,
    weight: str = "medium",
    min_font_size: int = 20,
) -> dict:
    width, height = box
    size = font_size
    leading_ratio = line_height / font_size

    while size > min_font_size:
        candidate_line_height = round(size * leading_ratio)
        lines = wrap_segments(segments, font(size, weight), width)
        if len(lines) * candidate_line_height <= height:
            line_height = candidate_line_height
            break
        size -= 1
    else:
        lines = wrap_segments(segments, font(size, weight), width)
        line_height = round(size * leading_ratio)

    ft = font(size, weight)
    measure = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    runs: list[dict] = []

    for line_index, line in enumerate(lines):
        x = 0.0
        y = line_index * line_height + round(size * 0.92)
        run_text = ""
        run_color: tuple[int, int, int] | None = None
        run_x = 0.0

        def flush() -> None:
            nonlocal run_text, run_color, run_x
            if not run_text:
                return
            runs.append(
                {
                    "kind": "text",
                    "text": run_text,
                    "x": round(run_x),
                    "y": y,
                    "size": size,
                    "leading": line_height,
                    "font": FONT_POSTSCRIPT[weight],
                    "color": list(run_color or BLACK),
                }
            )
            run_text = ""
            run_color = None

        for ch, color in line:
            if run_color is None:
                run_color = color
                run_x = x
            elif color != run_color:
                flush()
                run_color = color
                run_x = x
            run_text += ch
            x += text_width(measure, ch, ft)
        flush()

    return {
        "key": key,
        "match": match,
        "box": {"width": width, "height": height},
        "font_family": "Source Han Sans CN",
        "editable": True,
        "overflow": len(lines) * line_height > height,
        "runs": runs,
    }


def build_text_blocks(content: dict, rules: dict) -> dict[str, dict]:
    fields = content["fields"]
    rich = content["rich_text"]
    field_rules = rules["field_rules"]

    return {
        "top_intro": build_native_text_block(
            "top_intro",
            {"type": "prefix", "text": "上周债券收益率窄幅震荡"},
            rich["top_intro"],
            (901, 624),
            36,
            56,
            "medium",
        ),
        "market_sentence": build_native_text_block(
            "market_sentence",
            {"type": "prefix", "text": "5月8日-5月14日"},
            rich["market_sentence"],
            (915, 52),
            34,
            48,
            "medium",
        ),
        "funding": build_native_text_block(
            "funding",
            {"type": "prefix", "text": "1、央行在公开市场操作上净回笼500亿元"},
            split_rich_text(numbered_funding(fields["funding"]), field_rules["funding"]),
            (576, 292),
            36,
            54,
            "medium",
        ),
        "fund_chart_title": build_native_text_block(
            "fund_chart_title",
            {"type": "prefix", "text": "DR001/DR007上周情况"},
            rich["fund_chart_title"],
            (445, 87),
            30,
            40,
            "medium",
        ),
        "risk_preference": build_native_text_block(
            "risk_preference",
            {"type": "prefix", "text": "1、特朗普访华落地"},
            split_rich_text(numbered_risk_preference(fields["risk_preference"]), field_rules["risk_preference"]),
            (587, 292),
            36,
            54,
            "medium",
        ),
        "outlook": build_native_text_block(
            "outlook",
            {"type": "prefix", "text": "展望后市，重点关注特朗普访华进展"},
            rich["outlook"],
            (889, 292),
            34,
            52,
            "medium",
        ),
        "strategy": build_native_text_block(
            "strategy",
            {"type": "contains", "text": "境内债券市场"},
            rich["strategy"],
            (899, 355),
            36,
            56,
            "medium",
        ),
    }


def main() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import extract_word_psd_content
    import prepare_basic_v0_assets

    prepare_basic_v0_assets.main()
    extract_word_psd_content.main()

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    content = json.loads(PSD_CONTENT_JSON.read_text(encoding="utf-8"))
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    fields = content["fields"]
    meta = content["meta"]

    data = {
        "original_psd": str(PSD),
        "output_psd": str(OUT_DIR / "金葵花债市周观察20260521_原生文本v3.psd"),
        "output_png": str(OUT_DIR / "金葵花债市周观察20260521_原生文本v3.png"),
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
        "native_text_blocks": build_text_blocks(content, rules),
        "notes": [
            "v3 keeps rich paragraphs as editable Photoshop text layers.",
            "Each red or black run is a separate point text layer using Source Han Sans CN.",
            "Table and chart replacements remain image layers.",
        ],
    }

    out = WORK_DIR / "content.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    print(data["output_png"])


if __name__ == "__main__":
    main()
