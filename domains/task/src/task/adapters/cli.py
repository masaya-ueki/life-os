"""task の CLI アダプタ（スケルトン）。

入力（CLI 引数）をユースケース呼び出しに変換する境界。
"""

from __future__ import annotations

from task.application import create_task


def main(argv: list[str] | None = None) -> int:
    """エントリポイント（スケルトン）。"""
    title = " ".join(argv) if argv else "サンプルタスク"
    task = create_task(title)
    print(f"created: {task.id} {task.title} [{task.status.value}]")
    return 0
