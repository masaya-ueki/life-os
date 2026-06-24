"""生成スライドの QA チェッカー（post-generation fitness function）。

outline.yml / index.html / .pptx の 3 つの生成物を検査し、
明らかな品質問題（テキスト溢れ・空プレースホルダ・外部依存・1スライド1メッセージ逸脱）
を自動検知・報告する。check_structure.py と同じ出力インタフェースを採用する。

使い方:
    uv run --project scripts/deckgen -m deckgen.qa <slug>        # 特定 deck を検査
    uv run --project scripts/deckgen -m deckgen.qa --all          # 全 deck を検査
    uv run --project scripts/deckgen -m deckgen.qa <slug> --json  # JSON 出力
    uv run --project scripts/deckgen -m deckgen.qa <slug> --strict # warning でも exit 1

終了コード: error が 1 件以上なら 1。--strict なら warning でも 1。なければ 0。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path

from deckgen.loader import DECKS_DIR, load_outline, resolve_outline_path

# --- 定数 ---

PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")
MAX_BULLETS = 7         # これを超えると 1スライド1メッセージ逸脱と判定
OVERFLOW_CHARS_HTML = 600  # 1スライドのテキスト上限（HTML）
OVERFLOW_CHARS_PER_CM2 = 6  # pptx: 1cm² あたりの推定最大文字数
OVERFLOW_MIN_CHARS = 100    # pptx: 最低閾値

# void 要素は handle_endtag が呼ばれないため depth カウントから除外
_VOID_ELEMENTS = frozenset(
    ["area", "base", "br", "col", "embed", "hr", "img", "input",
     "link", "meta", "param", "source", "track", "wbr"]
)


@dataclass
class Finding:
    check: str
    severity: str  # "error" | "warning"
    path: str
    message: str


# ---------------------------------------------------------------------------
# Outline チェック
# ---------------------------------------------------------------------------

def check_outline(outline: dict, label: str) -> list[Finding]:
    """outline.yml を検査し、論理的な品質問題を返す。"""
    findings: list[Finding] = []
    for ci, ch in enumerate(outline.get("chapters", [])):
        for si, slide in enumerate(ch.get("slides", [])):
            slide_label = f"{label}:ch{ci + 1}/slide{si + 1}"

            # QA-OUTLINE-EMPTY: title が空
            title = str(slide.get("title", ""))
            if not title.strip():
                findings.append(Finding(
                    "QA-OUTLINE-EMPTY", "error", slide_label, "title が空"))

            # QA-OUTLINE-PH: プレースホルダ残存
            all_text = " ".join([
                title,
                str(slide.get("summary", "")),
                str(slide.get("message", "")),
                " ".join(str(c) for c in slide.get("content", [])),
            ])
            if PLACEHOLDER_RE.search(all_text):
                findings.append(Finding(
                    "QA-OUTLINE-PH", "warning", slide_label, "プレースホルダ残存"))

            # QA-OUTLINE-EXCESS-BULLETS: 1スライド1メッセージ逸脱
            content = slide.get("content", [])
            if isinstance(content, list) and len(content) > MAX_BULLETS:
                findings.append(Finding(
                    "QA-OUTLINE-EXCESS-BULLETS", "warning", slide_label,
                    f"content が多い ({len(content)} 件 > {MAX_BULLETS})"))

    return findings


# ---------------------------------------------------------------------------
# HTML チェック
# ---------------------------------------------------------------------------

class _HtmlQaParser(HTMLParser):
    """`.slide` 要素を追跡して品質問題を検出する HTMLParser。"""

    def __init__(self, label_prefix: str) -> None:
        super().__init__()
        self._prefix = label_prefix
        self.findings: list[Finding] = []
        self._depth = 0
        self._slide_count = 0
        self._in_slide = False
        self._slide_open_depth = -1
        self._text_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs_dict = dict(attrs)

        # QA-HTML-EXTERNAL: src / href に外部 URL
        for attr in ("src", "href"):
            val = attrs_dict.get(attr, "")
            if val.startswith(("http://", "https://")):
                self.findings.append(Finding(
                    "QA-HTML-EXTERNAL", "error",
                    f"{self._prefix}:{tag}",
                    f"外部 URL ({attr}): {val[:80]}"))

        # QA-HTML-EXTERNAL: style 属性の url() に外部 URL
        for m in re.finditer(r"url\(['\"]?(https?://[^\s'\"\)\]]+)", attrs_dict.get("style", "")):
            self.findings.append(Finding(
                "QA-HTML-EXTERNAL", "error",
                f"{self._prefix}:{tag}",
                f"外部 URL (style): {m.group(1)[:80]}"))

        if tag.lower() in _VOID_ELEMENTS:
            return

        self._depth += 1

        # slide div の開始を検出
        if tag.lower() == "div" and not self._in_slide:
            classes = attrs_dict.get("class", "").split()
            if "slide" in classes:
                self._in_slide = True
                self._slide_open_depth = self._depth
                self._slide_count += 1
                self._text_buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _VOID_ELEMENTS:
            return
        if self._in_slide and tag.lower() == "div" and self._depth == self._slide_open_depth:
            self._flush_slide()
            self._in_slide = False
        self._depth -= 1

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        # XHTML スタイルの自己閉鎖タグ（<div/> など）への対応
        self.handle_starttag(tag, attrs)
        if tag.lower() not in _VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self._in_slide:
            self._text_buf.append(data)

    def _flush_slide(self) -> None:
        text = "".join(self._text_buf)
        label = f"{self._prefix}:slide-{self._slide_count}"

        # QA-HTML-EMPTY-PH: プレースホルダ残存
        if PLACEHOLDER_RE.search(text):
            self.findings.append(Finding(
                "QA-HTML-EMPTY-PH", "warning", label, "プレースホルダ残存"))

        # QA-HTML-OVERFLOW: テキスト量超過
        clean = re.sub(r"\s+", " ", text).strip()
        if len(clean) > OVERFLOW_CHARS_HTML:
            self.findings.append(Finding(
                "QA-HTML-OVERFLOW", "warning", label,
                f"テキスト量超過 ({len(clean)} 文字 > {OVERFLOW_CHARS_HTML})"))


def check_html(html_path: Path, label_prefix: str | None = None) -> list[Finding]:
    """index.html を検査し、レンダリング品質問題を返す。"""
    prefix = label_prefix or html_path.as_posix()
    parser = _HtmlQaParser(prefix)
    parser.feed(html_path.read_text(encoding="utf-8"))
    return parser.findings


# ---------------------------------------------------------------------------
# PPTX チェック
# ---------------------------------------------------------------------------

def check_pptx(pptx_path: Path, label_prefix: str | None = None) -> list[Finding]:
    """生成済み .pptx を検査し、レンダリング品質問題を返す。"""
    from pptx import Presentation  # noqa: PLC0415

    prefix = label_prefix or pptx_path.as_posix()
    findings: list[Finding] = []
    prs = Presentation(str(pptx_path))

    for i, slide in enumerate(prs.slides, 1):
        slide_label = f"{prefix}:slide-{i}"

        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            tf = shape.text_frame
            text = tf.text

            # QA-PPTX-EMPTY: 空テキストフレーム
            if not text.strip():
                findings.append(Finding(
                    "QA-PPTX-EMPTY", "warning", slide_label, "空のテキストフレーム"))
                continue

            # QA-PPTX-PH: プレースホルダ残存
            if PLACEHOLDER_RE.search(text):
                findings.append(Finding(
                    "QA-PPTX-PH", "warning", slide_label, "プレースホルダ残存"))

            # QA-PPTX-OVERFLOW: テキスト量超過（面積ベースのヒューリスティック）
            try:
                w_cm = shape.width.cm
                h_cm = shape.height.cm
                if w_cm > 0 and h_cm > 0:
                    limit = max(OVERFLOW_MIN_CHARS, w_cm * h_cm * OVERFLOW_CHARS_PER_CM2)
                    if len(text) > limit:
                        findings.append(Finding(
                            "QA-PPTX-OVERFLOW", "warning", slide_label,
                            f"テキスト量超過 ({len(text)} 文字 > {int(limit)})"))
            except (AttributeError, TypeError):
                pass

    return findings


# ---------------------------------------------------------------------------
# Deck ファサード
# ---------------------------------------------------------------------------

def check_deck(slug_or_path: str) -> list[Finding]:
    """outline.yml / index.html / .pptx をまとめて検査する。"""
    findings: list[Finding] = []
    outline_path = resolve_outline_path(slug_or_path)
    deck_dir = outline_path.parent
    slug = deck_dir.name

    # outline.yml
    try:
        outline = load_outline(slug_or_path)
        findings.extend(check_outline(outline, f"{slug}/outline.yml"))
    except Exception as exc:
        findings.append(Finding(
            "QA-OUTLINE-LOAD", "error", f"{slug}/outline.yml",
            f"読み込みエラー: {exc}"))
        return findings

    # index.html（存在する場合のみ）
    html_path = deck_dir / "index.html"
    if html_path.exists():
        findings.extend(check_html(html_path, label_prefix=f"{slug}/index.html"))

    # {slug}.pptx（存在する場合のみ）
    pptx_path = deck_dir / f"{slug}.pptx"
    if pptx_path.exists():
        findings.extend(check_pptx(pptx_path, label_prefix=f"{slug}/{slug}.pptx"))

    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_report(findings: list[Finding]) -> None:
    for f in findings:
        marker = "✗" if f.severity == "error" else "⚠"
        print(f"{marker} [{f.check}] {f.path}: {f.message}")
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    print(f"— error: {errors} / warning: {warnings}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="deckgen.qa",
        description="生成スライドの QA チェック（post-generation fitness function）",
    )
    parser.add_argument("target", nargs="?",
                        help="deck の slug またはパス（--all と排他）")
    parser.add_argument("--all", action="store_true",
                        help="domains/presentation/decks/ 配下の全 deck を検査")
    parser.add_argument("--json", action="store_true",
                        help="JSON で出力（check_structure.py 準拠）")
    parser.add_argument("--strict", action="store_true",
                        help="warning でも exit 1")
    args = parser.parse_args(argv)

    if args.all:
        targets = sorted(d.name for d in DECKS_DIR.iterdir() if d.is_dir())
    elif args.target:
        targets = [args.target]
    else:
        parser.print_help()
        return 2

    all_findings: list[Finding] = []
    for target in targets:
        all_findings.extend(check_deck(target))

    if args.json:
        summary = {
            "error": sum(1 for f in all_findings if f.severity == "error"),
            "warning": sum(1 for f in all_findings if f.severity == "warning"),
        }
        print(json.dumps(
            {"findings": [asdict(f) for f in all_findings], "summary": summary},
            ensure_ascii=False, indent=2))
    else:
        _print_report(all_findings)

    errors = sum(1 for f in all_findings if f.severity == "error")
    warnings = sum(1 for f in all_findings if f.severity == "warning")
    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
