#!/usr/bin/env bash
# PPTX → PNG 変換スクリプト（LibreOffice headless + pdftoppm 使用）
#
# Usage:
#   bash scripts/deckgen/tools/pptx_to_png.sh <slug_or_pptx_path> [output_dir] [--dpi N]
#
# 出力: output_dir/ に slide-01.png, slide-02.png, ... を生成。
# 既存ファイルは上書きする（再生成のたびに最新状態になる）。
#
# 実行方法（優先順位順）:
#   1. ローカルに libreoffice + pdftoppm があればそのまま使う
#   2. なければ Docker（pptx-convert サービス）経由で実行する
#      → docker compose build pptx-convert  ← 初回のみ
#      → docker compose run --rm pptx-convert bash scripts/deckgen/tools/pptx_to_png.sh <slug>

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

# --- 依存チェック: ローカル or Docker ---
_has() { command -v "$1" &>/dev/null; }

if ! _has soffice || ! _has pdftoppm; then
  # Docker フォールバック
  if _has docker && docker compose config --services 2>/dev/null | grep -q "^pptx-convert$"; then
    echo "[pptx_to_png] LibreOffice がローカルにないため Docker (pptx-convert) を使用します"
    # 引数を再構築して Docker 内で自分自身を呼び出す
    exec docker compose run --rm pptx-convert \
      bash scripts/deckgen/tools/pptx_to_png.sh \
      "$PPTX" "$OUTDIR" --dpi "$DPI"
  else
    echo "ERROR: LibreOffice と pdftoppm が見つかりません。" >&2
    echo "" >&2
    echo "選択肢 A — Docker を使う（推奨・ローカル環境を汚さない）:" >&2
    echo "  docker compose build pptx-convert  # 初回のみ（数分かかります）" >&2
    echo "  docker compose run --rm pptx-convert bash scripts/deckgen/tools/pptx_to_png.sh $TARGET" >&2
    echo "" >&2
    echo "選択肢 B — ローカルにインストールする:" >&2
    echo "  sudo apt-get install -y libreoffice poppler-utils" >&2
    exit 1
  fi
fi

# --- 変換: PPTX → PDF ---
TMPDIR_CONV="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_CONV"' EXIT

echo "[pptx_to_png] PPTX → PDF 変換中: $PPTX"
soffice --headless --convert-to pdf --outdir "$TMPDIR_CONV" "$PPTX" 2>/dev/null

PDF_NAME="$(basename "${PPTX%.pptx}.pdf")"
PDF_PATH="$TMPDIR_CONV/$PDF_NAME"

if [[ ! -f "$PDF_PATH" ]]; then
  echo "ERROR: PDF 変換に失敗しました。LibreOffice のログを確認してください。" >&2
  exit 1
fi

# --- 変換: PDF → PNG ---
echo "[pptx_to_png] PDF → PNG 変換中 (${DPI}dpi): $PDF_PATH"
rm -f "$OUTDIR"/slide-*.png

pdftoppm -r "$DPI" -png "$PDF_PATH" "$OUTDIR/slide"

# slide-1.png, slide-2.png, ... → slide-01.png, slide-02.png, ... に零埋め
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
