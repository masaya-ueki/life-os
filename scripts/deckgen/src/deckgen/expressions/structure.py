"""structure: 関係・分類・位置づけ。
type = matrix-2x2 | tree | pyramid | matrix-table | venn。
venn は簡略化のため tree 同様の箇条書きにフォールバック。

data 契約: slide-expression/references/structure.md
"""

from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from deckgen import layout


def render(pslide, theme, slide, region):
    data = slide.get("data") or {}
    t = data.get("type", "tree")
    if t == "matrix-2x2":
        _matrix_2x2(pslide, theme, data, region)
    elif t == "pyramid":
        _pyramid(pslide, theme, data, region)
    elif t == "matrix-table":
        _matrix_table(pslide, theme, data, region)
    else:  # tree / venn / その他
        _tree(pslide, theme, data, region)


def _centered_text(shape, text, size, color):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = True
    run.font.name = "Yu Gothic"
    run.font.color.rgb = layout.rgb(color)


def _matrix_2x2(pslide, theme, data, region):
    left, top, width, height = region
    axis_x = str(data.get("axis_x", ""))
    axis_y = str(data.get("axis_y", ""))
    quad = [str(q) for q in (data.get("quadrants") or [])]
    quad += [""] * (4 - len(quad))

    # 軸ラベル用に外周マージンを確保
    pad_l = Inches(0.5)
    pad_b = Inches(0.4)
    grid_left = left + pad_l
    grid_w = width - pad_l
    grid_h = height - pad_b
    cell_w = grid_w // 2
    cell_h = grid_h // 2
    # 配置順: 左上→右上→左下→右下。右上(0,1)=最優先を accent で強調。
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for idx, (rr, cc) in enumerate(positions):
        x = grid_left + cc * cell_w
        y = top + rr * cell_h
        fill = theme["accent"] if (rr == 0 and cc == 1) else theme["card"]
        color = theme["on_accent"] if (rr == 0 and cc == 1) else theme["fg"]
        box = layout.add_box_shape(
            pslide, x + Inches(0.05), y + Inches(0.05),
            cell_w - Inches(0.1), cell_h - Inches(0.1),
            fill=fill, line=theme["line"], line_width=1.0,
            shape=MSO_SHAPE.RECTANGLE,
        )
        _centered_text(box, quad[idx], 16, color)
    # 軸ラベル: X は下中央、Y は左縦
    if axis_x:
        layout.add_textbox(
            pslide, grid_left, top + grid_h + Inches(0.02), grid_w, pad_b,
            f"→ {axis_x}", size=14, color=theme["muted"], bold=True,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
        )
    if axis_y:
        layout.add_textbox(
            pslide, left - Inches(0.05), top, pad_l + Inches(0.05), grid_h,
            f"↑ {axis_y}", size=14, color=theme["muted"], bold=True,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, wrap=True,
        )


def _tree(pslide, theme, data, region):
    left, top, width, height = region
    root = data.get("root")
    children = data.get("children") or []
    items = []
    if root:
        items.append((str(root), 0))
    _walk(children, 1, items)
    if not items:
        return
    layout.add_bullets(
        pslide, left, top, width, height, items,
        size=20, color=theme["fg"], bullet="", line_spacing=1.3, space_after=8,
    )


def _walk(nodes, level, out):
    for node in nodes:
        if isinstance(node, dict):
            name = node.get("name", "")
            mark = "▸ " if level == 1 else "・"
            out.append((f"{mark}{name}", level))
            _walk(node.get("children") or [], level + 1, out)
        else:
            out.append((f"・{node}", level))


def _pyramid(pslide, theme, data, region):
    left, top, width, height = region
    layers = [str(x) for x in (data.get("layers") or [])]
    if not layers:
        return
    n = len(layers)
    gap = Inches(0.12)
    row_h = (height - gap * (n - 1)) // n
    # 頂点(最後)が狭く、土台(最初)が広い。layers[0]=土台 を最下段に。
    for i, layer in enumerate(reversed(layers)):
        # i=0 が頂点(最上段・最狭)
        frac = (i + 1) / n
        w = int(width * frac)
        x = left + (width - w) // 2
        y = top + i * (row_h + gap)
        shade = [theme["accent"], theme["accent2"], theme["muted"], theme["line"]]
        fill = shade[i % len(shade)]
        shape = MSO_SHAPE.TRAPEZOID if i == 0 else MSO_SHAPE.RECTANGLE
        box = layout.add_box_shape(
            pslide, x, y, w, row_h, fill=fill, line=None, shape=shape,
        )
        _centered_text(box, layer, 16, theme["on_accent"])


def _matrix_table(pslide, theme, data, region):
    # rows/cols が無い汎用分類表は tree フォールバックで十分
    _tree(pslide, theme, data, region)
