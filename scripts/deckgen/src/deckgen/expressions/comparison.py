"""comparison: 対比。mode = two-column | pros-cons | table。

data 契約: slide-expression/references/comparison.md
"""

from __future__ import annotations

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from deckgen import layout


def render(pslide, theme, slide, region):
    data = slide.get("data") or {}
    mode = data.get("mode", "two-column")
    if mode == "table":
        _table(pslide, theme, data, region)
    else:
        _two_column(pslide, theme, data, region, mode)


def _two_column(pslide, theme, data, region, mode):
    left, top, width, height = region
    pros_cons = mode == "pros-cons"
    gap = Inches(0.4)
    col_w = (width - gap) // 2
    note = data.get("note")
    note_h = Inches(0.5) if note else 0
    body_h = height - note_h

    cols = [
        ("left", data.get("left") or {}, theme["good"] if pros_cons else theme["muted"]),
        ("right", data.get("right") or {}, theme["bad"] if pros_cons else theme["accent"]),
    ]
    for i, (_key, col, head_color) in enumerate(cols):
        x = left + i * (col_w + gap)
        card = layout.add_box_shape(
            pslide, x, top, col_w, body_h,
            fill=theme["card"], line=theme["line"], line_width=1.0,
        )
        card.shadow.inherit = False
        # ラベル見出し
        layout.add_textbox(
            pslide, x + Inches(0.2), top + Inches(0.15),
            col_w - Inches(0.4), Inches(0.55),
            col.get("label", ""), size=22, color=head_color, bold=True,
        )
        # 項目
        items = [str(v) for v in (col.get("items") or [])]
        if items:
            layout.add_bullets(
                pslide, x + Inches(0.25), top + Inches(0.85),
                col_w - Inches(0.5), body_h - Inches(1.0), items,
                size=18, color=theme["fg"], line_spacing=1.25, space_after=6,
            )
    if note:
        layout.add_textbox(
            pslide, left, top + body_h + Inches(0.1), width, note_h,
            str(note), size=14, color=theme["muted"],
        )


def _table(pslide, theme, data, region):
    left, top, width, height = region
    axes = [str(a) for a in (data.get("axes") or [])]
    columns = data.get("columns") or []
    if not columns:
        return
    n_rows = 1 + len(axes)
    n_cols = 1 + len(columns)
    # 高さは行数に合わせて上詰め（最大 region 内）
    row_h = min(Inches(0.7), height // max(n_rows, 1))
    table_h = row_h * n_rows
    table = layout.add_table(pslide, left, top, width, table_h, n_rows, n_cols)

    # 1列目を細め、データ列を等幅に
    first_w = Inches(2.6)
    rest = (width - first_w) // len(columns)
    table.columns[0].width = first_w
    for c in range(1, n_cols):
        table.columns[c].width = rest

    # ヘッダ行: [空, 列名...]
    layout.style_cell(table.cell(0, 0), "", fill=theme["accent"])
    for c, col in enumerate(columns, start=1):
        layout.style_cell(
            table.cell(0, c), str(col.get("name", "")),
            size=18, color=theme["on_accent"], bold=True,
            fill=theme["accent"], align=PP_ALIGN.CENTER,
        )
    # 各評価軸の行
    for r, axis in enumerate(axes, start=1):
        zebra = theme["card"] if r % 2 == 1 else theme["bg"]
        layout.style_cell(
            table.cell(r, 0), axis, size=16, color=theme["fg"],
            bold=True, fill=theme["card"],
        )
        for c, col in enumerate(columns, start=1):
            vals = col.get("values") or []
            text = str(vals[r - 1]) if r - 1 < len(vals) else ""
            layout.style_cell(
                table.cell(r, c), text, size=16, color=theme["fg"],
                fill=zebra, align=PP_ALIGN.CENTER,
            )
