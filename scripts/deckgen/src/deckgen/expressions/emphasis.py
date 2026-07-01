"""emphasis: 1枚1メッセージの強調。
mode = big-number | kpi | message | quote。

data 契約: slide-expression/references/emphasis.md
"""

from __future__ import annotations

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from deckgen import layout


def render(pslide, theme, slide, region):
    data = slide.get("data") or {}
    mode = data.get("mode", "message")
    if mode == "big-number":
        _big_number(pslide, theme, data, region)
    elif mode == "kpi":
        _kpi(pslide, theme, data, region)
    elif mode == "quote":
        _quote(pslide, theme, data, region, slide)
    else:
        _message(pslide, theme, data, region, slide)


def _accent_card(pslide, theme, region):
    """アクセント色のグラデーションカード（GenSpark 水準の depth 表現）。"""
    left, top, width, height = region
    card = layout.add_box_shape(
        pslide, left, top, width, height, fill=theme["accent"], line=None,
    )
    # accent → accent2 のグラデーションで奥行き感を演出
    accent2 = theme.get("accent2", theme["accent"])
    try:
        layout.add_gradient_fill(card, theme["accent"], accent2, angle=135.0)
    except Exception:
        pass  # グラデーション未対応環境では solid fill にフォールバック
    return card


def _big_number(pslide, theme, data, region):
    left, top, width, height = region
    _accent_card(pslide, theme, region)
    value = str(data.get("value", ""))
    unit = str(data.get("unit", ""))
    label = str(data.get("label", ""))
    box = pslide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _run(p, value, layout.FONT_HERO, theme["on_accent"], True)
    if unit:
        _run(p, unit, layout.FONT_H1, theme["on_accent"], True)
    if label:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        _run(p2, label, layout.FONT_LEAD, theme["on_accent"], False)


def _message(pslide, theme, data, region, slide):
    left, top, width, height = region
    _accent_card(pslide, theme, region)
    text = str(data.get("text") or slide.get("summary") or "")
    box = pslide.shapes.add_textbox(
        left + Inches(0.6), top, width - Inches(1.2), height
    )
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _run(p, text, layout.FONT_H1, theme["on_accent"], True)


def _quote(pslide, theme, data, region, slide):
    left, top, width, height = region
    _accent_card(pslide, theme, region)
    text = str(data.get("text") or slide.get("summary") or "")
    cite = str(data.get("cite", ""))
    box = pslide.shapes.add_textbox(
        left + Inches(0.6), top, width - Inches(1.2), height
    )
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _run(p, f"“{text}”", layout.FONT_H2, theme["on_accent"], True)
    if cite:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        _run(p2, cite, layout.FONT_LEAD, theme["on_accent"], False)


def _kpi(pslide, theme, data, region):
    left, top, width, height = region
    cards = data.get("cards") or []
    if not cards:
        return
    n = len(cards)
    gap = layout.SPACE_3
    card_w = (width - gap * (n - 1)) // n
    card_h = min(Inches(2.6), height)
    card_top = top + (height - card_h) // 2
    for i, card in enumerate(cards):
        x = left + i * (card_w + gap)
        box = layout.add_box_shape(
            pslide, x, card_top, card_w, card_h,
            fill=theme["card"], line=theme["line"], line_width=1.0,
        )
        tf = box.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        _run(p, str(card.get("num", "")), layout.FONT_DISPLAY, theme["accent"], True)
        delta = str(card.get("delta", ""))
        if delta:
            _run(p, f" {delta}", layout.FONT_LEAD, theme["good"], True)
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        _run(p2, str(card.get("label", "")), layout.FONT_BODY, theme["fg"], False)


def _run(p, text, size, color, bold):
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.name = layout.FONT
    r.font.color.rgb = layout.rgb(color)
