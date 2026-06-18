"""配色トークン。presentation/templates/theme-tokens.yml を単一ソースとして読む。

HTML スライド（slide-html-renderer）と pptx でブランドを一致させるための共有パレット。
deck.theme（default / dark / ...）で切り替える。色は内部的に "RRGGBB"（先頭 # なし）。
"""

from __future__ import annotations

from pathlib import Path

import yaml


def _find_tokens_file() -> Path:
    """配置場所に依存せず presentation/templates/theme-tokens.yml を探す。

    deckgen は支援ツール（scripts/deckgen）。loader._find_decks_dir と同様に、
    このファイルから上方向にリポジトリルートを辿って単一ソースを解決する。
    """
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "presentation" / "templates" / "theme-tokens.yml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "theme-tokens.yml が見つかりません（presentation/templates/）"
    )


def _load() -> tuple[dict[str, dict[str, str]], str]:
    """単一ソースを読み、(THEMES, FONT) を返す。

    色は #rrggbb で記述されているため、pptx 用に先頭 # を外して大文字化する。
    """
    data = yaml.safe_load(_find_tokens_file().read_text(encoding="utf-8"))
    themes = {
        name: {k: str(v).lstrip("#").upper() for k, v in tokens.items()}
        for name, tokens in data["themes"].items()
    }
    return themes, str(data.get("font", "Yu Gothic"))


# base.css.md と同じ配色を theme-tokens.yml から読み込む（二重定義を排除）。
THEMES, FONT = _load()


def get_theme(name: str | None) -> dict[str, str]:
    """テーマ名から配色 dict を返す。未知のテーマは default にフォールバック。"""
    return THEMES.get(name or "default", THEMES["default"])
