"""title: 表紙の全面レイアウト（中央寄せ）。builder から個別に呼ばれる。"""

from __future__ import annotations

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from deckgen import layout


def render_cover(pslide, theme, deck, slide):
    title = slide.get("title") or deck.get("title", "")
    subtitle = slide.get("summary") or deck.get("subtitle", "")
    content = [str(x) for x in (slide.get("content") or [])]
    date = deck.get("date", "")

    # 左端アクセントバー（GenSpark 水準のビジュアルアンカー）
    layout.add_accent_bar(
        pslide, Inches(0), Inches(0), layout.SLIDE_H,
        theme["accent"], width=Inches(0.18),
    )
    # タイトル下部のアクセントライン（見た目の根拠を与える）
    layout.add_rule(
        pslide,
        Inches(1.0), Inches(4.05), layout.SLIDE_W - Inches(2.0),
        theme["accent"], weight=3.0,
    )

    # メインタイトル
    box = pslide.shapes.add_textbox(
        Inches(1.2), Inches(2.0), layout.SLIDE_W - Inches(2.0), Inches(2.0)
    )
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    _run(p, title, layout.FONT_DISPLAY, theme["accent"], True)

    if subtitle:
        sb = pslide.shapes.add_textbox(
            Inches(1.2), Inches(4.15), layout.SLIDE_W - Inches(2.0), Inches(1.0)
        )
        stf = sb.text_frame
        stf.word_wrap = True
        sp = stf.paragraphs[0]
        sp.alignment = PP_ALIGN.LEFT
        _run(sp, subtitle, layout.FONT_LEAD, theme["fg"], False)

    if content:
        cb = pslide.shapes.add_textbox(
            Inches(1.2), Inches(5.25), layout.SLIDE_W - Inches(2.5), Inches(1.5)
        )
        ctf = cb.text_frame
        ctf.word_wrap = True
        for i, line in enumerate(content):
            cp = ctf.paragraphs[0] if i == 0 else ctf.add_paragraph()
            cp.alignment = PP_ALIGN.LEFT
            cp.space_after = Pt(4)
            _run(cp, f"· {line}", layout.FONT_SMALL, theme["muted"], False)

    if date:
        db = pslide.shapes.add_textbox(
            Inches(1.2), layout.SLIDE_H - Inches(0.75),
            layout.SLIDE_W - Inches(2.0), Inches(0.45)
        )
        dp = db.text_frame.paragraphs[0]
        dp.alignment = PP_ALIGN.LEFT
        _run(dp, str(date), layout.FONT_CAPTION, theme["muted"], False)


def _run(p, text, size, color, bold):
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.name = layout.FONT
    r.font.color.rgb = layout.rgb(color)
