"""配色トークン。presentation/templates/base.css.md のパレットを Python に転記。

HTML スライドと pptx のブランドを一致させるための単一情報源。
deck.theme（default / dark）で切り替える。色は "RRGGBB"（先頭 # なし）。
"""

from __future__ import annotations

# base.css.md の :root / [data-theme="dark"] と同値
THEMES: dict[str, dict[str, str]] = {
    "default": {
        "bg": "FFFFFF",
        "fg": "1A1A2E",
        "muted": "6B7280",
        "accent": "2563EB",
        "accent2": "7E57C2",
        "good": "16A34A",
        "bad": "DC2626",
        "line": "E5E7EB",
        "card": "F8FAFC",
        "on_accent": "FFFFFF",  # アクセント面上の文字色
    },
    "dark": {
        "bg": "0F172A",
        "fg": "F1F5F9",
        "muted": "94A3B8",
        "accent": "60A5FA",
        "accent2": "7E57C2",
        "good": "16A34A",
        "bad": "DC2626",
        "line": "334155",
        "card": "1E293B",
        "on_accent": "0F172A",
    },
}

# OS 標準フォント（base.css.md と同方針: Web フォント禁止）。
# 日本語が含まれるため和文ゴシックを既定にする。
FONT = "Yu Gothic"


def get_theme(name: str | None) -> dict[str, str]:
    """テーマ名から配色 dict を返す。未知のテーマは default にフォールバック。"""
    return THEMES.get(name or "default", THEMES["default"])
