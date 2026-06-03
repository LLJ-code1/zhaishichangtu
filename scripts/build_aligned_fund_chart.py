from __future__ import annotations

from pathlib import Path

from prepare_basic_v0_assets import chart_name_for_series, parse_chart, save_line_chart
from project_paths import WORK_DIR


OUT_PATH = WORK_DIR / "native_v3/assets/fund_chart_aligned.png"


def build_chart(path: Path = OUT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fund_series = parse_chart(chart_name_for_series(("回购加权利率:1天", "回购加权利率:7天")))
    save_line_chart(
        path,
        fund_series,
        (862, 442),
        1.20,
        1.45,
        [1.20, 1.25, 1.30, 1.35, 1.40, 1.45],
        [(86, 160, 220), (239, 125, 45)],
        legend_cols=1,
        show_date_labels=True,
    )
    return path


if __name__ == "__main__":
    print(build_chart())
