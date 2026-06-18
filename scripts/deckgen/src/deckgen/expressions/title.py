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

    # メインタイトル
    box = pslide.shapes.add_textbox(
        Inches(1.0), Inches(2.3), layout.SLIDE_W - Inches(2.0), Inches(1.8)
    )
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _run(p, title, 48, theme["accent"], True)

    if subtitle:
        sb = pslide.shapes.add_textbox(
            Inches(1.0), Inches(4.1), layout.SLIDE_W - Inches(2.0), Inches(0.9)
        )
        stf = sb.text_frame
        stf.word_wrap = True
        sp = stf.paragraphs[0]
        sp.alignment = PP_ALIGN.CENTER
        _run(sp, subtitle, 24, theme["fg"], False)

    if content:
        cb = pslide.shapes.add_textbox(
            Inches(1.5), Inches(5.1), layout.SLIDE_W - Inches(3.0), Inches(1.6)
        )
        ctf = cb.text_frame
        ctf.word_wrap = True
        for i, line in enumerate(content):
            cp = ctf.paragraphs[0] if i == 0 else ctf.add_paragraph()
            cp.alignment = PP_ALIGN.CENTER
            cp.space_after = Pt(4)
            _run(cp, line, 16, theme["muted"], False)

    if date:
        db = pslide.shapes.add_textbox(
            Inches(1.0), layout.SLIDE_H - Inches(0.8),
            layout.SLIDE_W - Inches(2.0), Inches(0.5)
        )
        dp = db.text_frame.paragraphs[0]
        dp.alignment = PP_ALIGN.CENTER
        _run(dp, str(date), 14, theme["muted"], False)


def _run(p, text, size, color, bold):
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.name = "Yu Gothic"
    r.font.color.rgb = layout.rgb(color)
