"""CLI: outline.yml → 編集可能ネイティブ pptx。

使い方:
  uv run --project scripts/deckgen -m deckgen <slug>
  uv run --project scripts/deckgen -m deckgen path/to/outline.yml --out deck.pptx
  uv run --project scripts/deckgen -m deckgen <slug> --template brand.potx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from deckgen.builder import build_to_file
from deckgen.loader import OutlineError, load_outline, resolve_outline_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="deckgen",
        description="outline.yml から編集可能なネイティブ PowerPoint(.pptx) を生成",
    )
    parser.add_argument("target", help="deck の slug、または outline.yml のパス")
    parser.add_argument("--out", help="出力 .pptx パス（既定: deck と同じディレクトリ/{slug}.pptx）")
    parser.add_argument("--template", help="継承するテンプレ .pptx/.potx パス（任意）")
    args = parser.parse_args(argv)

    try:
        outline = load_outline(args.target)
    except OutlineError as e:
        print(f"[deckgen] エラー: {e}", file=sys.stderr)
        return 1

    out_path = _resolve_out(args.target, args.out)
    saved, n_slides, warnings = build_to_file(outline, out_path, args.template)

    for w in warnings:
        print(f"[deckgen] 注意: {w}", file=sys.stderr)
    print(f"[deckgen] 生成: {saved}（{n_slides} 枚）")
    if args.template:
        print(f"[deckgen] テンプレ継承: {args.template}")
    return 0


def _resolve_out(target: str, out: str | None) -> Path:
    if out:
        return Path(out)
    outline_path = resolve_outline_path(target)
    deck_dir = outline_path.parent
    slug = deck_dir.name
    return deck_dir / f"{slug}.pptx"


if __name__ == "__main__":
    raise SystemExit(main())
