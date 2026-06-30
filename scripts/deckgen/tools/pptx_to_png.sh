#!/usr/bin/env bash
# PPTX → PNG 変換スクリプト（Docker pptx-convert サービス経由）
#
# Usage:
#   bash scripts/deckgen/tools/pptx_to_png.sh <slug_or_pptx_path> [output_dir] [--dpi N]
#
# 出力: output_dir/ に slide-01.png, slide-02.png, ... を生成。
# 既存ファイルは上書きする（再生成のたびに最新状態になる）。
#
# 前提: docker compose build pptx-convert（初回のみ、数分）
# 実行環境を問わず Docker で統一する（ローカル直接実行は非対応）。

set -euo pipefail

# --- 引数パース ---
TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 <slug_or_pptx_path> [output_dir] [--dpi N]" >&2
  exit 1
fi

DPI=150
OUTDIR=""
shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dpi) DPI="$2"; shift 2 ;;
    *) OUTDIR="$1"; shift ;;
  esac
done

# --- PPTX パスの解決 ---
if [[ "$TARGET" == *.pptx ]]; then
  PPTX="$TARGET"
else
  SLUG="$TARGET"
  PPTX="domains/presentation/decks/${SLUG}/${SLUG}.pptx"
  if [[ ! -f "$PPTX" ]]; then
    echo "ERROR: PPTX が見つかりません: $PPTX" >&2
    echo "先に deckgen でスライドを生成してください:" >&2
    echo "  uv run --project scripts/deckgen -m deckgen $SLUG" >&2
    exit 1
  fi
fi

if [[ ! -f "$PPTX" ]]; then
  echo "ERROR: ファイルが存在しません: $PPTX" >&2
  exit 1
fi

# --- 出力ディレクトリ ---
if [[ -z "$OUTDIR" ]]; then
  OUTDIR="$(dirname "$PPTX")/preview"
fi
mkdir -p "$OUTDIR"

# --- Docker 確認 ---
if ! command -v docker &>/dev/null; then
  echo "ERROR: Docker が見つかりません。Docker Desktop をインストールしてください。" >&2
  exit 1
fi

# pptx-convert イメージが存在するか確認（未ビルドなら案内して停止）
if ! docker image inspect life-os-pptx-convert:local &>/dev/null; then
  echo "ERROR: pptx-convert イメージが未ビルドです。以下を実行してください:" >&2
  echo "  docker compose build pptx-convert" >&2
  exit 1
fi

# --- Docker コンテナ内で変換実行 ---
# このスクリプト自体がホストで動いているとき: コンテナに処理を委譲する。
# コンテナ内で動いているとき（PPTX_CONVERT_IN_DOCKER=1）: 実際に変換する。
if [[ "${PPTX_CONVERT_IN_DOCKER:-}" != "1" ]]; then
  echo "[pptx_to_png] Docker (pptx-convert) で変換を実行します..."
  exec docker compose run --rm \
    -e PPTX_CONVERT_IN_DOCKER=1 \
    pptx-convert \
    bash scripts/deckgen/tools/pptx_to_png.sh \
    "$PPTX" "$OUTDIR" --dpi "$DPI"
fi

# --- 以下はコンテナ内でのみ実行される ---

# --- 変換: PPTX → PDF ---
TMPDIR_CONV="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_CONV"' EXIT

echo "[pptx_to_png] PPTX → PDF 変換中: $PPTX"
soffice --headless --convert-to pdf --outdir "$TMPDIR_CONV" "$PPTX" 2>/dev/null

PDF_NAME="$(basename "${PPTX%.pptx}.pdf")"
PDF_PATH="$TMPDIR_CONV/$PDF_NAME"

if [[ ! -f "$PDF_PATH" ]]; then
  echo "ERROR: PDF 変換に失敗しました。" >&2
  exit 1
fi

# --- 変換: PDF → PNG ---
echo "[pptx_to_png] PDF → PNG 変換中 (${DPI}dpi): $PDF_PATH"
rm -f "$OUTDIR"/slide-*.png

pdftoppm -r "$DPI" -png "$PDF_PATH" "$OUTDIR/slide"

# slide-1.png → slide-01.png に零埋め
for f in "$OUTDIR"/slide-*.png; do
  [[ -f "$f" ]] || continue
  base="$(basename "$f")"
  num="${base#slide-}"
  num="${num%.png}"
  if [[ ${#num} -lt 2 ]]; then
    padded="$(printf '%02d' "$num")"
    mv "$f" "$OUTDIR/slide-${padded}.png"
  fi
done

# --- 完了報告 ---
COUNT=$(ls "$OUTDIR"/slide-*.png 2>/dev/null | wc -l)
echo "[pptx_to_png] 完了: $COUNT 枚 → $OUTDIR/"
ls "$OUTDIR"/slide-*.png 2>/dev/null | sort
