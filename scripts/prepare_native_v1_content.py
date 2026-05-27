from __future__ import annotations

import json
import sys

from project_paths import OUTPUT_DIR, PSD_TEMPLATE, ROOT, WORK_DIR as WEEK_WORK_DIR


PSD = PSD_TEMPLATE
WORK_DIR = WEEK_WORK_DIR / "native_v1"
OUT_DIR = OUTPUT_DIR / "native_v1"
PSD_CONTENT_JSON = WEEK_WORK_DIR / "psd_content" / "原版.json"


def numbered_funding(text: str) -> str:
    first = "央行在公开市场操作上净投放1490亿元。"
    if text.startswith(first):
        return text.replace(first, f"1、{first}\n2、", 1)
    return f"1、{text}"


def numbered_risk_preference(text: str) -> str:
    text = text.replace("权益方面，", "1、权益方面，", 1)
    text = text.replace("商品方面，", "\n2、商品方面，", 1)
    return text


def main() -> None:
    # Reuse the generated table/chart assets from the basic pipeline.
    sys.path.insert(0, str(ROOT / "scripts"))
    import prepare_basic_v0_assets
    import extract_word_psd_content

    prepare_basic_v0_assets.main()
    extract_word_psd_content.main()

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    content = json.loads(PSD_CONTENT_JSON.read_text(encoding="utf-8"))
    fields = content["fields"]
    meta = content["meta"]

    data = {
        "original_psd": str(PSD),
        "output_psd": str(OUT_DIR / "金葵花债市周观察20260521_原生组件v1.psd"),
        "output_png": str(OUT_DIR / "金葵花债市周观察20260521_原生组件v1.png"),
        "x0": 3042,
        "width": 1125,
        "height": 7037,
        "date": meta["date"],
        "top_title": fields["top_title"],
        "intro": fields["top_intro"],
        "performance_sentence": fields["market_sentence"],
        "funding": numbered_funding(fields["funding"]),
        "fund_chart_title": fields["fund_chart_title"],
        "risk_preference": numbered_risk_preference(fields["risk_preference"]),
        "outlook": fields["outlook"],
        "strategy": fields["strategy"],
        "source_risk": f"{fields['source']}\n{fields['risk_warning']}",
        "psd_content_json": str(PSD_CONTENT_JSON),
        "rich_text": content["rich_text"],
        "assets": {
            "table": str(WEEK_WORK_DIR / "basic_v0" / "assets" / "yield_table.png"),
            "yield_chart": str(WEEK_WORK_DIR / "basic_v0" / "assets" / "yield_chart.png"),
            "fund_chart": str(WEEK_WORK_DIR / "basic_v0" / "assets" / "fund_chart.png"),
        },
        "notes": [
            "v1 keeps original PSD cards, title bars, icons, filters, and shadows.",
            "Text layers are replaced in place, so rich red emphasis may need a later style pass.",
            "Table/chart layers are image replacements fitted to original PSD bounds.",
        ],
    }

    out = WORK_DIR / "content.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    print(data["output_png"])


if __name__ == "__main__":
    main()
