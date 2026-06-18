"""deckgen — outline.yml を編集可能なネイティブ pptx に変換するビルドツール。

設計根拠: docs/adr/0004-pptx-output.md
契約(outline.yml スキーマ): presentation/README.md と
.claude/skills/slide-expression/references/*.md
"""

from deckgen.builder import build_presentation
from deckgen.loader import load_outline

__all__ = ["build_presentation", "load_outline"]
