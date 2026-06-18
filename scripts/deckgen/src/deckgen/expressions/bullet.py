"""bullet: タイトル+本文の箇条書き。最も汎用的な表現（フォールバック先）。

描画関数の共通シグネチャ: render(pslide, theme, slide, region)
  pslide = python-pptx の Slide / theme = 配色 dict /
  slide  = outline のスライド辞書（content・data を持つ） /
  region = (left, top, width, height) 本文領域(EMU)
"""

from __future__ import annotations

from deckgen import layout


def render(pslide, theme, slide, region):
    left, top, width, height = region
    pts = slide.get("content") or []
    if not pts:
        return
    # 件数に応じて文字サイズを調整（詰め込みすぎ防止）
    size = 24 if len(pts) <= 4 else 20
    layout.add_bullets(
        pslide, left, top, width, height, [str(x) for x in pts],
        size=size, color=theme["fg"], line_spacing=1.35, space_after=10,
    )
