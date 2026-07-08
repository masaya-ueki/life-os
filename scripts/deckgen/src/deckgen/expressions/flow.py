"""flow: 手順・流れ。type = steps | timeline | cycle（timeline/cycle は steps 同様に描く）。

data 契約: slide-expression/references/flow.md
"""

from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

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
    # 横フローは 3〜5 ステップまで（flow.md 準拠）。6 以上は横幅が不足するため
    # 縦レイアウトに自動切替する。
    if n >= 6:
        _vertical(pslide, theme, steps, region)
        return
    gap = layout.FLOW_ARROW_W + layout.FLOW_H_GAP_PAD
    box_w = (width - gap * (n - 1)) // n
    box_h = min(layout.FLOW_BOX_MAX_H, height)
    box_top = top + (height - box_h) // 2
    for i, step in enumerate(steps):
        x = left + i * (box_w + gap)
        label, desc = _step_texts(step)
        layout.add_card(pslide, x, box_top, box_w, box_h, theme)
        _badge(pslide, x, box_top, theme, i + 1)
        # バッジ下端との重なりを避けラベルを下にずらす
        layout.add_textbox(
            pslide, x + layout.FLOW_LABEL_PAD, box_top + layout.FLOW_LABEL_TOP,
            box_w - layout.FLOW_LABEL_PAD * 2, layout.FLOW_LABEL_H,
            label, size=layout.FLOW_LABEL_FONT, color=theme["accent"], bold=True,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
        )
        if desc:
            desc_top = (
                box_top + layout.FLOW_LABEL_TOP + layout.FLOW_LABEL_H + layout.SPACE_1
            )
            desc_h = (
                box_h
                - (layout.FLOW_LABEL_TOP + layout.FLOW_LABEL_H + layout.SPACE_1)
                - layout.CARD_PAD_Y
            )
            layout.add_textbox(
                pslide, x + layout.DIAG_PAD, desc_top,
                box_w - layout.DIAG_PAD * 2, desc_h,
                desc, size=layout.FLOW_DESC_FONT, color=theme["fg"],
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.TOP, autofit=True,
            )
        # 矢印（最後以外）
        if i < n - 1:
            layout.add_arrow(
                pslide, x + box_w + layout.FLOW_ARROW_OFFSET_H,
                box_top + box_h // 2 - layout.FLOW_ARROW_BODY_H // 2,
                layout.FLOW_ARROW_W, layout.FLOW_ARROW_BODY_H, color=theme["muted"],
            )


def _vertical(pslide, theme, steps, region):
    left, top, width, height = region
    n = len(steps)
    gap = layout.FLOW_ARROW_H + layout.DIAG_PAD_XS
    box_h = (height - gap * (n - 1)) // n
    for i, step in enumerate(steps):
        y = top + i * (box_h + gap)
        label, desc = _step_texts(step)
        layout.add_card(pslide, left, y, width, box_h, theme)
        _badge(pslide, left, y, theme, i + 1)
        text = f"{label}" + (f" — {desc}" if desc else "")
        layout.add_textbox(
            pslide, left + layout.FLOW_V_TEXT_LEFT, y,
            width - layout.FLOW_V_TEXT_LEFT - layout.CARD_PAD_X, box_h,
            text, size=layout.FLOW_LABEL_FONT, color=theme["fg"], bold=False,
            anchor=MSO_ANCHOR.MIDDLE, autofit=True,
        )
        if i < n - 1:
            layout.add_down_arrow(
                pslide, left + width // 2 - layout.FLOW_ARROW_BODY_H // 2,
                y + box_h + layout.FLOW_ARROW_OFFSET_V,
                layout.FLOW_ARROW_BODY_H, layout.FLOW_ARROW_H, color=theme["muted"],
            )


def _badge(pslide, x, y, theme, num):
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
    layout.set_center_text(sp, str(num), size=layout.BADGE_FONT, color=theme["on_accent"])
