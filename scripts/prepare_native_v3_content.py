from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from project_paths import OUTPUT_DIR, PSD_TEMPLATE, ROOT, WORK_DIR as WEEK_WORK_DIR


PSD = PSD_TEMPLATE
WORK_DIR = WEEK_WORK_DIR / "native_v3"
OUT_DIR = OUTPUT_DIR / "native_v3"
RULES_PATH = ROOT / "schemas" / "red_rules.json"
LAYER_MAP_PATH = ROOT / "schemas" / "psd_layer_map.json"

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


def cut_after_marker(text: str, marker: str | None) -> str:
    if not marker:
        return text
    index = text.find(marker)
    if index == -1:
        return text
    return text[: index + len(marker)]


def replace_source_date(source: str, source_date: str | None) -> str:
    if not source_date:
        return source
    return re.sub(r"截至\d{4}年\d{1,2}月\d{1,2}日", f"截至{source_date}", source)


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
    text = "".join(segment["text"] for segment in segments if segment["text"])
    style_ranges: list[dict] = []
    cursor = 0
    for segment in segments:
        segment_text = segment["text"]
        if not segment_text:
            continue
        start = cursor
        cursor += len(segment_text)
        color = color_for(segment.get("color", "black"))
        if style_ranges and style_ranges[-1]["color"] == list(color):
            style_ranges[-1]["to"] = cursor
            style_ranges[-1]["text"] += segment_text
            continue
        style_ranges.append(
            {
                "from": start,
                "to": cursor,
                "text": segment_text,
                "color": list(color),
                "font": FONT_POSTSCRIPT[weight],
                "size": size,
                "leading": line_height,
            }
        )

    return {
        "key": key,
        "match": match,
        "box": {"width": width, "height": height},
        "font_family": "Source Han Sans CN",
        "font": FONT_POSTSCRIPT[weight],
        "size": size,
        "leading": line_height,
        "editable": True,
        "render_strategy": "paragraph_text_style_ranges",
        "text": text,
        "style_ranges": style_ranges,
        "estimated_height": len(lines) * line_height,
        "estimated_width": round(max((sum(text_width(measure, ch, ft) for ch, _ in line) for line in lines), default=0)),
        "overflow": len(lines) * line_height > height,
    }


def text_layer_spec(layer_map: dict, key: str) -> tuple[dict, tuple[int, int]]:
    spec = layer_map["text_layers"][key]
    box = spec["box"]
    return spec["match"], (int(box["width"]), int(box["height"]))


def build_text_blocks(content: dict, rules: dict, layer_map: dict) -> dict[str, dict]:
    fields = content["fields"]
    rich = content["rich_text"]
    field_rules = rules["field_rules"]
    content_rules = layer_map.get("content_rules", {})
    top_intro_text = cut_after_marker(
        fields["top_intro"],
        content_rules.get("top_intro_cut_after"),
    )
    top_intro_segments = split_rich_text(top_intro_text, field_rules["top_intro"])
    risk_preference_text = content_rules.get("risk_preference_override")
    if not risk_preference_text:
        risk_preference_text = numbered_risk_preference(fields["risk_preference"])

    top_intro_match, top_intro_box = text_layer_spec(layer_map, "top_intro")
    market_sentence_match, market_sentence_box = text_layer_spec(layer_map, "market_sentence")
    funding_match, funding_box = text_layer_spec(layer_map, "funding")
    fund_chart_title_match, fund_chart_title_box = text_layer_spec(layer_map, "fund_chart_title")
    risk_preference_match, risk_preference_box = text_layer_spec(layer_map, "risk_preference")
    outlook_match, outlook_box = text_layer_spec(layer_map, "outlook")
    strategy_match, strategy_box = text_layer_spec(layer_map, "strategy")

    return {
        "top_intro": build_native_text_block(
            "top_intro",
            top_intro_match,
            top_intro_segments,
            top_intro_box,
            36,
            56,
            "medium",
        ),
        "market_sentence": build_native_text_block(
            "market_sentence",
            market_sentence_match,
            rich["market_sentence"],
            market_sentence_box,
            34,
            48,
            "medium",
        ),
        "funding": build_native_text_block(
            "funding",
            funding_match,
            split_rich_text(numbered_funding(fields["funding"]), field_rules["funding"]),
            funding_box,
            36,
            54,
            "medium",
        ),
        "fund_chart_title": build_native_text_block(
            "fund_chart_title",
            fund_chart_title_match,
            rich["fund_chart_title"],
            fund_chart_title_box,
            30,
            40,
            "medium",
        ),
        "risk_preference": build_native_text_block(
            "risk_preference",
            risk_preference_match,
            split_rich_text(risk_preference_text, field_rules["risk_preference"]),
            risk_preference_box,
            36,
            54,
            "medium",
        ),
        "outlook": build_native_text_block(
            "outlook",
            outlook_match,
            rich["outlook"],
            outlook_box,
            34,
            52,
            "medium",
        ),
        "strategy": build_native_text_block(
            "strategy",
            strategy_match,
            rich["strategy"],
            strategy_box,
            36,
            56,
            "medium",
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare native_v3 Photoshop content JSON.")
    parser.add_argument("--variant", choices=("原版", "固收+", "债市"), default="原版")
    parser.add_argument("--content-json", type=Path)
    parser.add_argument("--display-date")
    parser.add_argument("--source-date")
    return parser.parse_args(argv)


def psd_content_json_path(variant: str, explicit_path: Path | None) -> Path:
    if explicit_path is not None:
        return explicit_path
    return WEEK_WORK_DIR / "psd_content" / f"{variant}.json"


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    sys.path.insert(0, str(ROOT / "scripts"))
    import extract_word_psd_content
    import prepare_basic_v0_assets

    prepare_basic_v0_assets.main()
    extract_word_psd_content.main()

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    psd_content_json = psd_content_json_path(args.variant, args.content_json)
    content = json.loads(psd_content_json.read_text(encoding="utf-8"))
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    layer_map = json.loads(LAYER_MAP_PATH.read_text(encoding="utf-8"))
    fields = content["fields"]
    meta = content["meta"]
    canvas = layer_map["canvas"]
    layout_adjustments = layer_map.get("layout_adjustments", {})
    output_stem = f"金葵花债市周观察20260521_{args.variant}_原生文本v3"
    display_date = args.display_date or meta["date"]
    source = replace_source_date(fields["source"], args.source_date)

    data = {
        "variant": args.variant,
        "original_psd": str(PSD),
        "output_psd": str(OUT_DIR / f"{output_stem}.psd"),
        "output_png": str(OUT_DIR / f"{output_stem}.png"),
        "x0": canvas["x0"],
        "width": canvas["width"],
        "height": layout_adjustments.get("output_height", canvas["height"]),
        "date": display_date,
        "top_title": fields["top_title"],
        "source_risk": f"{source}\n{fields['risk_warning']}",
        "psd_content_json": str(psd_content_json),
        "psd_layer_map": str(LAYER_MAP_PATH),
        "layer_map": layer_map,
        "layout_adjustments": layout_adjustments,
        "layout_policy": "preserve_original_psd_components_then_replace_mapped_content",
        "assets": {
            "table": str(WEEK_WORK_DIR / "basic_v0" / "assets" / "yield_table.png"),
            "yield_chart": str(WEEK_WORK_DIR / "basic_v0" / "assets" / "yield_chart.png"),
            "fund_chart": str(WEEK_WORK_DIR / "basic_v0" / "assets" / "fund_chart.png"),
        },
        "native_text_blocks": build_text_blocks(content, rules, layer_map),
        "notes": [
            "v3 keeps rich paragraphs as editable Photoshop text layers.",
            "Each rich paragraph is a single Photoshop paragraph text layer with textStyleRange color spans.",
            "Table and chart replacements remain image layers.",
            "Original PSD visual components are preserved; mapped content layers are replaced in place.",
        ],
    }

    out = WORK_DIR / "content.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    print(data["output_png"])


if __name__ == "__main__":
    main()
