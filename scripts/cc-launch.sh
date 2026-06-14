#!/bin/bash
# worktree 自動作成 + Claude Code 自動起動スクリプト
# 使い方: scripts/cc-launch.sh <ブランチ名> [--queue-id <id>] [--no-plan] [--comment <text>] [--auto-downgrade]
#
# 処理フロー:
#   1. create_worktree.sh でworktree 作成
#   2. tmux セッション作成（cc-<issue番号>）
#   3. cc-run.sh --auto を tmux 内で起動
#   4. --queue-id が指定されている場合、queue.json を更新
#
# Issue #264:
#   - --no-plan: plan モードを経由せず通常チャットとして起動
#   - --comment <text>: 初回プロンプト末尾にカスタムコメントを追記
#
# Issue #337（#323 を修正）:
#   - --auto-downgrade: cc-run.sh 経由で claude に --model sonnet を渡して
#                       Sonnet 4.6 で起動する。--no-plan と併用可能。
#   - plan モード時（--auto-downgrade 未指定）はデフォルトで
#     軽量判定指示を末尾に追記し、Claude がユーザーに Sonnet 切替を提案させる。
#   - 常に --model opus または --model sonnet を明示的に cc-run.sh へ渡す。

set -uo pipefail

# カラー設定
RED="\033[0;31m"
YELLOW="\033[33m"
GREEN="\033[32m"
BLUE="\033[0;34m"
BOLD="\033[1m"
NC="\033[0m"

# 設定
QUEUE_DIR="$HOME/.claude/queue"
QUEUE_FILE="$QUEUE_DIR/queue.json"
LOCK_FILE="$QUEUE_FILE.lock"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREATE_WORKTREE="$SCRIPT_DIR/create_worktree.sh"
CC_RUN="$SCRIPT_DIR/cc-run.sh"

#########################################
# ヘルプ表示
#########################################
show_help() {
    cat <<EOF
使い方:
  $(basename "$0") <ブランチ名> [--queue-id <id>] [--no-plan] [--comment <text>] [--auto-downgrade]

引数:
  <ブランチ名>         作成するブランチ名（例: feat/issue-198-auto-launch）
  --queue-id <id>    queue.json のエントリ ID（cc-daemon.sh から呼び出す場合）
  --no-plan          plan モードを経由せず、通常のチャットとして起動
  --comment <text>   初回プロンプトに添えるカスタムコメント
  --auto-downgrade   起動時に --model sonnet を渡して Sonnet 4.6 で起動する。
                     --no-plan と併用可能。未指定時はデフォルトで --model opus を渡す。
                     plan モード時（--auto-downgrade 未指定）は軽量判定指示が末尾に追記され、
                     Claude がユーザーに /model claude-sonnet-4-6 の実行を提案する。

例:
  $(basename "$0") feat/issue-198-auto-launch-claude-code
  $(basename "$0") feat/issue-198-auto-launch-claude-code --queue-id 198-20260419-143022
  $(basename "$0") feat/issue-264-foo --no-plan --comment "通常チャットで起動してください"
  $(basename "$0") feat/issue-296-foo --auto-downgrade
  $(basename "$0") feat/issue-323-foo --no-plan --auto-downgrade
EOF
}

#########################################
# 引数パース
#########################################
if [[ $# -eq 0 ]]; then
    show_help
    exit 1
fi

case "$1" in
    -h|--help|help)
        show_help
        exit 0
        ;;
esac

BRANCH="$1"
shift

QUEUE_ID=""
PLAN_MODE="true"
INITIAL_COMMENT=""
AUTO_DOWNGRADE="false"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --queue-id)
            shift
            if [[ $# -eq 0 ]]; then
                echo -e "${RED}[cc-launch]${NC} エラー: --queue-id に値を指定してください。"
                exit 1
            fi
            QUEUE_ID="$1"
            shift
            ;;
        --no-plan)
            PLAN_MODE="false"
            shift
            ;;
        --comment)
            shift
            if [[ $# -eq 0 ]]; then
                echo -e "${RED}[cc-launch]${NC} エラー: --comment に値を指定してください。"
                exit 1
            fi
            INITIAL_COMMENT="$1"
            shift
            ;;
        --auto-downgrade)
            AUTO_DOWNGRADE="true"
            shift
            ;;
        *)
            echo -e "${RED}[cc-launch]${NC} エラー: 不明なオプション: $1"
            exit 1
            ;;
    esac
done

#########################################
# Issue 番号の抽出
#########################################
ISSUE_NUMBER=""
ISSUE_NUMBER=$(echo "$BRANCH" | grep -oE 'issue-[0-9]+' | grep -oE '[0-9]+' | head -1) || true

# 初期プロンプト（Issue 番号抽出時のみ設定。md5 fallback では空のまま）
# Issue #231: Claude Code 起動時に GitHub Issue 内容を読み込み plan モードへ自動遷移する
# Issue #264: --no-plan で plan モードをスキップ、--comment で末尾にコメント追記
# Issue #337（#323 を修正）:
#   - --auto-downgrade: cc-run.sh に --model sonnet を渡す（プロンプト埋め込みなし）
#   - --auto-downgrade 未指定かつ plan モード時: 軽量判定指示（ユーザー提案形式）を末尾に追記
#   - 常に --model opus または --model sonnet を cc-run.sh 呼び出し時に明示する
INITIAL_PROMPT=""
if [[ -n "$ISSUE_NUMBER" ]]; then
    if [[ "$PLAN_MODE" == "true" ]]; then
        INITIAL_PROMPT="/issue-memory ${ISSUE_NUMBER} を実行して、Issue 内容を読み込んだうえで plan モードで実装案を提示してください。"
    else
        INITIAL_PROMPT="/issue-memory ${ISSUE_NUMBER} を実行して、Issue 内容を読み込んでください。"
    fi
    if [[ -n "$INITIAL_COMMENT" ]]; then
        INITIAL_PROMPT="${INITIAL_PROMPT}"$'\n\n'"${INITIAL_COMMENT}"
    fi
    if [[ "$AUTO_DOWNGRADE" != "true" && "$PLAN_MODE" == "true" ]]; then
        # plan モード時（--auto-downgrade 未指定）: 軽量判定指示をユーザー提案形式で末尾に追記
        # --auto-downgrade 指定時はモデル指定を cc-run.sh 呼び出し時の --model sonnet で行うため追記不要
        INITIAL_PROMPT="${INITIAL_PROMPT}"$'\n\n---\n'"なお、plan の結果、タスクが軽量（1〜2 ファイル変更／単純なロジック／ドキュメント更新／設定値の調整／既存パターンを踏襲する小さな追記／単発のテスト追加 など）と判断できる場合、plan 承認後の実装に入る前に、ユーザーに対して \`/model claude-sonnet-4-6\` の実行を提案してください（Claude 自身では切り替えないこと）。"$'\n'"複雑（複数モジュール変更／アーキテクチャ判断を伴う／新規モジュール作成／ETL・dbt のフル設計／パフォーマンス改善 など）と判断した場合は Opus のまま続行してください。曖昧な場合は安全側（Opus 維持）を選んでください。"
    fi
else
    # ブランチ名に issue-番号 が含まれない場合は branch のハッシュ値を代替 ID に使用
    ISSUE_NUMBER=$(echo "$BRANCH" | md5sum | cut -c1-6)
    echo -e "${YELLOW}[cc-launch]${NC} ブランチ名から Issue 番号を取得できませんでした。代替 ID を使用: ${ISSUE_NUMBER}"
    echo -e "${YELLOW}[cc-launch]${NC} 初期プロンプトはスキップされます（--comment 指定があってもスキップ）。"
fi

#########################################
# worktree パス計算（create_worktree.sh と同一ロジック）
#########################################
MAIN_DIR="$(git -C "${SCRIPT_DIR}" worktree list | head -1 | awk '{print $1}')"
REPO_ROOT="$(cd "${MAIN_DIR}/.." && pwd)"
# ブランチ名のスラッシュをハイフンに変換してフラットなディレクトリ名を生成
# 例: feat/issue-198-auto-launch → feat-issue-198-auto-launch
WORKTREE_DIRNAME="${BRANCH//\//-}"
WORKTREE_PATH="${REPO_ROOT}/${WORKTREE_DIRNAME}"

echo -e "${BLUE}[cc-launch]${NC} ブランチ: ${GREEN}${BOLD}${BRANCH}${NC}"
echo -e "${BLUE}[cc-launch]${NC} worktree パス: ${WORKTREE_PATH}"

#########################################
# worktree 作成（既存の場合はスキップ）
#########################################
if git -C "${MAIN_DIR}" worktree list | grep -qF "${WORKTREE_PATH}"; then
    echo -e "${YELLOW}[cc-launch]${NC} worktree は既に存在します。スキップします。"
else
    echo -e "${BLUE}[cc-launch]${NC} worktree を作成しています..."
    if ! "$CREATE_WORKTREE" "$BRANCH"; then
        echo -e "${RED}[cc-launch]${NC} エラー: worktree の作成に失敗しました。"
        exit 1
    fi
fi

#########################################
# tmux セッション名の決定（重複時は連番）
#########################################
BASE_SESSION="cc-${ISSUE_NUMBER}"
TMUX_SESSION="$BASE_SESSION"

if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    counter=2
    while tmux has-session -t "${BASE_SESSION}-${counter}" 2>/dev/null; do
        ((counter++))
    done
    TMUX_SESSION="${BASE_SESSION}-${counter}"
    echo -e "${YELLOW}[cc-launch]${NC} セッション名が重複しています。代替セッション名を使用: ${TMUX_SESSION}"
fi

#########################################
# tmux セッション作成
#########################################
echo -e "${BLUE}[cc-launch]${NC} tmux セッションを作成しています: ${TMUX_SESSION}"

if ! tmux new-session -d -s "$TMUX_SESSION" -c "$WORKTREE_PATH"; then
    echo -e "${RED}[cc-launch]${NC} エラー: tmux セッションの作成に失敗しました。"
    exit 1
fi

# cc-run.sh --auto をセッション内で実行
# cc-run.sh 終了後に bash も exit させてセッションを閉じる。
# これにより cc-daemon.sh の monitor_running_entries が tmux セッション消失を検知し、
# キューエントリを done/error に遷移させられる。
#
# Issue #231: INITIAL_PROMPT が設定されている場合は cc-run.sh の `--` 経路で
# claude へ positional prompt として引き渡し、起動と同時に Issue 読み込みを開始する。
# Issue #337: --auto-downgrade 指定時は --model sonnet、未指定時は --model opus を
# 常に明示的に渡す（プロンプト埋め込みによる /model 実行方式は廃止）。
if [[ "$AUTO_DOWNGRADE" == "true" ]]; then
    MODEL_ARG="--model sonnet"
else
    MODEL_ARG="--model opus"
fi

if [[ -n "$INITIAL_PROMPT" ]]; then
    # シングルクォート内に含まれる ' を '\'' でエスケープ（POSIX シェルの慣用）
    ESCAPED_PROMPT="${INITIAL_PROMPT//\'/\'\\\'\'}"
    tmux send-keys -t "$TMUX_SESSION" \
        "./scripts/cc-run.sh --auto -- ${MODEL_ARG} '${ESCAPED_PROMPT}'; exit \$?" Enter
else
    tmux send-keys -t "$TMUX_SESSION" "./scripts/cc-run.sh --auto -- ${MODEL_ARG}; exit \$?" Enter
fi

#########################################
# queue.json の更新（--queue-id が指定されている場合）
#########################################
if [[ -n "$QUEUE_ID" ]] && [[ -f "$QUEUE_FILE" ]]; then
    (
        flock -x 200

        python3 - <<EOF
import json

queue_file = "$QUEUE_FILE"
entry_id = "$QUEUE_ID"
tmux_session = "$TMUX_SESSION"
worktree_path = "$WORKTREE_PATH"

try:
    with open(queue_file, encoding="utf-8") as f:
        queue = json.load(f)

    for entry in queue:
        if entry["id"] == entry_id:
            entry["tmux_session"] = tmux_session
            entry["worktree_path"] = worktree_path
            break

    with open(queue_file, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
except Exception as e:
    print(f"WARN: queue.json の更新に失敗しました: {e}")
EOF
    ) 200>"$LOCK_FILE" || echo -e "${YELLOW}[cc-launch]${NC} 警告: queue.json の更新に失敗しました（監視は tmux セッションで代替します）。"
fi

#########################################
# 完了メッセージ
#########################################
echo ""
echo -e "${GREEN}[cc-launch]${NC} === 起動完了 ==="
echo -e "${BLUE}[cc-launch]${NC} tmux セッションを作成しました: ${BOLD}${TMUX_SESSION}${NC}"
echo -e ""
echo -e "  接続するには以下を実行してください:"
echo -e "    ${BOLD}tmux attach -t ${TMUX_SESSION}${NC}"
echo -e ""
echo -e "  セッション一覧を確認するには:"
echo -e "    tmux ls"
