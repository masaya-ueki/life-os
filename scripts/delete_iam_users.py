#!/usr/bin/env python3
"""IAM ユーザを一括削除するスクリプト。

概要
----
入力ファイル（IAM ユーザ名の一覧）を読み込み、指定した AWS プロファイル
（既定: ``iam-tool``）で認証したうえで、対象ユーザを一括削除する。

IAM ユーザは、アクセスキー・ログインプロファイル・MFA デバイス・インライン/
アタッチ済みポリシー・グループ所属などの付随リソースが残っていると削除できず
``DeleteConflict`` になる。本スクリプトは削除前にこれら付随リソースをすべて
取り外してから ``delete_user`` を呼ぶ。

使い方
------
    python scripts/delete_iam_users.py <users_file> [--profile iam-tool] [--dry-run]

``<users_file>`` は 1 行 1 ユーザ名のテキストファイル。空行と ``#`` 始まりの
コメント行は無視する。

認証
----
プロファイルの資格情報が無効/期限切れの場合は ``aws login --profile
<profile>`` を自動実行して再認証を試みる。``aws login`` はブラウザを開いて
サインインする簡易認証コマンド（AWS CLI v2 2.32.0 以降が必要）。

依存
----
    pip install boto3
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # pragma: no cover - 実行環境依存
    sys.exit("boto3 が必要です。`pip install boto3` を実行してください。")


DEFAULT_PROFILE = "iam-tool"


# --------------------------------------------------------------------------- #
# 入力
# --------------------------------------------------------------------------- #
def load_usernames(path: Path) -> list[str]:
    """ユーザ名一覧ファイルを読み込む。空行と ``#`` コメント行は無視する。"""
    if not path.is_file():
        sys.exit(f"入力ファイルが見つかりません: {path}")

    usernames: list[str] = []
    seen: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        name = raw.strip()
        if not name or name.startswith("#"):
            continue
        if name in seen:  # 重複は 1 回だけ扱う
            continue
        seen.add(name)
        usernames.append(name)
    return usernames


# --------------------------------------------------------------------------- #
# 認証
# --------------------------------------------------------------------------- #
def build_session(profile: str) -> boto3.Session:
    """プロファイルで boto3 セッションを作り、必要なら aws login で再認証する。

    戻り値は認証済みのセッション。認証できない場合はプロセスを終了する。
    """

    def make_session() -> boto3.Session:
        # プロファイル未設定なら Session 構築時点で ProfileNotFound、資格情報が
        # 無効/期限切れなら get_caller_identity で例外になる。両方まとめて捕捉する。
        session = boto3.Session(profile_name=profile)
        session.client("sts").get_caller_identity()
        return session

    try:
        return make_session()
    except (ClientError, BotoCoreError) as exc:
        # 資格情報が無効/期限切れ、またはプロファイル未設定。aws login で再認証を試みる。
        print(f"認証が必要です（{exc.__class__.__name__}）。aws login を実行します...")

    try:
        subprocess.run(
            ["aws", "login", "--profile", profile],
            check=True,
        )
    except FileNotFoundError:
        sys.exit(
            "aws CLI が見つかりません。AWS CLI v2 (2.32.0 以降) をインストールしてください。"
        )
    except subprocess.CalledProcessError:
        sys.exit("aws login に失敗しました。認証を確認してください。")

    # ログイン後は資格情報を読み直すためセッションを作り直す。
    try:
        return make_session()
    except (ClientError, BotoCoreError) as exc:
        sys.exit(f"認証に失敗しました: {exc}")


def get_account_id(session: boto3.Session) -> str:
    """認証済みセッションからアカウント ID を取得する。"""
    return session.client("sts").get_caller_identity()["Account"]


# --------------------------------------------------------------------------- #
# 付随リソースの取り外し
# --------------------------------------------------------------------------- #
def _is_no_such_entity(exc: ClientError) -> bool:
    return exc.response.get("Error", {}).get("Code") == "NoSuchEntity"


def detach_dependencies(iam, username: str) -> None:
    """ユーザ削除前に付随リソースをすべて取り外す。

    IAM ユーザは以下が残っていると削除できないため、順に取り外す:
    アクセスキー / ログインプロファイル / MFA デバイス / 署名証明書 /
    SSH 公開鍵 / サービス固有の資格情報 / インラインポリシー /
    アタッチ済みマネージドポリシー / グループ所属 / アクセス許可境界。
    """
    # アクセスキー
    for key in iam.list_access_keys(UserName=username)["AccessKeyMetadata"]:
        iam.delete_access_key(UserName=username, AccessKeyId=key["AccessKeyId"])

    # ログインプロファイル（コンソールパスワード）
    try:
        iam.delete_login_profile(UserName=username)
    except ClientError as exc:
        if not _is_no_such_entity(exc):
            raise

    # MFA デバイス（無効化 → 仮想デバイスは削除）
    for mfa in iam.list_mfa_devices(UserName=username)["MFADevices"]:
        serial = mfa["SerialNumber"]
        iam.deactivate_mfa_device(UserName=username, SerialNumber=serial)
        # 仮想 MFA デバイスの ARN は :mfa/ を含む。実体も削除する。
        if ":mfa/" in serial:
            try:
                iam.delete_virtual_mfa_device(SerialNumber=serial)
            except ClientError as exc:
                if not _is_no_such_entity(exc):
                    raise

    # 署名証明書
    for cert in iam.list_signing_certificates(UserName=username)["Certificates"]:
        iam.delete_signing_certificate(
            UserName=username, CertificateId=cert["CertificateId"]
        )

    # SSH 公開鍵（CodeCommit 用）
    for key in iam.list_ssh_public_keys(UserName=username)["SSHPublicKeys"]:
        iam.delete_ssh_public_key(
            UserName=username, SSHPublicKeyId=key["SSHPublicKeyId"]
        )

    # サービス固有の資格情報
    creds = iam.list_service_specific_credentials(UserName=username)
    for cred in creds.get("ServiceSpecificCredentials", []):
        iam.delete_service_specific_credential(
            UserName=username,
            ServiceSpecificCredentialId=cred["ServiceSpecificCredentialId"],
        )

    # インラインポリシー
    for policy_name in iam.list_user_policies(UserName=username)["PolicyNames"]:
        iam.delete_user_policy(UserName=username, PolicyName=policy_name)

    # アタッチ済みマネージドポリシー
    attached = iam.list_attached_user_policies(UserName=username)
    for policy in attached["AttachedPolicies"]:
        iam.detach_user_policy(UserName=username, PolicyArn=policy["PolicyArn"])

    # グループ所属
    for group in iam.list_groups_for_user(UserName=username)["Groups"]:
        iam.remove_user_from_group(GroupName=group["GroupName"], UserName=username)

    # アクセス許可境界
    try:
        iam.delete_user_permissions_boundary(UserName=username)
    except ClientError as exc:
        if not _is_no_such_entity(exc):
            raise


def user_exists(iam, username: str) -> bool:
    """IAM ユーザが存在するか確認する。"""
    try:
        iam.get_user(UserName=username)
        return True
    except ClientError as exc:
        if _is_no_such_entity(exc):
            return False
        raise


def delete_user(iam, username: str) -> None:
    """付随リソースを取り外したうえでユーザを削除する。"""
    detach_dependencies(iam, username)
    iam.delete_user(UserName=username)


# --------------------------------------------------------------------------- #
# メイン
# --------------------------------------------------------------------------- #
def confirm(account_id: str, count: int) -> bool:
    """最終確認プロンプト。``yes`` のときだけ True を返す。"""
    answer = input(
        f"アカウント {account_id}：一括削除しますか？ {count}件 [yes/no]: "
    ).strip().lower()
    return answer == "yes"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="IAM ユーザを一括削除する。",
    )
    parser.add_argument(
        "users_file",
        type=Path,
        help="削除する IAM ユーザ名の一覧ファイル（1 行 1 ユーザ名）",
    )
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help=f"使用する AWS プロファイル（既定: {DEFAULT_PROFILE}）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際には削除せず、対象だけを表示する",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # 入力
    usernames = load_usernames(args.users_file)
    if not usernames:
        print("削除対象のユーザがありません。")
        return 0

    # 認証
    session = build_session(args.profile)
    account_id = get_account_id(session)
    iam = session.client("iam")

    # 存在確認（存在しないユーザは対象から除外し警告する）
    targets: list[str] = []
    missing: list[str] = []
    for name in usernames:
        (targets if user_exists(iam, name) else missing).append(name)

    if missing:
        print(f"存在しないため対象外: {len(missing)}件")
        for name in missing:
            print(f"  - {name}")

    if not targets:
        print("削除対象のユーザが存在しません。")
        return 0

    print(f"\n削除対象: {len(targets)}件")
    for name in targets:
        print(f"  - {name}")

    if args.dry_run:
        print("\n[dry-run] 実際の削除は行いませんでした。")
        return 0

    # 最終確認
    if not confirm(account_id, len(targets)):
        print("中止しました。")
        return 1

    # 削除
    deleted: list[str] = []
    failed: list[tuple[str, str]] = []
    for name in targets:
        try:
            delete_user(iam, name)
            deleted.append(name)
            print(f"削除: {name}")
        except (ClientError, BotoCoreError) as exc:
            failed.append((name, str(exc)))
            print(f"失敗: {name} ({exc})", file=sys.stderr)

    # 完了報告
    print("\n===== 完了報告 =====")
    print(f"アカウント: {account_id}")
    print(f"削除成功: {len(deleted)}件")
    print(f"削除失敗: {len(failed)}件")
    if failed:
        for name, reason in failed:
            print(f"  - {name}: {reason}")

    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
