"""theme.py のスモークテスト。

配色トークンが単一ソース presentation/templates/theme-tokens.yml から読まれ、
pptx 用の正規化（先頭 # 除去・大文字 16 進）が効いていることを確認する。
"""

from __future__ import annotations

import re

from deckgen.theme import FONT, THEMES, get_theme

_HEX = re.compile(r"^[0-9A-F]{6}$")


def test_known_themes_loaded_from_single_source():
    # theme-tokens.yml の値が #rrggbb → RRGGBB に正規化されて読まれる
    assert get_theme("default")["accent"] == "2563EB"
    assert get_theme("dark")["bg"] == "0F172A"
    assert get_theme("default")["on_accent"] == "FFFFFF"


def test_unknown_theme_falls_back_to_default():
    assert get_theme("no-such-theme") == get_theme("default")
    assert get_theme(None) == get_theme("default")


def test_colors_are_normalized_uppercase_hex_without_hash():
    for tokens in THEMES.values():
        for value in tokens.values():
            assert _HEX.match(value), value


def test_font_is_loaded():
    assert FONT == "Yu Gothic"
