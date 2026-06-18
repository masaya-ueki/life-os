"""スライド組み立ての共通ヘルパ（寸法・色・テキストボックス・図形）。

base.css.md の設計値（16:9・本文≥24px相当・見出し・配色トークン）を
pptx のネイティブ要素に写像する。すべて編集可能な要素として生成する。
"""

from __future__ import annotations

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from deckgen.theme import FONT

# --- スライド寸法（16:9 ワイド） ---
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# --- 余白とリージョン ---
MARGIN = Inches(0.6)
CONTENT_LEFT = MARGIN
CONTENT_WIDTH = SLIDE_W - 2 * MARGIN

TITLE_TOP = Inches(0.4)
TITLE_HEIGHT = Inches(0.95)
LEAD_TOP = Inches(1.4)
LEAD_HEIGHT = Inches(0.75)
BODY_TOP = Inches(2.35)
BODY_BOTTOM_MARGIN = Inches(0.45)
BODY_HEIGHT = SLIDE_H - BODY_TOP - BODY_BOTTOM_MARGIN

# Region = (left, top, width, height)（すべて EMU int）
Region = tuple


def rgb(hexcolor: str) -> RGBColor:
    return RGBColor.from_string(hexcolor)


def blank_layout(prs):
    """テンプレ非依存で使える Blank に近いレイアウトを返す。"""
    for layout in prs.slide_layouts:
        if layout.name.strip().lower() == "blank":
            return layout
    # 慣例上 index 6 が Blank。無ければ最後を使う。
    layouts = list(prs.slide_layouts)
    if len(layouts) > 6:
        return layouts[6]
    return layouts[-1]


def add_slide(prs):
    return prs.slides.add_slide(blank_layout(prs))


def fill_background(slide, hexcolor: str) -> None:
    """スライド全面に背景矩形を敷く（テンプレ無し時のテーマ背景）。"""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(hexcolor)
    shape.line.fill.background()
    shape.shadow.inherit = False
    # 背景は最背面へ
    sp = shape._element
    sp.getparent().remove(sp)
    slide.shapes._spTree.insert(2, sp)
    return shape


def add_textbox(
    slide,
    left,
    top,
    width,
    height,
    text="",
    *,
    size=24,
    color="1A1A2E",
    bold=False,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    font=FONT,
    wrap=True,
):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]
    p.alignment = align
    _style_run(p.add_run(), text, size, color, bold, font)
    return box


def _style_run(run, text, size, color, bold, font):
    run.text = text
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.name = font
    f.color.rgb = rgb(color)


def add_bullets(
    slide,
    left,
    top,
    width,
    height,
    items,
    *,
    size=22,
    color="1A1A2E",
    font=FONT,
    bullet="•  ",
    line_spacing=1.3,
    space_after=8,
):
    """箇条書きテキストフレーム。items は str か (text, level) のタプル列。"""
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            text, level = item
        else:
            text, level = item, 0
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = level
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        indent = "    " * level
        prefix = bullet if bullet else ""
        _style_run(p.add_run(), f"{indent}{prefix}{text}", size, color, False, font)
    return box


def add_box_shape(
    slide,
    left,
    top,
    width,
    height,
    *,
    fill="F8FAFC",
    line=None,
    line_width=1.0,
    shape=MSO_SHAPE.ROUNDED_RECTANGLE,
):
    sp = slide.shapes.add_shape(shape, left, top, width, height)
    sp.fill.solid()
    sp.fill.fore_color.rgb = rgb(fill)
    if line:
        sp.line.color.rgb = rgb(line)
        sp.line.width = Pt(line_width)
    else:
        sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def add_arrow(slide, left, top, width, height, color="6B7280"):
    sp = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, left, top, width, height)
    sp.fill.solid()
    sp.fill.fore_color.rgb = rgb(color)
    sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def add_down_arrow(slide, left, top, width, height, color="6B7280"):
    sp = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, left, top, width, height)
    sp.fill.solid()
    sp.fill.fore_color.rgb = rgb(color)
    sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def add_rule(slide, left, top, width, color, weight=2.5):
    """水平の罫線（タイトル下線など）。"""
    conn = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, left, top, left + width, top
    )
    conn.line.color.rgb = rgb(color)
    conn.line.width = Pt(weight)
    return conn


def style_cell(cell, text, *, size=18, color="1A1A2E", bold=False, fill=None,
               align=PP_ALIGN.LEFT, font=FONT):
    if fill is not None:
        cell.fill.solid()
        cell.fill.fore_color.rgb = rgb(fill)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.margin_left = Inches(0.1)
    cell.margin_right = Inches(0.1)
    cell.margin_top = Inches(0.04)
    cell.margin_bottom = Inches(0.04)
    tf = cell.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    _style_run(p.add_run(), text, size, color, bold, font)


def add_table(slide, left, top, width, height, rows, cols):
    gf = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = gf.table
    # python-pptx 既定のテーマ縞模様を抑える（テーマ色で塗るため）
    table.first_row = False
    table.horz_banding = False
    return table


def add_header(slide, theme, title, summary):
    """各コンテンツスライド共通の見出し（タイトル + 下線 + リード）を描き、
    本文用 Region (left, top, width, height) を返す。"""
    add_textbox(
        slide,
        CONTENT_LEFT,
        TITLE_TOP,
        CONTENT_WIDTH,
        TITLE_HEIGHT,
        title,
        size=32,
        color=theme["accent"],
        bold=True,
        anchor=MSO_ANCHOR.BOTTOM,
    )
    add_rule(
        slide,
        CONTENT_LEFT,
        TITLE_TOP + TITLE_HEIGHT,
        CONTENT_WIDTH,
        theme["line"],
        weight=2.5,
    )
    if summary:
        add_textbox(
            slide,
            CONTENT_LEFT,
            LEAD_TOP,
            CONTENT_WIDTH,
            LEAD_HEIGHT,
            summary,
            size=20,
            color=theme["fg"],
            bold=True,
        )
    return (CONTENT_LEFT, BODY_TOP, CONTENT_WIDTH, BODY_HEIGHT)
