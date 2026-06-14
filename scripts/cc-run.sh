#!/bin/bash
# Claude Code ラッパースクリプト
# 使い方: scripts/cc-run.sh [--auto] [-- <claude の追加引数>]
#   - 現在の git ブランチとディレクトリを状態ファイルに記録
#   - claude 終了後にステータスを更新
#   - cc-status.py でダッシュボード表示
#
# オプション:
#   --auto    オートモードで起動
#             - Opus 4.6/4.7（Max プラン以上）: --permission-mode auto
#             - それ以外（sonnet 等）          : --permission-mode bypassPermissions
#             ユーザーへの許可確認をすべてスキップして自動実行する。
#             並列 worktree 開発や CI 的な用途向け。

set -eo pipefail

# カラー設定
RED="\033[0;31m"
YELLOW="\033[33m"
GREEN="\033[32m"
BLUE="\033[0;34m"
NC="\033[0m"

#########################################
# 引数パース
#########################################
AUTO_MODE=false
CLAUDE_EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --)
            shift
            CLAUDE_EXTRA_ARGS+=("$@")
            break
            ;;
        *)
            echo -e "${RED}[cc-run]${NC} 不明なオプション: $1"
            echo "使い方: $0 [--auto] [-- <claude の追加引数>]"
            exit 1
            ;;
    esac
done

#########################################
# 設定
#########################################
STATUS_DIR="$HOME/.claude/status"
mkdir -p "$STATUS_DIR"

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
WORKTREE_PATH=$(pwd)

# ファイル名用: / と _ を - に変換
ID=$(echo "$BRANCH" | sed 's|[/_]|-|g')
SCRIPT_PID=$$
# PIDを含めることで同一ブランチの複数実行を個別管理できる
STATUS_FILE="$STATUS_DIR/${ID}-${SCRIPT_PID}.json"
STARTED_AT=$(date -Iseconds)

#########################################
# ステータス書き込み関数
#########################################
write_status() {
    local status="$1"
    local exit_code="${2:-null}"
    local finished_at="${3:-null}"

    cat > "$STATUS_FILE" <<EOF
{
  "id": "${ID}",
  "branch": "${BRANCH}",
  "worktree_path": "${WORKTREE_PATH}",
  "pid": ${SCRIPT_PID},
  "started_at": "${STARTED_AT}",
  "finished_at": ${finished_at},
  "status": "${status}",
  "exit_code": ${exit_code},
  "auto_mode": ${AUTO_MODE}
}
EOF
}

#########################################
# Ctrl+C / SIGTERM ハンドラ
#########################################
on_interrupt() {
    write_status "done" "130" "\"$(date -Iseconds)\""
    exit 130
}
trap on_interrupt INT TERM

#########################################
# 起動
#########################################
echo -e "${BLUE}[cc-run]${NC} ブランチ: ${GREEN}${BRANCH}${NC}"
echo -e "${BLUE}[cc-run]${NC} ステータスファイル: ${STATUS_FILE}"

if $AUTO_MODE; then
    echo -e "${BLUE}[cc-run]${NC} モード: ${YELLOW}オート（許可確認スキップ）${NC}"
fi

echo -e "${BLUE}[cc-run]${NC} claude を起動します..."
echo ""

write_status "running"

#########################################
# auto モード時の permission-mode 決定
#########################################
# --permission-mode auto は Opus 4.6/4.7 + Max プランのみ使用可能。
# それ以外（sonnet 等）は bypassPermissions にフォールバックする。
# モデル判定の優先順位:
#   1. CLAUDE_EXTRA_ARGS の --model フラグ
#   2. ANTHROPIC_MODEL 環境変数
#   3. 未指定（auto を試行）
determine_permission_mode() {
    local model=""
    local i=0
    while [ $i -lt ${#CLAUDE_EXTRA_ARGS[@]} ]; do
        if [ "${CLAUDE_EXTRA_ARGS[$i]}" = "--model" ]; then
            model="${CLAUDE_EXTRA_ARGS[$((i + 1))]:-}"
            break
        fi
        i=$((i + 1))
    done
    if [ -z "$model" ]; then
        model="${ANTHROPIC_MODEL:-}"
    fi
    if [ -z "$model" ] || [[ "$model" == *opus* ]]; then
        echo "auto"
    else
        echo "bypassPermissions"
    fi
}

#########################################
# claude 実行（フォアグラウンド）
#########################################
if $AUTO_MODE; then
    PERMISSION_MODE=$(determine_permission_mode)
    echo -e "${BLUE}[cc-run]${NC} permission-mode: ${YELLOW}${PERMISSION_MODE}${NC}"
    claude --permission-mode "$PERMISSION_MODE" "${CLAUDE_EXTRA_ARGS[@]}"
else
    claude "${CLAUDE_EXTRA_ARGS[@]}"
fi
CLAUDE_EXIT=$?

#########################################
# 終了時ステータス更新
#########################################
FINISHED_AT=$(date -Iseconds)
if [ "$CLAUDE_EXIT" -eq 0 ]; then
    write_status "done" "$CLAUDE_EXIT" "\"$FINISHED_AT\""
    echo -e "\n${GREEN}[cc-run]${NC} 完了 (exit: $CLAUDE_EXIT)"
else
    write_status "error" "$CLAUDE_EXIT" "\"$FINISHED_AT\""
    echo -e "\n${RED}[cc-run]${NC} エラー終了 (exit: $CLAUDE_EXIT)"
fi
