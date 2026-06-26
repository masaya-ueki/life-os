# tools — ユーティリティスクリプト集

> **構成根拠**: [ADR-0002 複数領域を Modular Monolith × Bounded Context で共存させる](../../docs/adr/0002-modular-monolith-bounded-context.md)

個人向けの汎用ユーティリティスクリプトをまとめた Bounded Context。
各ツールは独立したサブモジュールとして `src/tools/` 配下に格納する。

## 収録ツール

| ツール | モジュール | 概要 |
|--------|-----------|------|
| CSV 分割 | `tools.csv_splitter` | CSV ファイルを指定行数ごとに分割する |

## 内部構成

```
src/tools/
├── public.py         # ★他領域に公開する唯一の契約（現在は空）
└── csv_splitter/     # 各ツールはサブモジュールとして追加
    └── split.py      # コアロジック + CLI エントリポイント
data/
└── csv_splitter/
    ├── input/        # 入力 CSV のデフォルト置き場
    └── output/       # 実行ごとにタイムスタンプ付きサブディレクトリを生成
test/
└── test_csv_splitter.py
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

## 境界（Context Map メモ）

- 他領域からは `from tools.public import ...` のみ許可（現在エクスポートなし）。
- `tools.csv_splitter` への直接 import は `.importlinter` で禁止される。
- tools 自体も他領域の内部パッケージ（`media.models` 等）を直接 import しない。
