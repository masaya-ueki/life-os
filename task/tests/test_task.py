"""task のスモークテスト（スケルトン）。"""

from task.application import create_task
from task.domain import Status


def test_create_task_starts_as_todo():
    task = create_task("買い物に行く")
    assert task.title == "買い物に行く"
    assert task.status is Status.TODO


def test_complete_task():
    task = create_task("掃除")
    task.complete()
    assert task.status is Status.DONE
