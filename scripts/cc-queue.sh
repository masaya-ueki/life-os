#!/bin/bash
# Claude Code キューマネージャー
# 使い方: scripts/cc-queue.sh <command> [args...]
#
# コマンド:
#   enqueue <issue番号> [ブランチ名] [--comment <text>|-m <text>] [--no-plan]
#                                     キューに追加（ブランチ名省略時は GitHub から自動生成）
#   list                              キュー一覧表示
#   cancel <issue番号>                pending のタスクをキャンセル
#   clear                             done/error/cancelled を削除

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

#########################################
# ヘルプ表示
#########################################
show_help() {
    cat <<EOF
使い方:
  $(basename "$0") enqueue <issue番号> [ブランチ名] [--comment <text>|-m <text>] [--no-plan] [--auto-downgrade]
  $(basename "$0") list
  $(basename "$0") cancel <issue番号>
  $(basename "$0") clear

コマンド:
  enqueue <issue番号> [ブランチ名] [--comment <text>|-m <text>] [--no-plan] [--auto-downgrade]
      Issue をキューに追加します。
      ブランチ名を省略すると GitHub Issue のタイトルから自動生成します。

      オプション:
        --comment <text>, -m <text>
            初回プロンプトに添えるカスタムコメントを指定します。
            複数行や記号を含む場合はシェルのクォートで囲んでください。
        --no-plan
            plan モードを経由せず、通常のチャットとして起動します。
            既定では plan モードから開始します。
        --auto-downgrade
            --model sonnet を渡して Sonnet 4.6 で起動します。
            --no-plan と併用可能です（通常チャットを Sonnet で起動）。
            未指定時はデフォルトで --model opus を渡します。
            plan モード時（--auto-downgrade 未指定）は軽量判定指示が末尾に追記され、
            Claude がユーザーに /model claude-sonnet-4-6 の実行を提案します。

  list
      キューの一覧を表示します。

  cancel <issue番号>
      pending 状態のタスクをキャンセルします。
      running 状態のタスクはキャンセルできません。

  clear
      done / error / cancelled のエントリを削除します。

例:
  $(basename "$0") enqueue 197
  $(basename "$0") enqueue 197 feat/issue-197-queue-manager
  $(basename "$0") enqueue 197 --comment "参考: https://example.com/spec.md"
  $(basename "$0") enqueue 197 --no-plan -m "通常チャットで開始してください"
  $(basename "$0") enqueue 197 --auto-downgrade
  $(basename "$0") enqueue 197 --no-plan --auto-downgrade
  $(basename "$0") list
  $(basename "$0") cancel 197
  $(basename "$0") clear
EOF
}

#########################################
# キューファイル初期化
#########################################
init_queue() {
    mkdir -p "$QUEUE_DIR"
    if [[ ! -f "$QUEUE_FILE" ]]; then
        echo "[]" > "$QUEUE_FILE"
    fi
}

#########################################
# ブランチ名自動生成（GitHub Issue タイトルから）
#########################################
generate_branch_name() {
    local issue_number="$1"

    if ! command -v gh &>/dev/null; then
        echo -e "${RED}[cc-queue]${NC} gh CLI が見つかりません。ブランチ名を直接指定してください。" >&2
        return 1
    fi

    local title
    title=$(gh issue view "$issue_number" --json title -q '.title' 2>/dev/null) || {
        echo -e "${RED}[cc-queue]${NC} Issue #${issue_number} の取得に失敗しました。" >&2
        return 1
    }

    local kebab_title
    kebab_title=$(echo "$title" \
        | tr '[:upper:]' '[:lower:]' \
        | sed 's/[^a-z0-9]/-/g' \
        | sed 's/--*/-/g' \
        | sed 's/^-//' \
        | sed 's/-$//' \
        | cut -c1-50)

    echo "feat/issue-${issue_number}-${kebab_title}"
}

#########################################
# enqueue: キューに追加
#########################################
cmd_enqueue() {
    # 引数パース: 位置引数（issue番号 / ブランチ名）とフラグを共存させる
    local positional=()
    local initial_comment=""
    local plan_mode="true"
    local auto_downgrade="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -m|--comment)
                shift
                if [[ $# -eq 0 ]]; then
                    echo -e "${RED}[cc-queue]${NC} エラー: --comment / -m に値を指定してください。"
                    exit 1
                fi
                initial_comment="$1"
                shift
                ;;
            --no-plan)
                plan_mode="false"
                shift
                ;;
            --auto-downgrade)
                auto_downgrade="true"
                shift
                ;;
            --)
                shift
                positional+=("$@")
                break
                ;;
            -*)
                echo -e "${RED}[cc-queue]${NC} エラー: 不明なオプション: $1"
                echo "  使い方: $(basename "$0") enqueue <issue番号> [ブランチ名] [--comment <text>|-m <text>] [--no-plan] [--auto-downgrade]"
                exit 1
                ;;
            *)
                positional+=("$1")
                shift
                ;;
        esac
    done

    if [[ ${#positional[@]} -lt 1 ]]; then
        echo -e "${RED}[cc-queue]${NC} エラー: issue番号を指定してください。"
        echo "  使い方: $(basename "$0") enqueue <issue番号> [ブランチ名] [--comment <text>|-m <text>] [--no-plan] [--auto-downgrade]"
        exit 1
    fi

    local issue_number="${positional[0]}"
    local branch="${positional[1]:-}"

    # issue番号のバリデーション
    if ! [[ "$issue_number" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}[cc-queue]${NC} エラー: issue番号は数値で指定してください。"
        exit 1
    fi

    # ブランチ名の自動生成
    if [[ -z "$branch" ]]; then
        echo -e "${BLUE}[cc-queue]${NC} GitHub から Issue #${issue_number} のタイトルを取得中..."
        branch=$(generate_branch_name "$issue_number") || exit 1
        echo -e "${BLUE}[cc-queue]${NC} ブランチ名: ${BOLD}${branch}${NC}"
    fi

    init_queue

    local entry_id="${issue_number}-$(date +%Y%m%d-%H%M%S)"
    local queued_at
    queued_at=$(date -Iseconds)

    # ユーザー入力（initial_comment）はシェル展開を避けて環境変数経由で Python に渡す。
    # これにより ' や " を含むコメントでも JSON 破壊やシェル注入の懸念がない。
    (
        flock -x 200

        QUEUE_FILE="$QUEUE_FILE" \
        ENTRY_ID="$entry_id" \
        ISSUE_NUMBER="$issue_number" \
        BRANCH="$branch" \
        QUEUED_AT="$queued_at" \
        INITIAL_COMMENT="$initial_comment" \
        PLAN_MODE="$plan_mode" \
        AUTO_DOWNGRADE="$auto_downgrade" \
        python3 - <<'EOF'
import json, os, sys

queue_file = os.environ["QUEUE_FILE"]
issue_number = int(os.environ["ISSUE_NUMBER"])
initial_comment = os.environ["INITIAL_COMMENT"] or None
plan_mode = os.environ["PLAN_MODE"] != "false"
auto_downgrade = os.environ["AUTO_DOWNGRADE"] == "true"

entry = {
    "id": os.environ["ENTRY_ID"],
    "issue": issue_number,
    "branch": os.environ["BRANCH"],
    "status": "pending",
    "queued_at": os.environ["QUEUED_AT"],
    "started_at": None,
    "finished_at": None,
    "tmux_session": None,
    "worktree_path": None,
    "exit_code": None,
    "initial_comment": initial_comment,
    "plan_mode": plan_mode,
    "auto_downgrade": auto_downgrade,
}

with open(queue_file, encoding="utf-8") as f:
    queue = json.load(f)

# 同じ issue が pending/running で既にキューにある場合は警告
existing = [e for e in queue if e["issue"] == issue_number and e["status"] in ("pending", "running")]
if existing:
    print(f"WARN: Issue #{issue_number} は既にキューに存在します（status: {existing[0]['status']}）")
    sys.exit(1)

queue.append(entry)

with open(queue_file, "w", encoding="utf-8") as f:
    json.dump(queue, f, ensure_ascii=False, indent=2)

print("OK")
EOF
    ) 200>"$LOCK_FILE"

    local result=$?
    if [[ $result -eq 0 ]]; then
        echo -e "${GREEN}[cc-queue]${NC} Issue #${issue_number} をキューに追加しました。"
        echo -e "  ID: ${entry_id}"
        echo -e "  Branch: ${branch}"
        if [[ "$plan_mode" == "false" ]]; then
            echo -e "  Plan モード: OFF（通常チャット起動）"
        fi
        if [[ -n "$initial_comment" ]]; then
            echo -e "  カスタムコメント: あり"
        fi
        if [[ "$auto_downgrade" == "true" ]]; then
            echo -e "  Auto-downgrade: ON（--model sonnet で Sonnet 4.6 起動）"
        fi
    else
        # python3 が WARN を出した場合も exit 1 になるので、エラーメッセージは python3 側で出力済み
        exit 1
    fi
}

#########################################
# list: キュー一覧表示
#########################################
cmd_list() {
    if [[ ! -f "$QUEUE_FILE" ]]; then
        echo -e "${BLUE}[cc-queue]${NC} キューは空です。"
        return
    fi

    python3 - <<'EOF'
import json
from pathlib import Path

queue_file = Path.home() / ".claude" / "queue" / "queue.json"

try:
    with open(queue_file, encoding="utf-8") as f:
        queue = json.load(f)
except Exception as e:
    print(f"エラー: キューファイルの読み込みに失敗しました: {e}")
    raise SystemExit(1)

if not queue:
    print("キューは空です。")
    raise SystemExit(0)

# カラー定義
COLORS = {
    "pending":   "\033[0m",          # デフォルト
    "running":   "\033[33m",         # 黄
    "done":      "\033[32m",         # 緑
    "error":     "\033[31m",         # 赤
    "cancelled": "\033[2m",          # 暗
}
ICONS = {
    "pending":   "⏳",
    "running":   "⟳",
    "done":      "✓",
    "error":     "✗",
    "cancelled": "✕",
}
NC = "\033[0m"

# ヘッダー
print(f"\033[1m{'ID':<30} {'Issue':>6}  {'Status':<12} {'Branch':<50} {'Queued At'}\033[0m")
print("-" * 120)

for entry in queue:
    status = entry.get("status", "unknown")
    color = COLORS.get(status, "")
    icon = ICONS.get(status, "?")
    issue = f"#{entry.get('issue', '?')}"
    entry_id = entry.get("id", "")
    branch = entry.get("branch", "")
    queued_at = entry.get("queued_at", "")[:19].replace("T", " ") if entry.get("queued_at") else ""
    status_label = f"{icon} {status}"

    # ブランチ名を50文字に切り詰め
    if len(branch) > 49:
        branch = branch[:46] + "..."

    print(f"{color}{entry_id:<30} {issue:>6}  {status_label:<12} {branch:<50} {queued_at}{NC}")
EOF
}

#########################################
# cancel: pending をキャンセル
#########################################
cmd_cancel() {
    if [[ $# -lt 1 ]]; then
        echo -e "${RED}[cc-queue]${NC} エラー: issue番号を指定してください。"
        echo "  使い方: $(basename "$0") cancel <issue番号>"
        exit 1
    fi

    local issue_number="$1"

    if ! [[ "$issue_number" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}[cc-queue]${NC} エラー: issue番号は数値で指定してください。"
        exit 1
    fi

    if [[ ! -f "$QUEUE_FILE" ]]; then
        echo -e "${YELLOW}[cc-queue]${NC} キューは空です。"
        return
    fi

    (
        flock -x 200

        python3 - <<EOF
import json, sys

queue_file = "$QUEUE_FILE"
issue_number = $issue_number

with open(queue_file, encoding="utf-8") as f:
    queue = json.load(f)

found = False
for entry in queue:
    if entry["issue"] == issue_number:
        if entry["status"] == "pending":
            entry["status"] = "cancelled"
            found = True
            print(f"CANCELLED:{entry['id']}")
        elif entry["status"] == "running":
            print(f"RUNNING:{entry['id']}")
        else:
            print(f"SKIP:{entry['status']}:{entry['id']}")

if not found:
    skipped = [e for e in queue if e["issue"] == issue_number]
    if not skipped:
        print("NOT_FOUND")

with open(queue_file, "w", encoding="utf-8") as f:
    json.dump(queue, f, ensure_ascii=False, indent=2)
EOF
    ) 200>"$LOCK_FILE" | while IFS= read -r line; do
        case "$line" in
            CANCELLED:*)
                entry_id="${line#CANCELLED:}"
                echo -e "${GREEN}[cc-queue]${NC} Issue #${issue_number} (${entry_id}) をキャンセルしました。"
                ;;
            RUNNING:*)
                entry_id="${line#RUNNING:}"
                echo -e "${YELLOW}[cc-queue]${NC} Issue #${issue_number} (${entry_id}) は実行中のためキャンセルできません。"
                ;;
            SKIP:*)
                IFS=: read -r _ status entry_id <<< "$line"
                echo -e "${BLUE}[cc-queue]${NC} Issue #${issue_number} (${entry_id}) は ${status} のためスキップしました。"
                ;;
            NOT_FOUND)
                echo -e "${YELLOW}[cc-queue]${NC} Issue #${issue_number} はキューに見つかりませんでした。"
                ;;
        esac
    done
}

#########################################
# clear: 完了済みエントリを削除
#########################################
cmd_clear() {
    if [[ ! -f "$QUEUE_FILE" ]]; then
        echo -e "${BLUE}[cc-queue]${NC} キューは空です。"
        return
    fi

    (
        flock -x 200

        python3 - <<EOF
import json

queue_file = "$QUEUE_FILE"
remove_statuses = {"done", "error", "cancelled"}

with open(queue_file, encoding="utf-8") as f:
    queue = json.load(f)

before_count = len(queue)
queue = [e for e in queue if e.get("status") not in remove_statuses]
after_count = len(queue)
removed = before_count - after_count

with open(queue_file, "w", encoding="utf-8") as f:
    json.dump(queue, f, ensure_ascii=False, indent=2)

print(removed)
EOF
    ) 200>"$LOCK_FILE" | while IFS= read -r removed; do
        if [[ "$removed" -eq 0 ]]; then
            echo -e "${BLUE}[cc-queue]${NC} 削除対象のエントリはありませんでした。"
        else
            echo -e "${GREEN}[cc-queue]${NC} ${removed} 件のエントリを削除しました。"
        fi
    done
}

#########################################
# メイン
#########################################
if [[ $# -eq 0 ]]; then
    show_help
    exit 1
fi

COMMAND="$1"
shift

case "$COMMAND" in
    enqueue)
        cmd_enqueue "$@"
        ;;
    list)
        cmd_list
        ;;
    cancel)
        cmd_cancel "$@"
        ;;
    clear)
        cmd_clear
        ;;
    -h|--help|help)
        show_help
        ;;
    *)
        echo -e "${RED}[cc-queue]${NC} エラー: 不明なコマンド: ${COMMAND}"
        echo "  使い方: $(basename "$0") --help"
        exit 1
        ;;
esac
