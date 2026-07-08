"""title: 表紙の全面レイアウト。builder から個別に呼ばれる。

左揃えラインはコンテンツスライドと同じ CONTENT_LEFT / CONTENT_WIDTH を使い、
章をまたいでも左端が一直線に揃うようにする。座標は layout.COVER_* が単一の真実。
"""

from __future__ import annotations

from pptx.enum.text import MSO_ANCHOR

from deckgen import layout


def render_cover(pslide, theme, deck, slide):
    title = slide.get("title") or deck.get("title", "")
    subtitle = slide.get("summary") or deck.get("subtitle", "")
    content = [str(x) for x in (slide.get("content") or [])]
    date = deck.get("date", "")

    # 左端アクセントバー（表紙のビジュアルアンカー）
    layout.add_accent_bar(
        pslide, 0, 0, layout.SLIDE_H, theme["accent"], width=layout.COVER_BAR_W,
    )
    # タイトル下のアクセントライン
    layout.add_rule(
        pslide, layout.CONTENT_LEFT, layout.COVER_RULE_Y, layout.CONTENT_WIDTH,
        theme["accent"], weight=3.0,
    )

    # メインタイトル（下端をルール線に合わせる）
    layout.add_textbox(
        pslide, layout.CONTENT_LEFT, layout.COVER_TITLE_TOP,
        layout.CONTENT_WIDTH, layout.COVER_TITLE_H,
        title, size=layout.FONT_DISPLAY, color=theme["accent"], bold=True,
        anchor=MSO_ANCHOR.MIDDLE, autofit=True,
    )

    if subtitle:
        layout.add_textbox(
            pslide, layout.CONTENT_LEFT, layout.COVER_SUBTITLE_TOP,
            layout.CONTENT_WIDTH, layout.COVER_SUBTITLE_H,
            subtitle, size=layout.FONT_LEAD, color=theme["fg"],
        )

    if content:
        layout.add_bullets(
            pslide, layout.CONTENT_LEFT, layout.COVER_CONTENT_TOP,
            layout.CONTENT_WIDTH, layout.COVER_CONTENT_H,
            content, size=layout.FONT_SMALL, color=theme["muted"],
            bullet="· ", line_spacing=1.2, space_after=4,
        )

    if date:
        layout.add_textbox(
            pslide, layout.CONTENT_LEFT, layout.COVER_DATE_TOP,
            layout.CONTENT_WIDTH, layout.COVER_DATE_H,
            str(date), size=layout.FONT_CAPTION, color=theme["muted"],
        )
