"""outline.yml の読込と最低限の構造検証。

スキーマの単一の真実は domains/presentation/README.md。ここでは pptx 生成に必要な
構造（deck / chapters / slides）が揃っているかだけを確認する。
"""

from __future__ import annotations

from pathlib import Path

import yaml


def _find_decks_dir() -> Path:
    """配置場所に依存せず domains/presentation/decks を探す。

    deckgen は支援ツール（scripts/deckgen）。このファイルから上方向に
    `domains/presentation/decks` を持つリポジトリルートを探索する。
    """
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "domains" / "presentation" / "decks"
        if candidate.is_dir():
            return candidate
    return Path.cwd() / "domains" / "presentation" / "decks"


DECKS_DIR = _find_decks_dir()


class OutlineError(ValueError):
    """outline.yml の構造が pptx 生成に不適な場合に送出。"""


def resolve_outline_path(slug_or_path: str) -> Path:
    """slug もしくはパスから outline.yml の絶対パスを解決する。

    - 既存ファイルパス（.yml/.yaml）ならそのまま
    - ディレクトリなら そのディレクトリ/outline.yml
    - それ以外は slug とみなし domains/presentation/decks/{slug}/outline.yml
    """
    p = Path(slug_or_path)
    if p.is_file():
        return p.resolve()
    if p.is_dir():
        return (p / "outline.yml").resolve()
    return (DECKS_DIR / slug_or_path / "outline.yml").resolve()


def load_outline(slug_or_path: str) -> dict:
    """outline.yml を読み、検証済みの dict を返す。"""
    path = resolve_outline_path(slug_or_path)
    if not path.exists():
        raise OutlineError(f"outline.yml が見つかりません: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    _validate(data, path)
    return data


def _validate(data: object, path: Path) -> None:
    if not isinstance(data, dict):
        raise OutlineError(f"トップレベルは mapping である必要があります: {path}")
    if not isinstance(data.get("deck"), dict):
        raise OutlineError("`deck` セクションがありません")
    chapters = data.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise OutlineError("`chapters` は 1 件以上の配列である必要があります")
    for ci, ch in enumerate(chapters):
        if not isinstance(ch, dict) or not isinstance(ch.get("slides"), list):
            raise OutlineError(f"chapters[{ci}] に slides 配列がありません")
        for si, sl in enumerate(ch["slides"]):
            if not isinstance(sl, dict) or not sl.get("title"):
                raise OutlineError(
                    f"chapters[{ci}].slides[{si}] に title がありません"
                )


def iter_slides(outline: dict):
    """(chapter_name, slide_dict) を順に返すイテレータ。"""
    for ch in outline["chapters"]:
        chapter = ch.get("chapter", "")
        for slide in ch["slides"]:
            yield chapter, slide
