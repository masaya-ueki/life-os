"""flow: 手順・流れ。type = steps | timeline | cycle（timeline/cycle は steps 同様に描く）。

data 契約: slide-expression/references/flow.md
"""

from __future__ import annotations

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches

from deckgen import layout


def render(pslide, theme, slide, region):
    data = slide.get("data") or {}
    steps = data.get("steps") or []
    if not steps:
        return
    orientation = data.get("orientation", "horizontal")
    if orientation == "vertical":
        _vertical(pslide, theme, steps, region)
    else:
        _horizontal(pslide, theme, steps, region)


def _step_texts(step):
    if isinstance(step, dict):
        date = step.get("date")
        label = step.get("label", "")
        label = f"{date}　{label}" if date else label
        return str(label), str(step.get("desc", ""))
    return str(step), ""


def _horizontal(pslide, theme, steps, region):
    left, top, width, height = region
    n = len(steps)
    gap = layout.FLOW_ARROW_W + layout.FLOW_H_GAP_PAD
    box_w = (width - gap * (n - 1)) // n
    box_h = min(Inches(2.4), height)
    box_top = top + (height - box_h) // 2
    for i, step in enumerate(steps):
        x = left + i * (box_w + gap)
        label, desc = _step_texts(step)
        layout.add_box_shape(
            pslide, x, box_top, box_w, box_h,
            fill=theme["card"], line=theme["accent"], line_width=layout.DIAG_LINE_BOLD,
        )
        _badge(pslide, x, box_top, theme, i + 1)
        layout.add_textbox(
            pslide, x + layout.FLOW_LABEL_PAD, box_top + Inches(0.45),
            box_w - layout.FLOW_LABEL_PAD * 2, Inches(0.7),
            label, size=layout.FLOW_LABEL_FONT, color=theme["accent"], bold=True,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
        )
        if desc:
            layout.add_textbox(
                pslide, x + layout.DIAG_PAD, box_top + Inches(1.15),
                box_w - layout.DIAG_PAD * 2, box_h - Inches(1.3),
                desc, size=layout.FLOW_DESC_FONT, color=theme["fg"],
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.TOP,
            )
        # 矢印（最後以外）
        if i < n - 1:
            layout.add_arrow(
                pslide, x + box_w + layout.FLOW_ARROW_OFFSET_H,
                box_top + box_h // 2 - Inches(0.2),
                layout.FLOW_ARROW_W, Inches(0.4), color=theme["muted"],
            )


def _vertical(pslide, theme, steps, region):
    left, top, width, height = region
    n = len(steps)
    gap = layout.FLOW_ARROW_H + layout.DIAG_PAD_XS
    box_h = (height - gap * (n - 1)) // n
    for i, step in enumerate(steps):
        y = top + i * (box_h + gap)
        label, desc = _step_texts(step)
        layout.add_box_shape(
            pslide, left, y, width, box_h,
            fill=theme["card"], line=theme["accent"], line_width=layout.DIAG_LINE_BOLD,
        )
        _badge(pslide, left, y, theme, i + 1)
        text = f"{label}" + (f" — {desc}" if desc else "")
        layout.add_textbox(
            pslide, left + Inches(0.9), y, width - Inches(1.1), box_h,
            text, size=layout.FLOW_LABEL_FONT, color=theme["fg"], bold=False,
            anchor=MSO_ANCHOR.MIDDLE,
        )
        if i < n - 1:
            layout.add_down_arrow(
                pslide, left + width // 2 - Inches(0.2),
                y + box_h + layout.FLOW_ARROW_OFFSET_V,
                Inches(0.4), layout.FLOW_ARROW_H, color=theme["muted"],
            )


def _badge(pslide, x, y, theme, num):
    from pptx.enum.shapes import MSO_SHAPE
    sp = pslide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        x + layout.DIAG_PAD_SM,
        y + layout.BADGE_Y_OFFSET,
        layout.BADGE_D,
        layout.BADGE_D,
    )
    sp.fill.solid()
    sp.fill.fore_color.rgb = layout.rgb(theme["accent"])
    sp.line.fill.background()
    sp.shadow.inherit = False
    tf = sp.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _run(p, str(num), layout.BADGE_FONT, theme["on_accent"], True, theme)


def _run(p, text, size, color, bold, theme):
    from pptx.util import Pt
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.name = "Yu Gothic"
    r.font.color.rgb = layout.rgb(color)
