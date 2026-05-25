from __future__ import annotations

import math
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document


ROOT = Path("/Users/a123/Downloads/债市周观察/债市周观察")
DOCX = ROOT / "金葵花债市周度复盘20260521 - 修改版本.docx"
BASE_DIR = ROOT / "长图"
OUT_DIR = BASE_DIR / "20260521新版"

FONT_HEITI = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"

BLACK = (24, 22, 20)
RED = (232, 31, 31)
GREEN = (0, 172, 96)
CREAM = (255, 248, 235)
CREAM2 = (255, 251, 243)
WHITE = (255, 255, 255)
GOLD = (214, 155, 71)
LIGHT_GOLD = (248, 215, 169)
GRID = (218, 218, 218)
GREY = (110, 110, 110)


def font(size: int, bold: bool = True, song: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_SONG if song else FONT_HEITI, size)


def text_width(draw: ImageDraw.ImageDraw, text: str, ft: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(text, font=ft)


def fill_rect(draw: ImageDraw.ImageDraw, box, color):
    draw.rectangle(box, fill=color)


def rich_lines(draw: ImageDraw.ImageDraw, segments, ft, max_width):
    lines = []
    line = []
    width = 0
    for text, color in segments:
        for ch in text:
            if ch == "\n":
                lines.append(line)
                line = []
                width = 0
                continue
            w = text_width(draw, ch, ft)
            if line and width + w > max_width:
                lines.append(line)
                line = []
                width = 0
            line.append((ch, color))
            width += w
    if line:
        lines.append(line)
    return lines


def draw_rich_text(
    draw: ImageDraw.ImageDraw,
    xy,
    segments,
    ft,
    max_width: int,
    line_height: int,
    align: str = "left",
):
    x, y = xy
    for line in rich_lines(draw, segments, ft, max_width):
        line_text = "".join(ch for ch, _ in line)
        w = text_width(draw, line_text, ft)
        cx = x
        if align == "center":
            cx = x + (max_width - w) / 2
        for ch, color in line:
            draw.text((cx, y), ch, font=ft, fill=color)
            cx += text_width(draw, ch, ft)
        y += line_height
    return y


def draw_plain_center(draw, box, text, ft, fill=BLACK):
    x1, y1, x2, y2 = box
    bbox = draw.textbbox((0, 0), text, font=ft)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((x1 + (x2 - x1 - w) / 2, y1 + (y2 - y1 - h) / 2 - 2), text, font=ft, fill=fill)


def parse_docx_tables():
    doc = Document(DOCX)
    table = doc.tables[0]
    return [[cell.text.strip() for cell in row.cells] for row in table.rows]


def excel_date(n: str) -> datetime:
    return datetime(1899, 12, 30) + timedelta(days=float(n))


def parse_chart(chart_name: str):
    ns = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
    with zipfile.ZipFile(DOCX) as z:
        root = ET.fromstring(z.read(f"word/charts/{chart_name}"))
    series = []
    for ser in root.findall(".//c:ser", ns):
        tx = ser.find(".//c:tx//c:v", ns)
        name = tx.text if tx is not None else "series"
        cats = [pt.find("c:v", ns).text for pt in ser.findall(".//c:cat//c:pt", ns)]
        vals = [float(pt.find("c:v", ns).text) for pt in ser.findall(".//c:val//c:pt", ns)]
        pairs = [(excel_date(c), v) for c, v in zip(cats, vals)]
        pairs = [(d, v) for d, v in pairs if d.date() <= datetime(2026, 5, 21).date()]
        pairs.sort(key=lambda x: x[0])
        series.append((name, pairs))
    return series


TABLE_ROWS = parse_docx_tables()
YIELD_SERIES = parse_chart("chart1.xml")
FUND_SERIES = parse_chart("chart2.xml")


def fmt_date_short(s: str) -> str:
    if re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}$", s):
        d = datetime.strptime(s.replace("/", "-"), "%Y-%m-%d")
        return f"{d.year}/{d.month}/{d.day}"
    return s


def draw_table(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, rows):
    cols = len(rows[0])
    col_widths = [210] + [(w - 210) // (cols - 1)] * (cols - 1)
    col_widths[-1] = w - sum(col_widths[:-1])
    row_h = h // len(rows)
    f_header = font(24)
    f_body = font(23)
    cx = x
    for c in range(cols):
        cy = y
        for r in range(len(rows)):
            box = (cx, cy, cx + col_widths[c], cy + row_h)
            fill = (244, 241, 235) if r == 0 else (255, 251, 245)
            draw.rectangle(box, fill=fill, outline=(64, 64, 64), width=2)
            txt = rows[r][c]
            if c == 0 and r in (1, 2):
                txt = fmt_date_short(txt)
            color = BLACK
            if r == 3 and c > 0:
                try:
                    color = GREEN if float(txt) < 0 else RED
                except ValueError:
                    color = BLACK
            ft = f_header if r == 0 or c == 0 else f_body
            draw_plain_center(draw, box, txt, ft, color)
            cy += row_h
        cx += col_widths[c]


def draw_line_chart(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    series,
    y_min: float,
    y_max: float,
    ticks,
    colors,
    legend_cols: int = 3,
    rotate_dates: bool = True,
    show_date_labels: bool = False,
):
    left, top, right, bottom = x + 70, y + 20, x + w - 35, y + h - 90
    f_axis = font(17)
    f_legend = font(15)
    draw.line((left, top, left, bottom), fill=(190, 190, 190), width=2)
    draw.line((left, bottom, right, bottom), fill=(190, 190, 190), width=2)
    for tick in ticks:
        yy = bottom - (tick - y_min) / (y_max - y_min) * (bottom - top)
        draw.line((left, yy, right, yy), fill=GRID, width=1)
        draw.text((x + 8, yy - 11), f"{tick:.2f}", font=f_axis, fill=GREY)
    all_dates = sorted({d for _, pairs in series for d, _ in pairs})
    if not all_dates:
        return
    start, end = all_dates[0], all_dates[-1]
    span = max((end - start).days, 1)
    for idx in range(0, len(all_dates), max(1, len(all_dates) // 9)):
        d = all_dates[idx]
        xx = left + (d - start).days / span * (right - left)
        draw.line((xx, bottom, xx, bottom + 8), fill=(205, 205, 205), width=2)
        if not show_date_labels:
            continue
        label = d.strftime("%Y-%m-%d")
        if rotate_dates:
            tmp = Image.new("RGBA", (160, 28), (0, 0, 0, 0))
            td = ImageDraw.Draw(tmp)
            td.text((0, 0), label, font=f_axis, fill=GREY)
            tmp = tmp.rotate(50, expand=True)
            draw._image.alpha_composite(tmp, dest=(int(xx - 55), int(bottom + 8)))
        else:
            draw.text((xx - 34, bottom + 10), label[5:], font=f_axis, fill=GREY)
    for idx, (name, pairs) in enumerate(series):
        pts = []
        for d, val in pairs:
            xx = left + (d - start).days / span * (right - left)
            yy = bottom - (val - y_min) / (y_max - y_min) * (bottom - top)
            pts.append((xx, yy))
        if len(pts) > 1:
            draw.line(pts, fill=colors[idx % len(colors)], width=4, joint="curve")
    legend_y = y + h - 48
    col_w = w // legend_cols
    for idx, (name, _) in enumerate(series):
        lx = x + 55 + (idx % legend_cols) * col_w
        ly = legend_y + (idx // legend_cols) * 30
        label = name.replace("中债国债到期收益率:", "中债国债到期收益率:")
        label = label.replace("存款类机构质押式回购加权利率:", "回购加权利率:")
        draw.line((lx, ly + 10, lx + 42, ly + 10), fill=colors[idx % len(colors)], width=4)
        draw.text((lx + 50, ly), label, font=f_legend, fill=GREY)


def draw_small_fund_chart(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
    draw_line_chart(
        draw,
        x,
        y,
        w,
        h,
        FUND_SERIES,
        1.20,
        1.40,
        [1.20, 1.22, 1.24, 1.26, 1.28, 1.30, 1.32, 1.34, 1.36, 1.38, 1.40],
        [(86, 160, 220), (239, 125, 45)],
        legend_cols=1,
        rotate_dates=True,
    )


TOP_TEXT = {
    "原版": [
        ("上周债券", BLACK),
        ("收益率整体下行约2BP", RED),
        ("。资金利率小幅上行，央行", BLACK),
        ("净投放呵护月末资金面", RED),
        ("，经济数据整体稳定。", BLACK),
        ("期限上看，1年、5-30年国债下行更明显", RED),
        ("。近期债市仍受资金和配置力量支撑，但长端波动可能加大。建议控制风险，关注收益率阶段性上行后的", BLACK),
        ("配置机会", RED),
        ("。", BLACK),
    ],
    "固收+": [
        ("上周债券", BLACK),
        ("收益率整体下行约2BP", RED),
        ("。资金利率小幅上行，央行", BLACK),
        ("净投放呵护月末资金面", RED),
        ("，经济数据整体稳定。权益高位回落后企稳，商品价格分化。", BLACK),
        ("预计国内流动性仍将维持相对充裕", RED),
        ("，有利于", BLACK),
        ("股债偏强共振，固收+策略的配置价值仍在", RED),
        ("。可适时关注含权益资产的", BLACK),
        ("固收+产品", RED),
        ("，具体详情见下文。", BLACK),
    ],
    "债": [
        ("上周债券", BLACK),
        ("收益率整体下行约2BP", RED),
        ("。资金利率小幅上行，央行", BLACK),
        ("净投放呵护月末资金面", RED),
        ("，经济数据整体稳定。期限上看，1年、5-30年国债下行更明显，", BLACK),
        ("债市多头趋势仍在", RED),
        ("，但", BLACK),
        ("超长端波动可能加大", RED),
        ("。建议", BLACK),
        ("继续持有纯债产品", RED),
        ("，并关注收益率阶段性上行后的配置机会。", BLACK),
    ],
}


def section_offsets(name: str) -> int:
    return {"原版": 0, "固收+": 254, "债": 166}[name]


def draw_date(draw: ImageDraw.ImageDraw):
    # Small dark patch only behind the old date.
    fill_rect(draw, (455, 342, 680, 410), (86, 72, 55))
    draw.text((466, 342), "2026-5-21", font=font(38, song=True), fill=(255, 221, 172))


def draw_top_card(draw: ImageDraw.ImageDraw, variant: str, second_header_y: int):
    fill_rect(draw, (75, 552, 1045, 690), WHITE)
    draw.text((92, 575), "国债收益率整体下行", font=font(50), fill=BLACK)
    body_top = 1235
    body_bottom = second_header_y - 85
    fill_rect(draw, (86, body_top - 8, 1040, body_bottom), CREAM2)
    size = 40 if variant != "原版" else 39
    line_height = 66 if variant != "原版" else 64
    while size >= 31:
        ft = font(size)
        lines = rich_lines(draw, TOP_TEXT[variant], ft, 944)
        if len(lines) * line_height <= body_bottom - body_top:
            break
        size -= 1
        line_height = max(52, line_height - 2)
    draw_rich_text(draw, (88, body_top), TOP_TEXT[variant], font(size), 944, line_height)


def draw_market_section(draw: ImageDraw.ImageDraw, dy: int):
    y0 = 1981 + dy
    fill_rect(draw, (48, y0 + 105, 1075, y0 + 1360), CREAM)
    draw_rich_text(
        draw,
        (76, y0 + 128),
        [("5月15日-5月21日，", BLACK), ("国债收益率全期限下行。", RED)],
        font(35),
        980,
        52,
    )

    px, py, pw, ph = 88, y0 + 235, 950, 1070
    draw.rounded_rectangle((px, py, px + pw, py + ph), radius=12, fill=(255, 252, 248), outline=GOLD, width=2)
    draw_plain_center(draw, (px, py + 25, px + pw, py + 75), "不同期限国债收益率（上两周数据对比）", font(34), BLACK)
    draw_table(draw, px + 44, py + 115, pw - 88, 185, TABLE_ROWS)
    draw_plain_center(draw, (px, py + 355, px + pw, py + 415), "国债收益率曲线（近一年）", font(33), BLACK)
    draw_line_chart(
        draw,
        px + 40,
        py + 455,
        pw - 80,
        540,
        YIELD_SERIES,
        0.80,
        2.80,
        [0.80, 1.30, 1.80, 2.30, 2.80],
        [(86, 160, 220), (232, 122, 55), (165, 169, 170), (245, 180, 0), (68, 112, 196), (105, 168, 80)],
        legend_cols=3,
    )


def draw_analysis_section(draw: ImageDraw.ImageDraw, dy: int):
    y0 = 3364 + dy
    # Cover old right-side copy and old chart while preserving the left icons.
    fill_rect(draw, (337, y0 + 235, 1025, y0 + 635), (255, 251, 246))
    draw_rich_text(
        draw,
        (356, y0 + 250),
        [
            ("1、央行在公开市场操作上", BLACK),
            ("净投放1490亿元。\n", RED),
            ("2、", BLACK),
            ("资金利率上行", RED),
            ("。DR007收1.3280%；1年期国股行存单发行利率上行至1.445%。", BLACK),
        ],
        font(30),
        630,
        48,
    )
    fill_rect(draw, (150, y0 + 625, 960, y0 + 1250), (255, 251, 246))
    draw_plain_center(draw, (175, y0 + 650, 935, y0 + 700), "DR001/DR007上周情况:", font(31), (70, 70, 70))
    draw_plain_center(draw, (175, y0 + 695, 935, y0 + 740), "资金利率上行", font(31), RED)
    draw_small_fund_chart(draw, 170, y0 + 760, 770, 430)

    fill_rect(draw, (337, y0 + 1370, 1025, y0 + 1725), (255, 251, 246))
    draw_rich_text(
        draw,
        (356, y0 + 1380),
        [
            ("1、权益高位回落后企稳，", BLACK),
            ("主力资金仍有兑现意愿", RED),
            ("。\n2、油价回落，黄金反弹有限；风险偏好边际变化对长端定价仍有影响。", BLACK),
        ],
        font(30),
        630,
        50,
    )


def draw_outlook(draw: ImageDraw.ImageDraw, dy: int):
    y0 = 5241 + dy
    fill_rect(draw, (62, y0 + 105, 1060, y0 + 510), CREAM2)
    draw_rich_text(
        draw,
        (88, y0 + 132),
        [
            ("展望后市，当前银行间资金利率上行符合季节性规律，不改", BLACK),
            ("资金面宽松的基本格局", RED),
            ("。", BLACK),
            ("债市多头趋势延续", RED),
            ("，且仍有较多机构存在欠配压力。建议在控制风险的前提下，把握收益率可能出现的阶段性上行机会，", BLACK),
            ("逢高配置", RED),
            ("。", BLACK),
        ],
        font(33),
        930,
        54,
    )


def draw_source(draw: ImageDraw.ImageDraw, dy: int):
    y0 = 6388 + dy
    fill_rect(draw, (20, y0 - 20, 700, y0 + 45), (33, 25, 22))
    draw.text((29, y0 - 5), "数据来源：wind，截至2026年5月21日", font=font(25), fill=(120, 120, 120))


def build_variant(name: str):
    base = Image.open(BASE_DIR / f"{name}.png").convert("RGBA")
    draw = ImageDraw.Draw(base)
    dy = section_offsets(name)
    second_header_y = 1981 + dy
    draw_date(draw)
    draw_top_card(draw, name, second_header_y)
    draw_market_section(draw, dy)
    draw_analysis_section(draw, dy)
    draw_outlook(draw, dy)
    draw_source(draw, dy)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"金葵花债市周观察20260521_{name}.png"
    base.save(out)
    return out


def main():
    outputs = [build_variant(name) for name in ["原版", "固收+", "债"]]
    for p in outputs:
        print(p)


if __name__ == "__main__":
    main()
