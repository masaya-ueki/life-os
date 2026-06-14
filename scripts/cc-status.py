#!/usr/bin/env python3
"""
Claude Code 並列実行ステータスダッシュボード

使い方（推奨 - venv 自動セットアップ）:
  scripts/cc-status.sh              # フル表示（キュー + セッション）
  scripts/cc-status.sh --queue      # キューパネルのみ表示
  scripts/cc-status.sh --once       # 1回だけ表示して終了
  scripts/cc-status.sh --detail 199 # Issue #199 の詳細表示
  scripts/cc-status.sh --history    # 完了・失敗エントリも表示
  scripts/cc-status.sh --reattach   # 実行中 tmux セッションのアタッチコマンド一覧
  scripts/cc-status.sh --clean      # 完了・エラーのステータスファイルを削除

直接実行する場合（rich が必要）:
  python3 scripts/cc-status.py [OPTIONS]

依存:
  rich（cc-status.sh を使えば venv に自動インストールされます）
"""

import json
import os
import re
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
except ImportError:
    print("rich がインストールされていません。シェルラッパー経由で起動してください:")
    print("  scripts/cc-status.sh")
    print("")
    print("または手動でインストール:")
    print("  pip install rich")
    sys.exit(1)

STATUS_DIR = Path.home() / ".claude" / "status"
QUEUE_DIR = Path.home() / ".claude" / "queue"
QUEUE_FILE = QUEUE_DIR / "queue.json"
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
REFRESH_INTERVAL = 2  # 秒


# ─────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────

def extract_issue_number(branch: str) -> Optional[int]:
    """ブランチ名から issue 番号を抽出する"""
    m = re.search(r"issue-(\d+)", branch)
    return int(m.group(1)) if m else None


def worktree_path_to_project_key(path: str) -> str:
    """worktreeパスを ~/.claude/projects/ のキーに変換

    例: /workspace/foo/bar_baz  →  -workspace-foo-bar-baz
    Claude Code は / と _ をどちらも - に変換している
    """
    return path.replace("/", "-").replace("_", "-")


def get_elapsed(started_at: str, finished_at: Optional[str] = None) -> str:
    """経過時間を人間が読める形式で返す"""
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(finished_at) if finished_at else datetime.now().astimezone()
        elapsed = max(0, int((end - start).total_seconds()))

        if elapsed < 60:
            return f"{elapsed}s"
        elif elapsed < 3600:
            return f"{elapsed // 60}m{elapsed % 60:02d}s"
        else:
            return f"{elapsed // 3600}h{(elapsed % 3600) // 60:02d}m"
    except Exception:
        return "-"


def format_time(ts: Optional[str], fmt: str = "%H:%M") -> str:
    """ISO 8601 タイムスタンプを指定フォーマットで返す"""
    if not ts:
        return "-"
    try:
        return datetime.fromisoformat(ts).strftime(fmt)
    except Exception:
        return "-"


# ─────────────────────────────────────────
# JSONL パース（最終アクション取得）
# ─────────────────────────────────────────

def _get_latest_jsonl(worktree_path: str) -> Optional[Path]:
    """worktreeパスに対応する最新のJSONLファイルを返す"""
    try:
        project_key = worktree_path_to_project_key(worktree_path)
        project_dir = CLAUDE_PROJECTS_DIR / project_key
        if not project_dir.exists():
            return None
        jsonl_files = list(project_dir.glob("*.jsonl"))
        if not jsonl_files:
            return None
        return max(jsonl_files, key=lambda f: f.stat().st_mtime)
    except Exception:
        return None


def is_waiting_for_user(worktree_path: str) -> bool:
    """Claudeがユーザー入力待ち状態かどうかを判定する"""
    try:
        latest_file = _get_latest_jsonl(worktree_path)
        if not latest_file:
            return False

        with open(latest_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in reversed(lines[-100:]):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            if data.get("type") != "assistant":
                continue

            message = data.get("message", {})
            content = message.get("content", [])
            if not isinstance(content, list):
                return False

            has_tool_use = any(
                isinstance(item, dict) and item.get("type") == "tool_use"
                for item in content
            )
            return not has_tool_use

        return False
    except Exception:
        return False


def get_last_action(worktree_path: str) -> str:
    """最後のツール呼び出しをJSONLセッションファイルから取得"""
    try:
        latest_file = _get_latest_jsonl(worktree_path)
        if not latest_file:
            return "-"

        with open(latest_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in reversed(lines[-50:]):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                action = _extract_tool_action(data)
                if action:
                    return action
            except json.JSONDecodeError:
                continue

        return "-"
    except Exception:
        return "-"


def get_last_actions(worktree_path: str, n: int = 10) -> list[str]:
    """直近 n 件のツール呼び出しを新しい順で返す"""
    try:
        latest_file = _get_latest_jsonl(worktree_path)
        if not latest_file:
            return []

        with open(latest_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        results: list[str] = []
        for line in reversed(lines[-200:]):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                action = _extract_tool_action(data)
                if action:
                    results.append(action)
                    if len(results) >= n:
                        break
            except json.JSONDecodeError:
                continue

        return results
    except Exception:
        return []


def _extract_tool_action(data: dict) -> Optional[str]:
    """JSONオブジェクトからツール呼び出し文字列を抽出"""
    if data.get("type") != "assistant":
        return None

    message = data.get("message", {})
    content = message.get("content", [])

    if not isinstance(content, list):
        return None

    for item in reversed(content):
        if not isinstance(item, dict):
            continue
        if item.get("type") != "tool_use":
            continue
        return _format_tool_use(item.get("name", ""), item.get("input", {}))

    return None


def _format_tool_use(name: str, inp: dict) -> str:
    """ツール呼び出しを読みやすい文字列にフォーマット"""
    if name == "Bash":
        desc = inp.get("description", "")
        if desc:
            return f"Bash: {desc[:45]}"
        cmd = inp.get("command", "")
        return f"Bash: {cmd[:45]}"

    elif name in ("Read", "Write", "Edit", "MultiEdit"):
        path = inp.get("file_path", inp.get("path", ""))
        filename = Path(path).name if path else "?"
        return f"{name}: {filename}"

    elif name == "Glob":
        return f"Glob: {inp.get('pattern', '?')}"

    elif name == "Grep":
        pattern = inp.get("pattern", "?")
        return f"Grep: {pattern[:35]}"

    elif name == "WebFetch":
        url = inp.get("url", "?")
        return f"WebFetch: {url[:35]}"

    elif name == "WebSearch":
        query = inp.get("query", "?")
        return f"Search: {query[:35]}"

    elif name:
        return name

    return "-"


# ─────────────────────────────────────────
# キュー管理
# ─────────────────────────────────────────

def load_queue(history: bool = False) -> list:
    """~/.claude/queue/queue.json を読み込んでリストで返す"""
    if not QUEUE_FILE.exists():
        return []

    try:
        with open(QUEUE_FILE, encoding="utf-8") as f:
            queue = json.load(f)
    except Exception:
        return []

    if not history:
        # デフォルト: pending / running のみ表示
        queue = [e for e in queue if e.get("status") in ("pending", "running")]

    # キュー追加時刻順でソート
    queue.sort(key=lambda e: e.get("queued_at", ""))
    return queue


QUEUE_STATUS_DISPLAY = {
    "pending":   ("⏳ 待機中", "white"),
    "running":   ("⟳ 実行中", "yellow"),
    "done":      ("✓ 完了",   "green"),
    "error":     ("✗ エラー", "red"),
    "cancelled": ("✕ キャンセル", "dim"),
}


def build_queue_table(queue: list) -> Table:
    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="magenta",
        box=box.ROUNDED,
        expand=True,
        title="[bold magenta]Queue[/]",
    )
    table.add_column("#",             style="dim", width=3,  justify="right")
    table.add_column("Issue",         width=7,     justify="right")
    table.add_column("ブランチ",      min_width=30)
    table.add_column("状態",          width=14)
    table.add_column("経過",          width=8,     justify="right")
    table.add_column("追加時刻",      width=6,     justify="right", style="dim")
    table.add_column("tmux セッション", width=12,  style="dim")

    for i, e in enumerate(queue, 1):
        status = e.get("status", "unknown")
        icon, color = QUEUE_STATUS_DISPLAY.get(status, ("? 不明", "dim"))

        finished_at = e.get("finished_at") if status in ("done", "error", "cancelled") else None
        elapsed = get_elapsed(e.get("started_at", ""), finished_at) if e.get("started_at") else "-"
        queued_label = format_time(e.get("queued_at"))
        issue_label = f"#{e.get('issue', '?')}"
        tmux = e.get("tmux_session") or "-"

        table.add_row(
            str(i),
            issue_label,
            e.get("branch", "-"),
            Text(icon, style=color),
            elapsed,
            queued_label,
            tmux,
        )

    return table


def build_queue_summary(queue_all: list) -> str:
    """キューのサマリー文字列を返す（ヘッダー用）"""
    counts = {k: 0 for k in QUEUE_STATUS_DISPLAY}
    for e in queue_all:
        s = e.get("status", "unknown")
        if s in counts:
            counts[s] += 1

    return (
        f"[white]⏳ {counts['pending']}[/]  "
        f"[yellow]⟳ {counts['running']}[/]  "
        f"[green]✓ {counts['done']}[/]  "
        f"[red]✗ {counts['error']}[/]  "
        f"[dim]合計 {len(queue_all)}[/]"
    )


# ─────────────────────────────────────────
# プロセス・ステータス管理
# ─────────────────────────────────────────

def is_process_running(pid: int) -> bool:
    """PIDのプロセスが生存しているか確認"""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def load_statuses(history: bool = False) -> list:
    """~/.claude/status/*.json を読み込んでリストで返す（起動時刻順）"""
    if not STATUS_DIR.exists():
        return []

    statuses = []
    for status_file in STATUS_DIR.glob("*.json"):
        try:
            with open(status_file, encoding="utf-8") as f:
                data = json.load(f)

            if data.get("status") == "running":
                pid = data.get("pid")
                if pid and not is_process_running(int(pid)):
                    data["status"] = "error"
                    data["_note"] = "プロセスが予期せず終了"
                elif is_waiting_for_user(data.get("worktree_path", "")):
                    data["status"] = "waiting"

            statuses.append(data)
        except Exception:
            continue

    statuses.sort(key=lambda s: s.get("started_at", ""))

    if not history:
        statuses = [s for s in statuses if s.get("status") not in ("done", "error")]

    return statuses


def clean_statuses() -> int:
    """完了・エラーのステータスファイルを削除して削除件数を返す"""
    if not STATUS_DIR.exists():
        return 0

    removed = 0
    for status_file in STATUS_DIR.glob("*.json"):
        try:
            with open(status_file, encoding="utf-8") as f:
                data = json.load(f)
            status = data.get("status")
            if status == "running":
                pid = data.get("pid")
                if pid and not is_process_running(int(pid)):
                    status = "error"
            if status in ("done", "error"):
                status_file.unlink()
                removed += 1
        except Exception:
            continue
    return removed


# ─────────────────────────────────────────
# Sessions Rich UI
# ─────────────────────────────────────────

SESSION_STATUS_DISPLAY = {
    "running":  ("⟳ 実行中",   "yellow"),
    "waiting":  ("⏳ 入力待ち", "cyan"),
    "done":     ("✓ 完了",     "green"),
    "error":    ("✗ エラー",   "red"),
    "starting": ("… 起動中",   "dim"),
}


def build_sessions_table(statuses: list) -> Table:
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        box=box.ROUNDED,
        expand=True,
        title="[bold cyan]Claude Sessions[/]",
    )
    table.add_column("#",             style="dim", width=3,  justify="right")
    table.add_column("Issue",         width=7,     justify="right")
    table.add_column("ブランチ",      min_width=25)
    table.add_column("起動時刻",      width=6,     justify="right", style="dim")
    table.add_column("モード",        width=6,     justify="center")
    table.add_column("状態",          width=12)
    table.add_column("経過",          width=8,     justify="right")
    table.add_column("最終アクション", min_width=40)

    for i, s in enumerate(statuses, 1):
        status = s.get("status", "unknown")
        icon, color = SESSION_STATUS_DISPLAY.get(status, ("? 不明", "dim"))

        finished_at = s.get("finished_at") if status in ("done", "error") else None
        elapsed = get_elapsed(s.get("started_at", ""), finished_at)
        last_action = get_last_action(s.get("worktree_path", ""))
        started_label = format_time(s.get("started_at", ""))
        issue_num = extract_issue_number(s.get("branch", ""))
        issue_label = f"#{issue_num}" if issue_num else "-"

        auto_mode = s.get("auto_mode", False)
        mode_cell = Text("AUTO", style="bold red") if auto_mode else Text("-", style="dim")

        table.add_row(
            str(i),
            issue_label,
            s.get("branch", "-"),
            started_label,
            mode_cell,
            Text(icon, style=color),
            elapsed,
            last_action,
        )

    return table


def build_header(statuses: list, queue_all: list) -> Panel:
    """セッション + キュー両方のサマリーをヘッダーパネルに表示"""
    session_counts = {k: 0 for k in SESSION_STATUS_DISPLAY}
    auto_count = 0
    for s in statuses:
        status = s.get("status", "unknown")
        if status in session_counts:
            session_counts[status] += 1
        if s.get("auto_mode", False):
            auto_count += 1

    now = datetime.now().strftime("%H:%M:%S")
    session_summary = (
        f"[yellow]⟳ {session_counts['running']}[/]  "
        f"[cyan]⏳ {session_counts['waiting']}[/]  "
        f"[green]✓ {session_counts['done']}[/]  "
        f"[red]✗ {session_counts['error']}[/]"
    )
    auto_label = f"  [bold red]AUTO: {auto_count}[/]" if auto_count > 0 else ""
    queue_summary = build_queue_summary(queue_all)

    return Panel(
        f"[bold cyan]Claude Code Status Monitor[/]\n"
        f"[dim]Sessions:[/] {session_summary}{auto_label}   "
        f"[dim]Queue:[/] {queue_summary}\n"
        f"[dim]更新: {now}  |  Ctrl+C で終了  |  --help でオプション確認[/]",
        border_style="cyan",
    )


def build_empty_panel(label: str = "Sessions") -> Panel:
    return Panel(
        f"[dim]{label}に表示するエントリがありません[/]",
        border_style="dim",
        expand=True,
    )


def build_tips_panel() -> Panel:
    """tmux 操作の Tips を表示するパネル"""
    tips = (
        "[bold]Tips:[/]\n"
        "  [dim]特定のセッションに接続:[/]  [cyan]tmux attach -t cc-<番号>[/]\n"
        "  [dim]セッション一覧を確認:[/]    [cyan]tmux ls[/]\n"
        "  [dim]全実行中セッション接続:[/]  [cyan]scripts/cc-status.sh --reattach[/]"
    )
    return Panel(tips, border_style="dim", expand=True, title="[dim]操作ガイド[/]")


# ─────────────────────────────────────────
# --reattach（実行中 tmux セッション一覧）
# ─────────────────────────────────────────

def show_reattach(console: Console) -> None:
    """実行中のすべての tmux セッションとアタッチコマンドを一覧表示する"""
    queue_all = load_queue(history=True)
    running = [
        e for e in queue_all
        if e.get("status") == "running" and e.get("tmux_session")
    ]

    if not running:
        console.print("[yellow]実行中の tmux セッションはありません。[/]")
        return

    console.print(f"\n[bold cyan]実行中の tmux セッション ({len(running)} 件)[/]\n")

    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        box=box.ROUNDED,
        expand=True,
    )
    table.add_column("Issue",          width=8,  justify="right")
    table.add_column("ブランチ",       min_width=30)
    table.add_column("tmux セッション", width=14)
    table.add_column("アタッチコマンド")

    for e in running:
        tmux = e.get("tmux_session", "")
        table.add_row(
            f"#{e.get('issue', '?')}",
            e.get("branch", "-"),
            tmux,
            f"[cyan]tmux attach -t {tmux}[/]",
        )

    console.print(table)
    console.print(
        "\n[dim]使い方:[/] 上記の [cyan]tmux attach -t <セッション名>[/] を実行してアタッチしてください。"
        "  [dim]デタッチ:[/] [cyan]Ctrl+b d[/]\n"
    )


# ─────────────────────────────────────────
# 詳細表示
# ─────────────────────────────────────────

def show_detail(console: Console, issue: int) -> None:
    """指定 Issue の詳細情報を表示する"""
    # キューエントリを取得
    queue_entries: list = []
    if QUEUE_FILE.exists():
        try:
            with open(QUEUE_FILE, encoding="utf-8") as f:
                all_entries = json.load(f)
            queue_entries = [e for e in all_entries if e.get("issue") == issue]
        except Exception:
            pass

    # セッションエントリを取得
    session_entries: list = []
    if STATUS_DIR.exists():
        for sf in STATUS_DIR.glob("*.json"):
            try:
                with open(sf, encoding="utf-8") as f:
                    data = json.load(f)
                if extract_issue_number(data.get("branch", "")) == issue:
                    if data.get("status") == "running":
                        pid = data.get("pid")
                        if pid and not is_process_running(int(pid)):
                            data["status"] = "error"
                        elif is_waiting_for_user(data.get("worktree_path", "")):
                            data["status"] = "waiting"
                    session_entries.append(data)
            except Exception:
                continue

    if not queue_entries and not session_entries:
        console.print(f"[yellow]Issue #{issue} のエントリが見つかりません。[/]")
        return

    console.print(f"\n[bold cyan]Issue #{issue} 詳細情報[/]\n")

    # キューエントリ
    if queue_entries:
        for e in queue_entries:
            status = e.get("status", "unknown")
            icon, color = QUEUE_STATUS_DISPLAY.get(status, ("? 不明", "dim"))

            t = Table(box=box.SIMPLE, show_header=False, expand=False)
            t.add_column("項目", style="dim", width=18)
            t.add_column("値")

            t.add_row("Queue ID", e.get("id", "-"))
            t.add_row("Branch", e.get("branch", "-"))
            t.add_row("ステータス", Text(icon, style=color))
            t.add_row("追加時刻", format_time(e.get("queued_at"), "%Y-%m-%d %H:%M:%S"))
            t.add_row("開始時刻", format_time(e.get("started_at"), "%Y-%m-%d %H:%M:%S"))
            t.add_row("完了時刻", format_time(e.get("finished_at"), "%Y-%m-%d %H:%M:%S"))
            t.add_row("経過時間", get_elapsed(e.get("started_at", ""), e.get("finished_at")) if e.get("started_at") else "-")
            t.add_row("tmux セッション", e.get("tmux_session") or "-")
            t.add_row("worktree パス", e.get("worktree_path") or "-")
            t.add_row("終了コード", str(e.get("exit_code")) if e.get("exit_code") is not None else "-")

            console.print(Panel(t, title="[magenta]Queue エントリ[/]", border_style="magenta"))

            tmux = e.get("tmux_session")
            if tmux:
                console.print(f"[dim]tmux に接続:[/]  [bold]tmux attach -t {tmux}[/]\n")

    # セッションエントリ
    if session_entries:
        for s in session_entries:
            status = s.get("status", "unknown")
            icon, color = SESSION_STATUS_DISPLAY.get(status, ("? 不明", "dim"))
            worktree = s.get("worktree_path", "")

            t = Table(box=box.SIMPLE, show_header=False, expand=False)
            t.add_column("項目", style="dim", width=18)
            t.add_column("値")

            t.add_row("Branch", s.get("branch", "-"))
            t.add_row("ステータス", Text(icon, style=color))
            t.add_row("PID", str(s.get("pid", "-")))
            t.add_row("AUTO モード", "はい" if s.get("auto_mode") else "いいえ")
            t.add_row("開始時刻", format_time(s.get("started_at"), "%Y-%m-%d %H:%M:%S"))
            t.add_row("経過時間", get_elapsed(s.get("started_at", ""), s.get("finished_at")))
            t.add_row("worktree パス", worktree or "-")

            console.print(Panel(t, title="[cyan]Session エントリ[/]", border_style="cyan"))

            # 最近のアクション履歴
            if worktree:
                actions = get_last_actions(worktree, n=10)
                if actions:
                    at = Table(box=box.SIMPLE, show_header=False, expand=False)
                    at.add_column("#", style="dim", width=3, justify="right")
                    at.add_column("アクション")
                    for j, action in enumerate(actions, 1):
                        at.add_row(str(j), action)
                    console.print(Panel(at, title="[dim]最近のアクション（新しい順）[/]", border_style="dim"))


# ─────────────────────────────────────────
# エントリポイント
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code ステータスダッシュボード",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  cc-status.sh                # フル表示（キュー + セッション）、リアルタイム更新
  cc-status.sh --once         # 1回だけ表示して終了
  cc-status.sh --queue        # キューパネルのみ表示
  cc-status.sh --history      # 完了・失敗エントリも含めて表示
  cc-status.sh --detail 199   # Issue #199 の詳細表示
  cc-status.sh --reattach     # 実行中 tmux セッションのアタッチコマンドを一覧表示
  cc-status.sh --clean        # 完了・エラーのステータスファイルを削除
        """,
    )
    parser.add_argument("--clean",    action="store_true", help="完了・エラーのステータスファイルを削除")
    parser.add_argument("--once",     action="store_true", help="1回だけ表示して終了（CI/スクリプト用）")
    parser.add_argument("--queue",    action="store_true", help="キューパネルのみ表示")
    parser.add_argument("--history",  action="store_true", help="完了・失敗エントリも含めて表示")
    parser.add_argument("--detail",   type=int, metavar="ISSUE", help="指定 Issue 番号の詳細を表示")
    parser.add_argument("--reattach", action="store_true", help="実行中の tmux セッションのアタッチコマンドを一覧表示")
    args = parser.parse_args()

    console = Console()

    # --clean
    if args.clean:
        removed = clean_statuses()
        console.print(f"[green]削除完了:[/] {removed} 件のステータスファイルを削除しました")
        return

    # --detail
    if args.detail is not None:
        show_detail(console, args.detail)
        return

    # --reattach
    if args.reattach:
        show_reattach(console)
        return

    def render_once() -> object:
        """現在の状態を描画して renderable を返す"""
        queue_all = load_queue(history=True)   # ヘッダーサマリー用に全件取得
        queue = load_queue(history=args.history)
        statuses = load_statuses(history=args.history)

        if args.queue:
            # キューのみ
            if queue:
                return Group(build_queue_table(queue))
            return build_empty_panel("Queue")

        # フル表示
        header = build_header(load_statuses(history=True), queue_all)
        parts = [header]

        if queue:
            parts.append(build_queue_table(queue))
        else:
            parts.append(build_empty_panel("Queue"))

        if statuses:
            parts.append(build_sessions_table(statuses))
        else:
            parts.append(build_empty_panel("Sessions"))

        parts.append(build_tips_panel())

        return Group(*parts)

    # --once
    if args.once:
        console.print(render_once())
        return

    # リアルタイム更新モード
    try:
        with Live(console=console, refresh_per_second=1, screen=False) as live:
            while True:
                live.update(render_once())
                time.sleep(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        console.print("\n[dim]終了しました[/]")


if __name__ == "__main__":
    main()
