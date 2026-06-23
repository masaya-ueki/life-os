"""deckgen.qa のテスト。

正常系: 現存 deck が QA を pass すること
異常系: 合成データで各 check が正しく発火すること
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from deckgen.qa import (
    Finding,
    check_html,
    check_outline,
    check_pptx,
)


# ---------------------------------------------------------------------------
# Outline チェック
# ---------------------------------------------------------------------------

def _make_outline(slides: list[dict]) -> dict:
    return {
        "deck": {"title": "テスト", "theme": "default"},
        "chapters": [{"chapter": "c", "slides": slides}],
    }


def test_outline_clean_passes():
    outline = _make_outline([
        {"title": "タイトル", "summary": "s", "content": ["a", "b"], "expression": "bullet"},
    ])
    assert check_outline(outline, "test/outline.yml") == []


def test_outline_empty_title_flagged():
    outline = _make_outline([{"title": "", "expression": "bullet"}])
    findings = check_outline(outline, "test/outline.yml")
    assert any(f.check == "QA-OUTLINE-EMPTY" and f.severity == "error" for f in findings)


def test_outline_whitespace_title_flagged():
    outline = _make_outline([{"title": "   ", "expression": "bullet"}])
    findings = check_outline(outline, "test/outline.yml")
    assert any(f.check == "QA-OUTLINE-EMPTY" for f in findings)


def test_outline_placeholder_in_title_flagged():
    outline = _make_outline([{"title": "{{タイトルを入力}}", "expression": "bullet"}])
    findings = check_outline(outline, "test/outline.yml")
    assert any(f.check == "QA-OUTLINE-PH" and f.severity == "warning" for f in findings)


def test_outline_placeholder_in_content_flagged():
    outline = _make_outline([
        {"title": "t", "content": ["正常", "{{内容を入力}}"], "expression": "bullet"},
    ])
    findings = check_outline(outline, "test/outline.yml")
    assert any(f.check == "QA-OUTLINE-PH" for f in findings)


def test_outline_excess_bullets_flagged():
    """content が 8 件以上で QA-OUTLINE-EXCESS-BULLETS が発火する。"""
    content = [f"item{i}" for i in range(8)]  # 8 件（MAX_BULLETS=7 超え）
    outline = _make_outline([{"title": "t", "content": content, "expression": "bullet"}])
    findings = check_outline(outline, "test/outline.yml")
    assert any(f.check == "QA-OUTLINE-EXCESS-BULLETS" and f.severity == "warning" for f in findings)


def test_outline_exactly_max_bullets_passes():
    """content が MAX_BULLETS(7) 件ちょうどはフラグなし。"""
    content = [f"item{i}" for i in range(7)]
    outline = _make_outline([{"title": "t", "content": content, "expression": "bullet"}])
    findings = check_outline(outline, "test/outline.yml")
    assert not any(f.check == "QA-OUTLINE-EXCESS-BULLETS" for f in findings)


def test_real_deck_outline_passes():
    """claude-code-security の outline.yml は品質問題なし。"""
    from deckgen.loader import load_outline
    outline = load_outline("claude-code-security")
    findings = check_outline(outline, "claude-code-security/outline.yml")
    errors = [f for f in findings if f.severity == "error"]
    assert errors == [], errors


# ---------------------------------------------------------------------------
# HTML チェック
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>test</title><style>body{{}}</style></head>
<body>
{slides}
<script>var x=1;</script>
</body>
</html>
"""

_SLIDE_TEMPLATE = '<div class="slide" data-variant="{variant}">{content}</div>'


def _make_html(slides_html: str) -> str:
    return _HTML_TEMPLATE.format(slides=slides_html)


def test_html_clean_passes():
    slides = _SLIDE_TEMPLATE.format(variant="bullet", content="<h2>タイトル</h2><p>内容</p>")
    findings = check_html_from_str(_make_html(slides), "test/index.html")
    assert findings == []


def test_html_external_script_flagged():
    html = '<!DOCTYPE html><html><head><script src="https://cdn.example.com/app.js"></script></head><body></body></html>'
    findings = check_html_from_str(html, "test/index.html")
    assert any(f.check == "QA-HTML-EXTERNAL" and f.severity == "error" for f in findings)


def test_html_external_link_flagged():
    html = '<!DOCTYPE html><html><head><link href="https://fonts.googleapis.com/css" rel="stylesheet"></head><body></body></html>'
    findings = check_html_from_str(html, "test/index.html")
    assert any(f.check == "QA-HTML-EXTERNAL" for f in findings)


def test_html_external_img_src_in_slide_flagged():
    content = '<img src="https://example.com/img.png" alt="x">'
    slides = _SLIDE_TEMPLATE.format(variant="bullet", content=content)
    findings = check_html_from_str(_make_html(slides), "test/index.html")
    assert any(f.check == "QA-HTML-EXTERNAL" for f in findings)


def test_html_placeholder_in_slide_flagged():
    content = "<h2>{{スライドタイトル}}</h2>"
    slides = _SLIDE_TEMPLATE.format(variant="bullet", content=content)
    findings = check_html_from_str(_make_html(slides), "test/index.html")
    assert any(f.check == "QA-HTML-EMPTY-PH" and f.severity == "warning" for f in findings)


def test_html_overflow_in_slide_flagged():
    """601 文字超のテキストを含むスライドで QA-HTML-OVERFLOW が発火する。"""
    long_text = "あ" * 601
    content = f"<p>{long_text}</p>"
    slides = _SLIDE_TEMPLATE.format(variant="bullet", content=content)
    findings = check_html_from_str(_make_html(slides), "test/index.html")
    assert any(f.check == "QA-HTML-OVERFLOW" and f.severity == "warning" for f in findings)


def test_html_overflow_exactly_600_passes():
    """ちょうど 600 文字はフラグなし。"""
    text = "あ" * 600
    content = f"<p>{text}</p>"
    slides = _SLIDE_TEMPLATE.format(variant="bullet", content=content)
    findings = check_html_from_str(_make_html(slides), "test/index.html")
    assert not any(f.check == "QA-HTML-OVERFLOW" for f in findings)


def test_real_deck_html_no_external_deps():
    """claude-code-security/index.html に外部 URL がない。"""
    from deckgen.loader import DECKS_DIR
    html_path = DECKS_DIR / "claude-code-security" / "index.html"
    if not html_path.exists():
        pytest.skip("index.html が生成されていない")
    findings = check_html(html_path)
    external = [f for f in findings if f.check == "QA-HTML-EXTERNAL"]
    assert external == [], external


# ---------------------------------------------------------------------------
# PPTX チェック
# ---------------------------------------------------------------------------

def _make_minimal_pptx(out: Path) -> None:
    """python-pptx で最小の pptx（テキストフレームなし）を生成する。"""
    from pptx import Presentation
    prs = Presentation()
    layout = prs.slide_layouts[6]  # blank
    prs.slides.add_slide(layout)
    prs.save(str(out))


def _make_pptx_with_text(out: Path, text: str) -> None:
    """指定テキストを持つ pptx を生成する。"""
    from pptx import Presentation
    from pptx.util import Inches
    prs = Presentation()
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(5))
    txBox.text_frame.text = text
    prs.save(str(out))


def _make_pptx_with_empty_frame(out: Path) -> None:
    """空テキストフレームを含む pptx を生成する。"""
    from pptx import Presentation
    from pptx.util import Inches
    prs = Presentation()
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(5))
    txBox.text_frame.text = ""
    prs.save(str(out))


def test_pptx_clean_passes():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test.pptx"
        _make_pptx_with_text(out, "正常なテキスト")
        findings = check_pptx(out)
        errors = [f for f in findings if f.severity == "error"]
        assert errors == []


def test_pptx_empty_text_frame_flagged():
    """空テキストフレームで QA-PPTX-EMPTY が発火する。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test.pptx"
        _make_pptx_with_empty_frame(out)
        findings = check_pptx(out)
        assert any(f.check == "QA-PPTX-EMPTY" and f.severity == "warning" for f in findings)


def test_pptx_placeholder_flagged():
    """プレースホルダパターンで QA-PPTX-PH が発火する。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test.pptx"
        _make_pptx_with_text(out, "{{ここに内容を入力}}")
        findings = check_pptx(out)
        assert any(f.check == "QA-PPTX-PH" and f.severity == "warning" for f in findings)


def test_real_deck_pptx_no_errors():
    """claude-code-security から生成した pptx に error がない。"""
    from deckgen.builder import build_to_file
    from deckgen.loader import load_outline
    outline = load_outline("claude-code-security")
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "claude-code-security.pptx"
        build_to_file(outline, out)
        findings = check_pptx(out)
        errors = [f for f in findings if f.severity == "error"]
        assert errors == [], errors


# ---------------------------------------------------------------------------
# ヘルパ（テスト内のみ使用）
# ---------------------------------------------------------------------------

def check_html_from_str(html: str, label: str) -> list[Finding]:
    """HTML 文字列を直接検査するテスト用ヘルパ。"""
    from deckgen.qa import _HtmlQaParser
    parser = _HtmlQaParser(label)
    parser.feed(html)
    return parser.findings
