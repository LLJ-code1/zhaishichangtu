from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from project_paths import EDITED_DOCX, WORK_DIR
from prepare_basic_v0_assets import chart_name_for_series


OUT_PATH = WORK_DIR / "native_v3/assets/fund_chart_word_style.png"
FONT_PATH = Path("/System/Library/Fonts/STHeiti Medium.ttc")


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def excel_date(value: str) -> datetime:
    return datetime(1899, 12, 30) + timedelta(days=float(value))


def parse_fund_series() -> list[tuple[str, list[tuple[datetime, float]]]]:
    ns = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
    chart_name = chart_name_for_series(("回购加权利率:1天", "回购加权利率:7天"))
    with zipfile.ZipFile(EDITED_DOCX) as zf:
        root = ET.fromstring(zf.read(f"word/charts/{chart_name}"))

    series: list[tuple[str, list[tuple[datetime, float]]]] = []
    for ser in root.findall(".//c:ser", ns):
        tx = ser.find(".//c:tx//c:v", ns)
        name = tx.text if tx is not None and tx.text else "series"
        cats = [pt.find("c:v", ns).text for pt in ser.findall(".//c:cat//c:pt", ns)]
        vals = [float(pt.find("c:v", ns).text) for pt in ser.findall(".//c:val//c:pt", ns)]
        pairs = sorted((excel_date(cat), val) for cat, val in zip(cats, vals))
        series.append((name, pairs))
    return series


def draw_center(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, ft, fill) -> None:
    left, top, right, bottom = box
    bbox = draw.textbbox((0, 0), text, font=ft)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    draw.text(
        (left + (right - left - width) / 2, top + (bottom - top - height) / 2 - 2),
        text,
        font=ft,
        fill=fill,
    )


def draw_rotated_label(base: Image.Image, xy: tuple[float, float], text: str, ft, fill) -> None:
    bbox = ft.getbbox(text)
    label = Image.new("RGBA", (bbox[2] - bbox[0] + 12, bbox[3] - bbox[1] + 12), (0, 0, 0, 0))
    label_draw = ImageDraw.Draw(label)
    label_draw.text((6 - bbox[0], 6 - bbox[1]), text, font=ft, fill=fill)
    rotated = label.rotate(45, expand=True, resample=Image.Resampling.BICUBIC)
    x, y = xy
    base.alpha_composite(rotated, (round(x - rotated.width / 2), round(y)))


def short_label(name: str) -> str:
    return name.replace("存款类机构质押式回购加权利率:", "存款类机构质押式回购加权利率:")


def build_chart(path: Path = OUT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    series = parse_fund_series()
    width, height = 779, 568
    image = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)

    grey = (90, 90, 90, 255)
    grid = (205, 205, 205, 255)
    border = (210, 210, 210, 255)
    blue = (99, 150, 210, 255)
    orange = (224, 125, 55, 255)

    draw.rectangle((0, 0, width - 1, height - 1), outline=border, width=2)
    draw_center(draw, (0, 16, width, 78), "图7： DR001/DR007本周情况", font(32), grey)

    left, top, right, bottom = 88, 95, width - 76, 332
    y_min, y_max = 1.20, 1.45
    ticks = [1.20, 1.25, 1.30, 1.35, 1.40, 1.45]
    all_series_dates = sorted({item[0] for _, pairs in series for item in pairs})
    start, end = all_series_dates[0], all_series_dates[-1]
    all_dates = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
    span = max((end - start).days, 1)

    for tick in ticks:
        yy = bottom - (tick - y_min) / (y_max - y_min) * (bottom - top)
        draw.line((left, yy, right, yy), fill=grid, width=1)
        draw.text((18, yy - 14), f"{tick:.2f}", font=font(20), fill=grey)

    draw.line((left, bottom, right, bottom), fill=grid, width=2)
    for d in all_dates:
        xx = left + (d - start).days / span * (right - left)
        draw.line((xx, bottom, xx, bottom + 8), fill=grid, width=2)
        draw_rotated_label(image, (xx, bottom + 10), d.strftime("%Y-%m-%d"), font(19), grey)

    for idx, (_, pairs) in enumerate(series):
        points = []
        for d, value in pairs:
            xx = left + (d - start).days / span * (right - left)
            yy = bottom - (value - y_min) / (y_max - y_min) * (bottom - top)
            points.append((xx, yy))
        draw.line(points, fill=[blue, orange][idx], width=5, joint="curve")

    legend_x = 210
    legend_y = 470
    for idx, (name, _) in enumerate(series):
        y = legend_y + idx * 42
        color = [blue, orange][idx]
        draw.line((legend_x, y + 14, legend_x + 52, y + 14), fill=color, width=5)
        draw.text((legend_x + 58, y), short_label(name), font=font(23), fill=grey)

    image.save(path)
    return path


if __name__ == "__main__":
    print(build_chart())
