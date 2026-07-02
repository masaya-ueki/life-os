# tools — ユーティリティスクリプト集

> **構成根拠**: [ADR-0002 複数領域を Modular Monolith × Bounded Context で共存させる](../../docs/adr/0002-modular-monolith-bounded-context.md)

個人向けの汎用ユーティリティスクリプトをまとめた Bounded Context。
各ツールは独立したサブモジュールとして `src/tools/` 配下に格納する。

## 収録ツール

| ツール | モジュール | 概要 |
|--------|-----------|------|
| CSV 分割 | `tools.csv_splitter` | CSV ファイルを指定行数ごとに分割する |
| IAM ユーザ一覧 | `tools.iam_user_list` | 最終ログイン日で絞り込んだ IAM ユーザ一覧を CSV 出力する |

## 内部構成

```
src/tools/
├── public.py         # ★他領域に公開する唯一の契約（現在は空）
├── csv_splitter/     # 各ツールはサブモジュールとして追加
│   └── split.py      # コアロジック + CLI エントリポイント
└── iam_user_list/
    └── list_users.py # コアロジック + CLI エントリポイント
data/
├── csv_splitter/
│   ├── input/        # 入力 CSV のデフォルト置き場
│   └── output/       # 実行ごとにタイムスタンプ付きサブディレクトリを生成
└── iam_user_list/
    └── output/       # CSV 出力先（.gitignore で管理外）
test/
├── test_csv_splitter.py
└── test_iam_user_list.py
```

## csv_splitter — CSV 分割ツール

### 使い方

```bash
# Docker 経由で実行（--chunk-size は必須）
docker compose run --rm test \
  uv run python -m tools.csv_splitter.split --chunk-size 1000

# オプション一覧
uv run python -m tools.csv_splitter.split --help
```

### CLI オプション

| オプション | デフォルト | 説明 |
|-----------|------------|------|
| `--input` | `data/csv_splitter/input/` | 入力 CSV ファイルまたはディレクトリ |
| `--output` | `data/csv_splitter/output/{yyyymmdd_HHmmss}/` | 出力先ディレクトリ |
| `--chunk-size` | 1000 | 1 ファイルあたりの最大行数 |
| `--no-input-header` | （未指定 = ヘッダーあり） | 入力 CSV にヘッダー行がない場合に指定 |
| `--no-output-header` | （未指定 = ヘッダーを付与） | 出力にヘッダーを付与しない場合に指定 |

入力にディレクトリを指定した場合、CSV ファイルが 1 つだけのときは自動選択する。
2 つ以上ある場合はエラーになるのでファイルパスを直接指定すること。

### データパス

| パス | 用途 |
|------|------|
| `domains/tools/data/csv_splitter/input/` | 入力 CSV の置き場（デフォルト） |
| `domains/tools/data/csv_splitter/output/` | 実行時出力（.gitignore で管理外） |

## iam_user_list — IAM ユーザ一覧取得ツール

最終ログイン日（コンソールログイン＝`PasswordLastUsed`）が指定日 **以前** の IAM ユーザに
絞り込み、最終ログイン日で昇順ソートした一覧を CSV 出力する。棚卸し（使われていない
ユーザの洗い出し）を想定したツール。

### 前提

- **boto3** と **AWS CLI v2**（`aws sso login` 用）が必要。
- 実行環境に AWS 認証情報が要るため、テスト用 Docker イメージ（`docker compose run --rm test`）
  では動かない。ローカルホストで実行する。boto3 は uv workspace の依存には入れず、実行時に
  `uv run --with boto3` で一時的に与える（テストイメージを AWS SDK で肥大化させないため）。

### 使い方

```bash
# リポジトリルートで実行。--before は必須（yyyy-mm-dd）
uv run --with boto3 python -m tools.iam_user_list.list_users --before 2025-01-01

# プロファイル・出力先を指定
uv run --with boto3 python -m tools.iam_user_list.list_users \
  --before 2025-01-01 --profile iam-tool --output ./output/

# オプション一覧
uv run --with boto3 python -m tools.iam_user_list.list_users --help
```

`--login-mode auto`（既定）では、認証情報が無効なときだけ自動で
`aws sso login --profile <profile>` を実行して再試行する。

### CLI オプション

| オプション | デフォルト | 説明 |
|-----------|------------|------|
| `--before` | （必須） | この最終ログイン日以前（当日を含む）のユーザに絞り込む（`yyyy-mm-dd`） |
| `--profile` | `iam-tool` | 使用する AWS プロファイル名 |
| `--output` | `data/iam_user_list/output/{yyyymmdd_hhmmss}_{account_id}_iam_user_list.csv` | `.csv` ならファイル、ディレクトリなら既定ファイル名で配置 |
| `--login-mode` | `auto` | `aws sso login` の実行方針（`auto`＝必要時のみ / `always`＝必ず / `never`＝しない） |
| `--exclude-never-logged-in` | （未指定 = 含める） | 一度もログインしていないユーザを対象から除外する |

### 出力 CSV の列

`user_name` / `user_id` / `arn` / `create_date` / `password_last_used` /
`days_since_last_login` / `ever_logged_in`（Excel で開けるよう UTF-8 BOM 付き）。

### キャビアット

- 「最終ログイン日」は **コンソールログイン**（`PasswordLastUsed`）のみを見る。アクセスキー
  での API 利用は含まないため、コンソール未ログインでもキーが現役のユーザがいる点に注意
  （削除判断に使う場合は別途アクセスキーの利用状況を確認すること）。
- 一度もログインしていないユーザ（`PasswordLastUsed` なし）は「最も古い」とみなして既定で
  対象に含め、ソートでは先頭に来る。

### データパス

| パス | 用途 |
|------|------|
| `domains/tools/data/iam_user_list/output/` | CSV 出力先（デフォルト。`.gitignore` で管理外） |

## 境界（Context Map メモ）

- 他領域からは `from tools.public import ...` のみ許可（現在エクスポートなし）。
- `tools.csv_splitter` / `tools.iam_user_list` への直接 import は `.importlinter` で禁止される。
- tools 自体も他領域の内部パッケージ（`media.models` 等）を直接 import しない。
