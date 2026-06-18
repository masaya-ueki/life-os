"""expression 名 → 描画関数のレジストリ。

各描画関数のシグネチャ: render(slide, theme, data, region) -> None
region = (left, top, width, height)（EMU int）= 本文に使える領域。
未知/欠落の expression は builder 側で bullet にフォールバックする。
（title は全面レイアウトのため builder が個別処理する）
"""

from __future__ import annotations

from deckgen.expressions import bullet, chart, comparison, emphasis, flow, structure

RENDERERS = {
    "bullet": bullet.render,
    "comparison": comparison.render,
    "flow": flow.render,
    "structure": structure.render,
    "emphasis": emphasis.render,
    "chart": chart.render,
}


def get_renderer(expression: str | None):
    """expression に対応する描画関数を返す。無ければ None。"""
    return RENDERERS.get(expression or "")
