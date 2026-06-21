# life-os

個人のための「なんでも」環境（personal life operating system）。
日々の暮らしと活動にまつわる情報・作業を、ひとつのリポジトリに集約して管理することを目的とする。

## 目的

このリポジトリは、以下の領域を横断的に扱う個人用の基盤を目指す。

- **タスク管理** — 日々のやること・プロジェクト・進捗の管理
- **旅行の行先管理** — 行きたい場所・旅程・記録の管理
- **画像・動画管理** — 写真や動画などのメディア資産の整理・管理
- **販売管理** — 自作ツールなどの販売に関する管理（今後展開予定）
- **英語学習** — 学習した単語・イディオム・重要な表現の蓄積と再利用

## ステータス

現在は構築の初期段階。各領域はこれから対話的に設計・実装していく。

## 目指す開発スタイル — Loop Engineering

life-os が目指す開発スタイルは **Loop Engineering（loop エンジニア）** である。AI に一手ずつプロンプトを打つ人ではなく、**AI を呼び出す loop（自動化された反復）そのものを設計・所有する人**を目指す。

Boris Cherny の「loop」三段階定義では、進むほど人の関与が**減る**のではなく層が**上がる** — 手を動かす対象が「コード」から「並列セッション群」、そして「loop の設計」へと移る。

1. **Stage 1** — モデルは自分が操作する道具（補完で一行ずつ）
2. **Stage 2** — モデルは並列に動かす相棒（複数セッションを人がプロンプト）
3. **Stage 3** — モデルは自分のプログラムが呼ぶサブルーチン（loop が自律的に次を決める）

life-os は **Stage 2 を運用しつつ Stage 3 の部品（意図の構造化・再利用スキル・検証ゲート・歯止め）を仕込んでいる**段階にある。実践原則（意図を一度だけ書く / 反復の委譲 / 再利用可能なスキル群 / 検証ゲート / ハードストップ）と、この repo での現在地・ロードマップは下記ガイドにまとめる。

> **指針**: [目指す開発スタイル — Loop Engineering](./guides/development-policy/loop-engineering.md)

## アーキテクチャ

性質の異なる複数領域を 1 リポジトリで共存させるため、**Modular Monolith × Bounded Context**（Python / uv workspace）を採用する。各領域は独立した Bounded Context で、領域間連携は各領域の `public.py`（契約）経由のみ。境界は `.importlinter` で機械的に強制する。

> **設計根拠**: [ADR-0002 複数領域を Modular Monolith × Bounded Context で共存させる](./docs/adr/0002-modular-monolith-bounded-context.md)

領域は性質に応じて 2 アーキタイプを使い分ける。

- **アーキタイプA（動く領域）**: `task` / `content-sales` — 軽量ヘキサゴナル（`domain` / `application` / `adapters`）
- **アーキタイプB（データ領域）**: `media` / `travel` / `english` — 薄い構成（`models` / `index`）+ `data/`

## ディレクトリ構成

```
.
├── pyproject.toml            # uv workspace ルート（各領域をメンバー化）
├── uv.lock                   # 依存ロック（再現性のためコミット）
├── .importlinter             # 領域境界の強制（lint-imports で検査）
├── compose.yaml              # ローカル実行用 Docker Compose（test / lint）
├── docker/                   # テスト実行用 Dockerfile（コード非依存のツール領域）
├── shared/                   # Shared Kernel（領域非依存の最小限の基盤のみ）
├── domains/                  # 領域コンテナ: Bounded Context をまとめる親（ADR-0009）
│   ├── task/                 # 領域: タスク管理（アーキタイプA）
│   ├── content-sales/        # 領域: 販売管理（アーキタイプA）
│   ├── media/                # 領域: 画像・動画管理（アーキタイプB）
│   ├── travel/               # 領域: 旅行の行先管理（アーキタイプB）
│   └── english/              # 領域: 英語学習（アーキタイプB）
├── presentation/             # content領域: プレゼン作成（HTMLスライド生成・コード非依存）
├── .claude/
│   ├── agents/               # Claude Code サブエージェント（スライド生成 / pr-reviewer）
│   └── skills/               # Claude Code スキル（issue-memory / slide-* / code-review-* / directory-keeper）
├── .github/
│   ├── ISSUE_TEMPLATE/        # Issue テンプレート（ProductBacklog / Task / 調査）
│   └── pull_request_template.md
├── docs/
│   └── adr/                   # 設計決定記録（Architecture Decision Records）
├── guides/
│   └── development-policy/    # 開発運用ルール（Issue 運用など）
├── rule/                      # ディレクトリ構成論ルール（構造ガバナンス）
├── scripts/                   # 開発・運用を補助する自動化スクリプト群
├── CLAUDE.md                  # Claude Code 向けプロジェクト指示書
└── README.md
```

> `presentation/` はコードを持たない content 領域（`docs/`・`guides/` と同類）で、uv workspace member でも Bounded Context でもない。スライド生成のエージェント・スキルは Claude Code がネイティブに認識する `.claude/agents/`・`.claude/skills/` に置く（[ADR-0003](./docs/adr/0003-presentation-system.md)）。
>
> `docker/`・`compose.yaml` はテスト実行用のツール領域で、Bounded Context ではない（uv workspace member・`.importlinter` の管理対象外）。`Dockerfile` は専用ディレクトリ `docker/` に隔離し、`compose.yaml` は慣習どおりルートに置く（[ADR-0006](./docs/adr/0006-docker-test-environment.md)）。

各領域はスケルトン段階で、要件が固まり次第 `public.py` と内部を肉付けしていく。新しい領域を追加する際は、`domains/` 配下のディレクトリ・uv workspace の `members`・`.importlinter` のコントラクト・対応する `system: *` ラベルを併せて整備する（手順は ADR-0002、配置先は [ADR-0009](./docs/adr/0009-group-domains-under-domains-dir.md) 参照）。

## 開発セットアップ

テスト・境界検査は **Docker（Docker Compose）で実行する**。ローカルに Python / uv を導入する必要はない（[uv](https://docs.astral.sh/uv/) は Docker イメージ内部でのみ使う）。

```bash
docker compose run --rm test    # 各領域のスモークテスト（pytest）
docker compose run --rm lint    # 領域境界（.importlinter）を検査
docker compose build            # 依存を変えたときにイメージを再ビルド
```

ソースをマウントするため、コード変更は再ビルド無しで即反映される（`pyproject.toml` / `uv.lock` を変えたときだけ `build` する）。構成と判断の根拠は [ADR-0006](./docs/adr/0006-docker-test-environment.md)。

## Git 戦略

純粋な **GitHub Flow（`main` ブランチのみ）** を採用する。

- 長命ブランチは `main` だけ
- 作業は**最新化した `main`**（ブランチ作成前に必ず `git pull`）から `{type}/issue-{N}-{作業名}` の feature ブランチを切る
- PR（本文に `Closes #N`）でレビュー後、`main` に直接マージする

## 開発運用

- [目指す開発スタイル — Loop Engineering](./guides/development-policy/loop-engineering.md) — loop エンジニアを目指す方針と Stage 3 へのロードマップ
- [ディレクトリ構成論ルール](./rule/README.md) — リポジトリがどうあるべきか（配置・命名・ドキュメント重複禁止）
- [directory-keeper](./.claude/skills/directory-keeper/SKILL.md) — 構成を日次で監査し整頓するエージェント（Routines で定期実行・[ADR-0005](./docs/adr/0005-directory-governance-daily-keeper.md)）
- [Issue 運用ルール](./guides/development-policy/issue-operation-rules.md) — Issue の分類・ラベル・作業フロー
- [Issue メモリスキル](./.claude/skills/issue-memory/SKILL.md) — Issue の起票から作業完了報告まで一本化する
- [コードレビュー運用ルール](./guides/development-policy/code-review-rules.md) — PR を観点別スキルでレビューし、修正PR作成 or 検証付き自動マージまで回す（`pr-reviewer` エージェント）
- [ADR（設計決定記録）](./docs/adr/README.md) — 「なぜその設計にしたか」を残す
- [プレゼン作成システム](./presentation/README.md) — テーマから HTML スライドを生成するエージェント・スキル基盤
- 構成チェック: `python scripts/check_structure.py`（ルール準拠の決定的チェック）
- ラベルの一括作成: `./scripts/setup-github-labels.sh --dry-run`（確認）/ `./scripts/setup-github-labels.sh`（適用）
