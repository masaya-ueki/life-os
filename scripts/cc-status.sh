#!/usr/bin/env bash
# Claude Code ステータスダッシュボード ランチャー
#
# rich がインストールされていない環境でも動作するよう、
# venv を自動セットアップして cc-status.py を実行します。
#
# 使い方:
#   scripts/cc-status.sh              # フル表示（キュー + セッション）
#   scripts/cc-status.sh --queue      # キューパネルのみ表示
#   scripts/cc-status.sh --once       # 1回だけ表示して終了（CI/スクリプト用）
#   scripts/cc-status.sh --detail 199 # Issue #199 の詳細表示
#   scripts/cc-status.sh --history    # 完了・失敗エントリも含めて表示
#   scripts/cc-status.sh --reattach   # 実行中 tmux セッションのアタッチコマンドを一覧
#   scripts/cc-status.sh --clean      # 完了・エラーのステータスファイルを削除

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${HOME}/.cache/cc-status-venv"
PYTHON_SCRIPT="${SCRIPT_DIR}/cc-status.py"

# venv がなければ作成
if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[cc-status] venv を作成しています: ${VENV_DIR}"
  python3 -m venv "${VENV_DIR}"
fi

# rich がインストールされていなければインストール
if ! "${VENV_DIR}/bin/python" -c "import rich" 2>/dev/null; then
  echo "[cc-status] rich をインストールしています..."
  "${VENV_DIR}/bin/pip" install --quiet rich
fi

# venv の Python でスクリプトを実行
exec "${VENV_DIR}/bin/python" "${PYTHON_SCRIPT}" "$@"
