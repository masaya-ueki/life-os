"""iam_user_list の純粋ロジック（絞り込み・ソート・CSV 整形）のテスト。

boto3 / AWS 認証は伴わない（list_users.py が boto3 を遅延 import しているため、
本テストは boto3 未インストールでも収集・実行できる）。
"""

from __future__ import annotations

import csv
from datetime import date, datetime, timezone

from tools.iam_user_list.list_users import (
    CSV_HEADER,
    IamUser,
    build_output_filename,
    filter_and_sort_users,
    resolve_output_path,
    to_csv_row,
    write_csv,
)


def _user(name: str, plu: datetime | None) -> IamUser:
    return IamUser(
        user_name=name,
        user_id=f"AIDA{name}",
        arn=f"arn:aws:iam::123456789012:user/{name}",
        create_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
        password_last_used=plu,
    )


def test_filter_keeps_users_logged_in_on_or_before_before_date():
    users = [
        _user("old", datetime(2024, 6, 30, 12, 0, tzinfo=timezone.utc)),
        _user("boundary", datetime(2025, 1, 1, 23, 59, tzinfo=timezone.utc)),
        _user("recent", datetime(2025, 6, 1, tzinfo=timezone.utc)),
    ]
    result = filter_and_sort_users(users, before=date(2025, 1, 1))
    names = [u.user_name for u in result]
    assert names == ["old", "boundary"]  # 当日(boundary)は含む、それ以降(recent)は除外


def test_never_logged_in_included_by_default_and_sorted_first():
    users = [
        _user("logged", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        _user("never", None),
    ]
    result = filter_and_sort_users(users, before=date(2025, 1, 1))
    assert [u.user_name for u in result] == ["never", "logged"]


def test_never_logged_in_can_be_excluded():
    users = [
        _user("logged", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        _user("never", None),
    ]
    result = filter_and_sort_users(
        users, before=date(2025, 1, 1), include_never_logged_in=False
    )
    assert [u.user_name for u in result] == ["logged"]


def test_sort_is_ascending_by_last_login():
    users = [
        _user("c", datetime(2024, 12, 1, tzinfo=timezone.utc)),
        _user("a", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        _user("b", datetime(2024, 6, 1, tzinfo=timezone.utc)),
    ]
    result = filter_and_sort_users(users, before=date(2025, 1, 1))
    assert [u.user_name for u in result] == ["a", "b", "c"]


def test_to_csv_row_reports_days_and_ever_logged_in():
    now = datetime(2025, 1, 11, tzinfo=timezone.utc)
    logged = to_csv_row(_user("x", datetime(2025, 1, 1, tzinfo=timezone.utc)), now)
    never = to_csv_row(_user("y", None), now)

    assert logged[CSV_HEADER.index("days_since_last_login")] == "10"
    assert logged[CSV_HEADER.index("ever_logged_in")] == "yes"
    assert never[CSV_HEADER.index("days_since_last_login")] == ""
    assert never[CSV_HEADER.index("ever_logged_in")] == "no"
    assert never[CSV_HEADER.index("password_last_used")] == ""


def test_build_output_filename_format():
    when = datetime(2025, 1, 2, 3, 4, 5)
    assert (
        build_output_filename("123456789012", when)
        == "20250102_030405_123456789012_iam_user_list.csv"
    )


def test_resolve_output_path_directory_vs_file(tmp_path):
    when = datetime(2025, 1, 2, 3, 4, 5)

    # ディレクトリ指定 → 既定ファイル名を付与
    as_dir = resolve_output_path(tmp_path, "123456789012", when)
    assert as_dir == tmp_path / "20250102_030405_123456789012_iam_user_list.csv"

    # .csv 指定 → そのまま
    explicit = tmp_path / "custom.csv"
    assert resolve_output_path(explicit, "123456789012", when) == explicit


def test_write_csv_roundtrip(tmp_path):
    now = datetime(2025, 1, 11, tzinfo=timezone.utc)
    users = [
        _user("never", None),
        _user("logged", datetime(2025, 1, 1, tzinfo=timezone.utc)),
    ]
    path = tmp_path / "out.csv"
    write_csv(path, users, now)

    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    assert rows[0] == CSV_HEADER
    assert rows[1][0] == "never"
    assert rows[2][0] == "logged"
    assert len(rows) == 3
