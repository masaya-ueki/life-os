#!/bin/bash
# Claude Code キューデーモン
# 使い方: scripts/cc-daemon.sh <command> [options...]
#
# コマンド:
#   start [--max-parallel N]  デーモン起動（デフォルト N=3）
#   stop                      デーモン停止
#   status                    デーモン状態確認

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
PID_FILE="$QUEUE_DIR/daemon.pid"
LOG_FILE="$QUEUE_DIR/daemon.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCH_SCRIPT="$SCRIPT_DIR/cc-launch.sh"
STATUS_DIR="$HOME/.claude/status"
DEFAULT_MAX_PARALLEL=10
POLL_INTERVAL=2

#########################################
# ヘルプ表示
#########################################
show_help() {
    cat <<EOF
使い方:
  $(basename "$0") start [--max-parallel N]
  $(basename "$0") stop
  $(basename "$0") status

コマンド:
  start [--max-parallel N]
      キューデーモンをバックグラウンドで起動します。
      --max-parallel N で最大並列実行数を指定できます（デフォルト: ${DEFAULT_MAX_PARALLEL}）。

  stop
      起動中のデーモンを停止します。

  status
      デーモンの状態を確認します。

例:
  $(basename "$0") start
  $(basename "$0") start --max-parallel 5
  $(basename "$0") status
  $(basename "$0") stop
EOF
}

#########################################
# ログ出力
#########################################
log() {
    local level="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*" >> "$LOG_FILE"
}

#########################################
# キュー操作: python3 インライン実行
#########################################

# running エントリ数を取得
count_running() {
    python3 - <<EOF
import json
from pathlib import Path

queue_file = Path("$QUEUE_FILE")
if not queue_file.exists():
    print(0)
    raise SystemExit(0)

with open(queue_file, encoding="utf-8") as f:
    queue = json.load(f)

print(sum(1 for e in queue if e.get("status") == "running"))
EOF
}

# pending から 1 件取り出してステータスを running に更新。
# 出力: JSON 1 行 {"id","issue","branch","initial_comment","plan_mode","auto_downgrade"} または空文字
# Issue #264: initial_comment / plan_mode を後段 (cc-launch.sh) へ伝搬する必要があるため
#             スペース区切りからJSON 1 行に変更（コメントに改行・空白が含まれても安全）。
# Issue #296: auto_downgrade を追加（plan モード後に Sonnet へ自動切替するか）。
dequeue_one() {
    local started_at
    started_at=$(date -Iseconds)

    (
        flock -x 200

        python3 - <<EOF
import json, sys
from datetime import datetime

queue_file = "$QUEUE_FILE"
started_at = "$started_at"

if not __import__("pathlib").Path(queue_file).exists():
    sys.exit(0)

with open(queue_file, encoding="utf-8") as f:
    queue = json.load(f)

for entry in queue:
    if entry.get("status") == "pending":
        entry["status"] = "running"
        entry["started_at"] = started_at
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
        # 後方互換: 旧バージョンで enqueue されたエントリにフィールドが無い場合の既定値
        payload = {
            "id": entry["id"],
            "issue": entry["issue"],
            "branch": entry["branch"],
            "initial_comment": entry.get("initial_comment"),
            "plan_mode": entry.get("plan_mode", True),
            "auto_downgrade": entry.get("auto_downgrade", False),
        }
        print(json.dumps(payload, ensure_ascii=False))
        sys.exit(0)

# pending なし
sys.exit(0)
EOF
    ) 200>"$LOCK_FILE"
}

# running エントリの tmux_session と worktree_path を更新（cc-launch.sh から呼び出し用）
update_running_entry() {
    local entry_id="$1"
    local tmux_session="$2"
    local worktree_path="$3"

    (
        flock -x 200

        python3 - <<EOF
import json

queue_file = "$QUEUE_FILE"
entry_id = "$entry_id"
tmux_session = "$tmux_session"
worktree_path = "$worktree_path"

with open(queue_file, encoding="utf-8") as f:
    queue = json.load(f)

for entry in queue:
    if entry["id"] == entry_id:
        entry["tmux_session"] = tmux_session
        entry["worktree_path"] = worktree_path
        break

with open(queue_file, "w", encoding="utf-8") as f:
    json.dump(queue, f, ensure_ascii=False, indent=2)
EOF
    ) 200>"$LOCK_FILE"
}

# running エントリのステータスを done/error に更新
finish_entry() {
    local entry_id="$1"
    local exit_code="$2"
    local finished_at
    finished_at=$(date -Iseconds)

    local new_status="done"
    if [[ "$exit_code" != "0" ]]; then
        new_status="error"
    fi

    (
        flock -x 200

        python3 - <<EOF
import json

queue_file = "$QUEUE_FILE"
entry_id = "$entry_id"
new_status = "$new_status"
exit_code = $exit_code
finished_at = "$finished_at"

with open(queue_file, encoding="utf-8") as f:
    queue = json.load(f)

for entry in queue:
    if entry["id"] == entry_id:
        entry["status"] = new_status
        entry["exit_code"] = exit_code
        entry["finished_at"] = finished_at
        break

with open(queue_file, "w", encoding="utf-8") as f:
    json.dump(queue, f, ensure_ascii=False, indent=2)
EOF
    ) 200>"$LOCK_FILE"
}

# running エントリを取得（監視用）
get_running_entries() {
    python3 - <<EOF
import json
from pathlib import Path

queue_file = Path("$QUEUE_FILE")
if not queue_file.exists():
    raise SystemExit(0)

with open(queue_file, encoding="utf-8") as f:
    queue = json.load(f)

for entry in queue:
    if entry.get("status") == "running":
        entry_id = entry.get("id", "")
        issue = entry.get("issue", "")
        tmux_session = entry.get("tmux_session") or ""
        worktree_path = entry.get("worktree_path") or ""
        print(f"{entry_id}\t{issue}\t{tmux_session}\t{worktree_path}")
EOF
}

#########################################
# worktree の status ファイルから exit_code を取得
#########################################
get_exit_code_from_status() {
    local worktree_path="$1"

    python3 - <<EOF
import json, os
from pathlib import Path

status_dir = Path.home() / ".claude" / "status"
worktree_path = "$worktree_path"

if not status_dir.exists() or not worktree_path:
    print(1)
    raise SystemExit(0)

# worktree_path が一致する status ファイルのうち最新を取得
matching = []
for f in status_dir.glob("*.json"):
    try:
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        if data.get("worktree_path") == worktree_path:
            matching.append((f.stat().st_mtime, data))
    except Exception:
        continue

if not matching:
    print(1)
    raise SystemExit(0)

# 最新ファイルの exit_code を返す
latest = sorted(matching, key=lambda x: x[0], reverse=True)[0][1]
exit_code = latest.get("exit_code")
print(exit_code if exit_code is not None else 1)
EOF
}

#########################################
# デーモンメインループ
#########################################
daemon_loop() {
    local max_parallel="$1"

    log "INFO" "デーモン起動 (max-parallel=${max_parallel}, pid=${BASHPID})"

    # SIGTERM/SIGINT ハンドラ
    trap 'log "INFO" "デーモン停止シグナルを受信"; exit 0' TERM INT

    while true; do
        poll_queue "$max_parallel"
        sleep "$POLL_INTERVAL"
    done
}

#########################################
# キューポーリング
#########################################
poll_queue() {
    local max_parallel="$1"

    if [[ ! -f "$QUEUE_FILE" ]]; then
        return
    fi

    # 1. running エントリの tmux セッションを監視
    monitor_running_entries

    # 2. 空きスロットがあれば pending を dequeue
    local running_count
    running_count=$(count_running)

    if [[ "$running_count" -lt "$max_parallel" ]]; then
        launch_next_pending
    fi
}

#########################################
# running エントリの tmux セッション監視
#########################################
monitor_running_entries() {
    while IFS=$'\t' read -r entry_id issue tmux_session worktree_path; do
        [[ -z "$entry_id" ]] && continue

        # tmux セッション名が未設定の場合はスキップ（cc-launch.sh が起動中）
        if [[ -z "$tmux_session" ]]; then
            continue
        fi

        # tmux セッションの生存確認
        if ! tmux has-session -t "$tmux_session" 2>/dev/null; then
            # セッション消滅 → 完了とみなす
            local exit_code=0
            if [[ -n "$worktree_path" ]]; then
                exit_code=$(get_exit_code_from_status "$worktree_path")
            fi

            log "INFO" "セッション ${tmux_session} (Issue #${issue}) が終了 (exit_code=${exit_code})"
            finish_entry "$entry_id" "$exit_code"
        fi
    done < <(get_running_entries)
}

#########################################
# pending から 1 件取り出して起動
#########################################
launch_next_pending() {
    local result
    result=$(dequeue_one)

    [[ -z "$result" ]] && return

    # JSON 1 行を NUL 区切り文字列に分解して安全に各フィールドへ取り出す。
    # コメント (initial_comment) は改行・空白・引用符を含む可能性があるため必須の対応。
    local entry_id issue branch initial_comment plan_mode auto_downgrade
    {
        IFS= read -r -d '' entry_id || true
        IFS= read -r -d '' issue || true
        IFS= read -r -d '' branch || true
        IFS= read -r -d '' initial_comment || true
        IFS= read -r -d '' plan_mode || true
        IFS= read -r -d '' auto_downgrade || true
    } < <(printf '%s' "$result" | python3 -c '
import json, sys
data = json.loads(sys.stdin.read())
fields = ("id", "issue", "branch", "initial_comment", "plan_mode", "auto_downgrade")
for k in fields:
    v = data.get(k)
    if v is None:
        sys.stdout.write("\0")
    elif isinstance(v, bool):
        sys.stdout.write(("true" if v else "false") + "\0")
    else:
        sys.stdout.write(str(v) + "\0")
')

    log "INFO" "dequeue: Issue #${issue} (${branch}) [${entry_id}] plan_mode=${plan_mode} auto_downgrade=${auto_downgrade} comment=$([[ -n "$initial_comment" ]] && echo yes || echo no)"

    # cc-launch.sh の存在確認
    if [[ ! -x "$LAUNCH_SCRIPT" ]]; then
        log "WARN" "cc-launch.sh が見つかりません。Issue #198 の実装をお待ちください: ${LAUNCH_SCRIPT}"
        # running に更新したエントリを pending に戻す
        (
            flock -x 200
            python3 - <<EOF
import json
queue_file = "$QUEUE_FILE"
entry_id = "$entry_id"
with open(queue_file, encoding="utf-8") as f:
    queue = json.load(f)
for entry in queue:
    if entry["id"] == entry_id:
        entry["status"] = "pending"
        entry["started_at"] = None
        break
with open(queue_file, "w", encoding="utf-8") as f:
    json.dump(queue, f, ensure_ascii=False, indent=2)
EOF
        ) 200>"$LOCK_FILE"
        return
    fi

    # cc-launch.sh の引数を組み立て（Issue #264, #296）
    local launch_args=("$branch" "--queue-id" "$entry_id")
    if [[ "$plan_mode" == "false" ]]; then
        launch_args+=("--no-plan")
    fi
    if [[ -n "$initial_comment" ]]; then
        launch_args+=("--comment" "$initial_comment")
    fi
    if [[ "$auto_downgrade" == "true" ]]; then
        launch_args+=("--auto-downgrade")
    fi

    # cc-launch.sh をバックグラウンドで実行し、完了時に queue を更新
    (
        # cc-launch.sh を実行して worktree 作成 + tmux セッション起動
        if "$LAUNCH_SCRIPT" "${launch_args[@]}"; then
            # tmux_session と worktree_path の取得は cc-launch.sh が queue.json を更新する想定
            # （更新されていない場合は monitor_running_entries でセッション監視）
            log "INFO" "cc-launch.sh 完了: Issue #${issue} (${entry_id})"
        else
            local launch_exit=$?
            log "ERROR" "cc-launch.sh 失敗: Issue #${issue} (${entry_id}) exit_code=${launch_exit}"
            finish_entry "$entry_id" "$launch_exit"
        fi
    ) &
}

#########################################
# start コマンド
#########################################
cmd_start() {
    local max_parallel="$DEFAULT_MAX_PARALLEL"

    # 引数パース
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --max-parallel)
                shift
                if [[ $# -eq 0 ]] || ! [[ "$1" =~ ^[0-9]+$ ]]; then
                    echo -e "${RED}[cc-daemon]${NC} エラー: --max-parallel に数値を指定してください。"
                    exit 1
                fi
                max_parallel="$1"
                shift
                ;;
            *)
                echo -e "${RED}[cc-daemon]${NC} エラー: 不明なオプション: $1"
                exit 1
                ;;
        esac
    done

    # 二重起動チェック
    if [[ -f "$PID_FILE" ]]; then
        local existing_pid
        existing_pid=$(cat "$PID_FILE")
        if kill -0 "$existing_pid" 2>/dev/null; then
            echo -e "${YELLOW}[cc-daemon]${NC} デーモンはすでに起動しています。(PID: ${existing_pid})"
            exit 1
        else
            # PID ファイルが残骸の場合は削除して続行
            rm -f "$PID_FILE"
        fi
    fi

    mkdir -p "$QUEUE_DIR"

    echo -e "${BLUE}[cc-daemon]${NC} デーモンを起動しています... (max-parallel=${max_parallel})"

    # バックグラウンドでデーモンループを起動
    # setsid で新しいプロセスグループを作成し、制御端末から切り離す
    (
        # 標準入出力を切り離す
        exec </dev/null >>"$LOG_FILE" 2>&1
        daemon_loop "$max_parallel"
    ) &

    local daemon_pid=$!
    echo "$daemon_pid" > "$PID_FILE"

    # PID が有効かすぐに確認
    sleep 0.5
    if kill -0 "$daemon_pid" 2>/dev/null; then
        echo -e "${GREEN}[cc-daemon]${NC} デーモンを起動しました。(PID: ${daemon_pid})"
        echo -e "  ログ: ${LOG_FILE}"
        echo -e "  停止: $(basename "$0") stop"
    else
        echo -e "${RED}[cc-daemon]${NC} デーモンの起動に失敗しました。ログを確認してください: ${LOG_FILE}"
        rm -f "$PID_FILE"
        exit 1
    fi
}

#########################################
# stop コマンド
#########################################
cmd_stop() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo -e "${YELLOW}[cc-daemon]${NC} デーモンは起動していません。(PID ファイルなし)"
        return
    fi

    local pid
    pid=$(cat "$PID_FILE")

    if ! kill -0 "$pid" 2>/dev/null; then
        echo -e "${YELLOW}[cc-daemon]${NC} デーモンプロセスが見つかりません。(PID: ${pid})"
        rm -f "$PID_FILE"
        return
    fi

    echo -e "${BLUE}[cc-daemon]${NC} デーモンを停止しています... (PID: ${pid})"
    kill -TERM "$pid"

    # 最大5秒待機
    local waited=0
    while kill -0 "$pid" 2>/dev/null && [[ $waited -lt 5 ]]; do
        sleep 1
        ((waited++)) || true
    done

    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${RED}[cc-daemon]${NC} デーモンが停止しませんでした。強制終了します。"
        kill -KILL "$pid" 2>/dev/null || true
    fi

    rm -f "$PID_FILE"
    echo -e "${GREEN}[cc-daemon]${NC} デーモンを停止しました。"
}

#########################################
# status コマンド
#########################################
cmd_status() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo -e "${YELLOW}[cc-daemon]${NC} 状態: ${BOLD}停止中${NC}"
        return
    fi

    local pid
    pid=$(cat "$PID_FILE")

    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}[cc-daemon]${NC} 状態: ${BOLD}起動中${NC}"
        echo -e "  PID: ${pid}"
        echo -e "  ログ: ${LOG_FILE}"

        if [[ -f "$QUEUE_FILE" ]]; then
            python3 - <<EOF
import json
from pathlib import Path

queue_file = Path("$QUEUE_FILE")
try:
    with open(queue_file, encoding="utf-8") as f:
        queue = json.load(f)
    pending = sum(1 for e in queue if e.get("status") == "pending")
    running = sum(1 for e in queue if e.get("status") == "running")
    print(f"  キュー: pending={pending}, running={running}")
except Exception:
    pass
EOF
        fi
    else
        echo -e "${YELLOW}[cc-daemon]${NC} 状態: ${BOLD}停止中${NC} (PID ファイルが残存: ${pid})"
        echo "  PID ファイルを削除するには: rm ${PID_FILE}"
    fi
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
    start)
        cmd_start "$@"
        ;;
    stop)
        cmd_stop
        ;;
    status)
        cmd_status
        ;;
    -h|--help|help)
        show_help
        ;;
    *)
        echo -e "${RED}[cc-daemon]${NC} エラー: 不明なコマンド: ${COMMAND}"
        echo "  使い方: $(basename "$0") --help"
        exit 1
        ;;
esac
