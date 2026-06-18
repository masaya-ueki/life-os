"""deckgen のスモークテスト。

- 実 deck(claude-code-security)からスライド数一致・表シェイプ存在を確認
- 合成 outline で全 expression（chart/emphasis/structure/flow/comparison）を描画し、
  チャートが生成され、画像が一切含まれない（=編集可能ネイティブ）ことを確認
"""

from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE_TYPE

from deckgen.builder import build_presentation
from deckgen.loader import iter_slides, load_outline


def _all_shapes(prs):
    for s in prs.slides:
        yield from s.shapes


def test_real_deck_slide_count_and_table():
    outline = load_outline("claude-code-security")
    expected = sum(1 for _ in iter_slides(outline))
    prs, warnings = build_presentation(outline)
    assert len(prs.slides) == expected
    # comparison table を含むスライドがある
    assert any(sh.has_table for sh in _all_shapes(prs))
    # 既知 expression のみなので未知警告は無い
    assert warnings == []


def test_no_images_means_editable():
    outline = load_outline("claude-code-security")
    prs, _ = build_presentation(outline)
    pics = [
        sh for sh in _all_shapes(prs)
        if sh.shape_type == MSO_SHAPE_TYPE.PICTURE
    ]
    assert pics == []


SYNTH = {
    "deck": {"title": "テスト", "subtitle": "sub", "theme": "dark"},
    "chapters": [
        {
            "chapter": "c",
            "slides": [
                {"title": "表紙", "summary": "s", "content": ["a"],
                 "expression": "title"},
                {"title": "棒グラフ", "summary": "推移", "expression": "chart",
                 "data": {"type": "bar", "unit": "%",
                          "series": [{"label": "2024", "value": 30},
                                     {"label": "2025", "value": 65}]}},
                {"title": "強調", "summary": "msg", "expression": "emphasis",
                 "data": {"mode": "big-number", "value": "-80", "unit": "%",
                          "label": "件数"}},
                {"title": "マトリクス", "summary": "m", "expression": "structure",
                 "data": {"type": "matrix-2x2", "axis_x": "x", "axis_y": "y",
                          "quadrants": ["A", "B", "C", "D"]}},
                {"title": "フロー", "summary": "f", "expression": "flow",
                 "data": {"type": "steps", "orientation": "horizontal",
                          "steps": [{"label": "1", "desc": "d"},
                                    {"label": "2", "desc": "d"}]}},
                {"title": "未知", "summary": "u", "content": ["x", "y"],
                 "expression": "nonexistent"},
            ],
        }
    ],
}


def test_synthetic_all_expressions_and_chart():
    prs, warnings = build_presentation(SYNTH)
    assert len(prs.slides) == 6
    # ネイティブチャートが1つ生成される
    assert sum(1 for sh in _all_shapes(prs) if sh.has_chart) == 1
    # 画像は無い
    assert not any(
        sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in _all_shapes(prs)
    )
    # 未知 expression は警告される
    assert any("nonexistent" in w for w in warnings)


def test_titles_present():
    prs, _ = build_presentation(SYNTH)
    texts = " ".join(
        sh.text_frame.text for sh in _all_shapes(prs) if sh.has_text_frame
    )
    assert "棒グラフ" in texts
    assert "マトリクス" in texts
