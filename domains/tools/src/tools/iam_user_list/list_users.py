"""IAM ユーザ一覧を最終ログイン日で絞り込んで CSV 出力するスクリプト。

処理の流れ:
    1. `iam-tool` プロファイルで AWS 認証する（必要なら `aws sso login` を実行）。
    2. 全 IAM ユーザを取得する。
    3. 最終ログイン日（コンソールログイン＝PasswordLastUsed）が指定日 **以前** の
       ユーザに絞り込む。一度もログインしていないユーザ（PasswordLastUsed なし）は
       「最も古い」とみなしてデフォルトで対象に含める。
    4. 最終ログイン日で昇順ソート（未ログインを先頭）して CSV に書き出す。

使い方（リポジトリルートで実行。boto3 は uv の一時依存として渡す）:
    uv run --with boto3 python -m tools.iam_user_list.list_users --before 2025-01-01
    uv run --with boto3 python -m tools.iam_user_list.list_users \
        --before 2025-01-01 --profile iam-tool --output ./output/

注意:
    - boto3 と AWS CLI v2（`aws sso login` 用）が必要。実行環境に AWS 認証情報が
      必要なため、テスト用 Docker イメージ（docker compose run --rm test）では動かない。
    - 「最終ログイン日」はコンソールログイン（PasswordLastUsed）を指す。アクセスキーの
      利用状況は含まない（README のキャビアット参照）。
"""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

# domains/tools/src/tools/iam_user_list/list_users.py → parents[3] == domains/tools
_DOMAIN_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = _DOMAIN_ROOT / "data" / "iam_user_list" / "output"
DEFAULT_PROFILE = "iam-tool"

CSV_HEADER = [
    "user_name",
    "user_id",
    "arn",
    "create_date",
    "password_last_used",
    "days_since_last_login",
    "ever_logged_in",
]


@dataclass(frozen=True)
class IamUser:
    """IAM ユーザ 1 件（list_users のレスポンスから必要な項目だけ抽出したもの）。"""

    user_name: str
    user_id: str
    arn: str
    create_date: datetime | None
    password_last_used: datetime | None


# --- 純粋ロジック（boto3 非依存。ここだけで絞り込み・整形をテストできる） ---


def _as_aware(dt: datetime) -> datetime:
    """naive な datetime は UTC とみなして aware にそろえる（比較の TypeError を防ぐ）。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _sort_key(password_last_used: datetime | None) -> datetime:
    """最終ログイン日の昇順ソート用キー。未ログインは最古（先頭）に来るようにする。"""
    if password_last_used is None:
        return datetime(1, 1, 1, tzinfo=timezone.utc)
    return _as_aware(password_last_used)


def filter_and_sort_users(
    users: list[IamUser],
    before: date,
    include_never_logged_in: bool = True,
) -> list[IamUser]:
    """最終ログイン日が ``before`` 以前のユーザに絞り、最終ログイン日で昇順ソートする。

    Args:
        users: 全 IAM ユーザ。
        before: この日（UTC のカレンダー日で比較）以前にログインしたユーザを残す。
        include_never_logged_in: 一度もログインしていないユーザを含めるか。

    Returns:
        絞り込み・ソート済みのユーザリスト。
    """
    kept: list[IamUser] = []
    for user in users:
        plu = user.password_last_used
        if plu is None:
            if include_never_logged_in:
                kept.append(user)
            continue
        if _as_aware(plu).date() <= before:
            kept.append(user)
    kept.sort(key=lambda u: _sort_key(u.password_last_used))
    return kept


def _iso(dt: datetime | None) -> str:
    return _as_aware(dt).isoformat() if dt is not None else ""


def to_csv_row(user: IamUser, now: datetime) -> list[str]:
    """1 ユーザを CSV_HEADER に対応する行へ変換する。``now`` は aware な現在時刻（UTC）。"""
    plu = user.password_last_used
    ever_logged_in = plu is not None
    if ever_logged_in:
        days_since = str((now - _as_aware(plu)).days)
    else:
        days_since = ""
    return [
        user.user_name,
        user.user_id,
        user.arn,
        _iso(user.create_date),
        _iso(plu),
        days_since,
        "yes" if ever_logged_in else "no",
    ]


def build_output_filename(account_id: str, when: datetime) -> str:
    """既定のファイル名 ``{yyyymmdd_hhmmss}_{account_id}_iam_user_list.csv`` を組み立てる。"""
    return f"{when:%Y%m%d_%H%M%S}_{account_id}_iam_user_list.csv"


def resolve_output_path(output_arg: Path | None, account_id: str, when: datetime) -> Path:
    """``--output`` の指定から実際の書き出しパスを決める。

    - 未指定       → DEFAULT_OUTPUT_DIR / 既定ファイル名
    - ``.csv`` 拡張子 → そのファイルパスを使う
    - それ以外     → ディレクトリとみなし、その下に既定ファイル名で置く
    """
    filename = build_output_filename(account_id, when)
    if output_arg is None:
        return DEFAULT_OUTPUT_DIR / filename
    if output_arg.suffix.lower() == ".csv":
        return output_arg
    return output_arg / filename


def write_csv(path: Path, users: list[IamUser], now: datetime) -> None:
    """ユーザ一覧を CSV に書き出す（Excel で開けるよう UTF-8 BOM 付き）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        for user in users:
            writer.writerow(to_csv_row(user, now))


# --- AWS 連携（boto3 / AWS CLI に依存。boto3 は遅延 import） ---


def _run_aws_sso_login(profile: str) -> None:
    """``aws sso login --profile <profile>`` を実行する（ブラウザ認証が開く）。"""
    aws = shutil.which("aws")
    if aws is None:
        raise RuntimeError(
            "aws CLI が見つかりません。ホストで `aws sso login --profile "
            f"{profile}` を実行してから、Docker では --login-mode never で実行してください"
            "（AWS CLI をインストール済みなら --login-mode auto/always が使えます）。"
        )
    print(f"[auth] aws sso login --profile {profile} を実行します...", file=sys.stderr)
    subprocess.run([aws, "sso", "login", "--profile", profile], check=True)


def _is_auth_error(exc: Exception) -> bool:
    """認証情報の欠如・期限切れなど「再ログインで直る」エラーかどうかを判定する。"""
    credential_error_names = {
        "NoCredentialsError",
        "PartialCredentialsError",
        "SSOTokenLoadError",
        "UnauthorizedSSOTokenError",
        "TokenRetrievalError",
        "CredentialRetrievalError",
    }
    if type(exc).__name__ in credential_error_names:
        return True
    try:
        error_code = exc.response["Error"]["Code"]  # type: ignore[attr-defined]
    except (AttributeError, KeyError, TypeError):
        error_code = None
    return error_code in {
        "ExpiredToken",
        "ExpiredTokenException",
        "InvalidClientTokenId",
        "RequestExpired",
        "UnrecognizedClientException",
    }


def _account_id(session) -> str:
    return session.client("sts").get_caller_identity()["Account"]


def create_session_and_account(profile: str, login_mode: str):
    """指定プロファイルの boto3 Session とアカウント ID を返す。

    login_mode:
        - "auto"  : 認証情報が無効なときだけ ``aws sso login`` を実行して再試行（既定）
        - "always": 先に必ず ``aws sso login`` を実行する
        - "never" : ログインは実行せず、既存の認証情報のみ使う
    """
    import boto3

    if login_mode == "always":
        _run_aws_sso_login(profile)

    session = boto3.Session(profile_name=profile)
    try:
        return session, _account_id(session)
    except Exception as exc:  # noqa: BLE001 - 認証エラーなら再ログインして再試行
        if login_mode == "never" or not _is_auth_error(exc):
            raise
        _run_aws_sso_login(profile)
        session = boto3.Session(profile_name=profile)
        return session, _account_id(session)


def fetch_users(session) -> list[IamUser]:
    """全 IAM ユーザをページングで取得する。"""
    iam = session.client("iam")
    users: list[IamUser] = []
    for page in iam.get_paginator("list_users").paginate():
        for u in page["Users"]:
            users.append(
                IamUser(
                    user_name=u["UserName"],
                    user_id=u["UserId"],
                    arn=u["Arn"],
                    create_date=u.get("CreateDate"),
                    password_last_used=u.get("PasswordLastUsed"),
                )
            )
    return users


# --- CLI ---


def _parse_before(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"日付は yyyy-mm-dd 形式で指定してください: {value!r}"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="最終ログイン日で絞り込んだ IAM ユーザ一覧を CSV 出力する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            f"デフォルト出力先: {DEFAULT_OUTPUT_DIR}/"
            "{yyyymmdd_hhmmss}_{account_id}_iam_user_list.csv"
        ),
    )
    parser.add_argument(
        "--before",
        type=_parse_before,
        required=True,
        metavar="YYYY-MM-DD",
        help="この最終ログイン日以前（当日を含む）のユーザに絞り込む",
    )
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help=f"使用する AWS プロファイル名（デフォルト: {DEFAULT_PROFILE}）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="出力先。.csv パスならそのファイル、ディレクトリなら既定ファイル名で配置",
    )
    parser.add_argument(
        "--login-mode",
        choices=("auto", "always", "never"),
        default="auto",
        help="aws sso login の実行方針（auto=必要時のみ / always=必ず / never=しない）",
    )
    parser.add_argument(
        "--exclude-never-logged-in",
        action="store_true",
        help="一度もログインしていないユーザを対象から除外する（既定は含める）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        session, account_id = create_session_and_account(args.profile, args.login_mode)
    except Exception as exc:  # noqa: BLE001 - 認証失敗はユーザ向けに要約して終了
        print(f"エラー: AWS 認証に失敗しました: {exc}", file=sys.stderr)
        return 1

    try:
        all_users = fetch_users(session)
    except Exception as exc:  # noqa: BLE001 - API 失敗はユーザ向けに要約して終了
        print(f"エラー: IAM ユーザの取得に失敗しました: {exc}", file=sys.stderr)
        return 1

    selected = filter_and_sort_users(
        all_users,
        before=args.before,
        include_never_logged_in=not args.exclude_never_logged_in,
    )

    now_utc = datetime.now(timezone.utc)
    output_path = resolve_output_path(args.output, account_id, datetime.now())
    write_csv(output_path, selected, now_utc)

    print(
        f"完了: アカウント {account_id} の IAM ユーザ {len(all_users)} 件中 "
        f"{len(selected)} 件を {output_path} に出力しました"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
