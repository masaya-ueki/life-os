"""chart: 数値の可視化（ネイティブ PowerPoint チャート）。
type = bar | line | pie | stacked。data 不足時は本文の箇条書きにフォールバック。

data 契約: slide-expression/references/chart.md
"""

from __future__ import annotations

from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.util import Inches, Pt

from deckgen import layout

_CHART_TYPES = {
    "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "line": XL_CHART_TYPE.LINE_MARKERS,
    "pie": XL_CHART_TYPE.PIE,
    "stacked": XL_CHART_TYPE.COLUMN_STACKED,
}


def render(pslide, theme, slide, region):
    data = slide.get("data") or {}
    ctype = data.get("type", "bar")
    series = data.get("series") or []
    chart_data, ok = _build_chart_data(ctype, series)
    if not ok:
        # データが無ければ本文をそのまま箇条書きに
        from deckgen.expressions import bullet
        bullet.render(pslide, theme, slide, region)
        return

    left, top, width, height = region
    note = data.get("note")
    note_h = Inches(0.4) if note else 0
    chart_h = height - note_h

    xl_type = _CHART_TYPES.get(ctype, XL_CHART_TYPE.COLUMN_CLUSTERED)
    gframe = pslide.shapes.add_chart(xl_type, left, top, width, chart_h, chart_data)
    chart = gframe.chart
    _style_chart(chart, theme, ctype, data.get("unit"))

    if note:
        layout.add_textbox(
            pslide, left, top + chart_h + Inches(0.05), width, note_h,
            str(note), size=layout.FONT_CAPTION, color=theme["muted"],
        )


def _build_chart_data(ctype, series):
    cd = CategoryChartData()
    if not series:
        return cd, False
    multi = ctype in ("line", "stacked") or (
        isinstance(series[0], dict) and "points" in series[0]
    )
    try:
        if multi:
            first = series[0]
            cats = [str(pt.get("x")) for pt in (first.get("points") or [])]
            if not cats:
                return cd, False
            cd.categories = cats
            for s in series:
                name = str(s.get("name", ""))
                ys = [_num(pt.get("y")) for pt in (s.get("points") or [])]
                cd.add_series(name, ys)
        else:
            cats = [str(s.get("label", "")) for s in series]
            vals = [_num(s.get("value")) for s in series]
            if not any(v is not None for v in vals):
                return cd, False
            cd.categories = cats
            cd.add_series("値", vals)
    except (AttributeError, TypeError):
        return cd, False
    return cd, True


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _style_chart(chart, theme, ctype, unit):
    chart.has_title = False
    if ctype in ("pie",):
        chart.has_legend = True
        chart.legend.position = XL_LEGEND_POSITION.RIGHT
        chart.legend.include_in_layout = False
        plot = chart.plots[0]
        plot.has_data_labels = True
        plot.data_labels.number_format = "0%" if unit == "%" else "General"
        plot.data_labels.number_format_is_linked = False
    elif ctype in ("stacked", "line"):
        chart.has_legend = True
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
    else:
        chart.has_legend = False
        # 単系列の棒はアクセント色で塗る
        try:
            chart.series[0].format.fill.solid()
            chart.series[0].format.fill.fore_color.rgb = layout.rgb(theme["accent"])
        except (IndexError, AttributeError):
            pass
