# CLAUDE.md

このリポジトリで作業する Claude Code 向けのガイドです。

## はじめに（最初に必ず読む）

**作業を始める前に、まず [README.md](./README.md) を読むこと。**
プロジェクトの目的・アーキテクチャ・ディレクトリ構成・開発セットアップ・Git 戦略は README が一次情報源です。本ファイルは README を読んだ前提で、作業時に繰り返し参照する要点と運用ルールへのポインタをまとめます。README と矛盾する場合は README を優先してください。

## プロジェクト概要

life-os は個人のための「なんでも」環境（personal life operating system）。タスク管理・旅行・メディア管理・販売管理などの異なる領域を 1 リポジトリに集約する。Python / uv workspace による **Modular Monolith × Bounded Context** 構成。

詳細は README と [docs/adr/](./docs/adr/README.md)（設計決定記録）を参照。

## アーキテクチャの要点

- 各領域は独立した **Bounded Context**。領域間連携は各領域の `public.py`（契約）経由のみ。
- 境界は [`.importlinter`](./.importlinter) で機械的に強制される。**他領域の内部パッケージ（`domain` / `application` / `adapters` / `models` / `index`）を直接 import しない。**
- `shared/` は領域非依存の Shared Kernel。いかなる領域にも依存してはならない。
- 領域には 2 アーキタイプがある:
  - **アーキタイプA（動く領域）**: `task` / `content-sales` — 軽量ヘキサゴナル（`domain` / `application` / `adapters`）
  - **アーキタイプB（データ領域）**: `media` / `travel` — 薄い構成（`models` / `index`）+ `data/`
- `presentation/`・`docs/`・`guides/` はコードを持たない content 領域（uv workspace member でも Bounded Context でもない）。
- 新領域を追加するときは、トップレベルディレクトリ・uv workspace の `members`・`.importlinter` のコントラクト・`system: *` ラベルを併せて整備する（手順は [ADR-0002](./docs/adr/0002-modular-monolith-bounded-context.md)）。
- 領域直下に `public.py` 以外の新規トップレベルモジュールを足したら、`.importlinter` にも追記すること。

## よく使うコマンド

[uv](https://docs.astral.sh/uv/) を使用する。

```bash
uv sync                 # 依存をインストール（dev グループに import-linter / pytest）
uv run lint-imports     # 領域境界（.importlinter）を検査
uv run pytest           # 各領域のスモークテストを実行
```

**コードを変更したら `uv run lint-imports` と `uv run pytest` を実行して境界とテストを確認すること。**

## Git・Issue 運用

純粋な **GitHub Flow（`main` ブランチのみ）**。長命ブランチは `main` だけ。

- ブランチ: `main` から `{type}/issue-{N}-{作業名-kebab-case}` を切る（例: `feat/issue-12-add-travel-list`）。
- コミット: Conventional Commits 形式 `{type}({scope}): {要約}`（例: `feat(task): タスク並び替え機能を追加`）。`{type}` は type ラベル、`{scope}` は `system: *` ラベルと一致させる。
- PR 本文に `Closes #N` を記載し、レビュー後 `main` に直接マージする。
- Issue の分類・ラベル・作業フローは [Issue 運用ルール](./guides/development-policy/issue-operation-rules.md) に従う。

## 設計判断（ADR）

一般的な慣習から外れた選択や、変更コストの高い構造的判断をしたときは ADR を残す（基準と手順は [docs/adr/README.md](./docs/adr/README.md)）。ADR に対応する設計には ADR へのリンクを張ること。

## 参照ドキュメント

- [README.md](./README.md) — プロジェクトの一次情報源（**最初に読む**）
- [docs/adr/](./docs/adr/README.md) — 設計決定記録（なぜその設計にしたか）
- [guides/development-policy/loop-engineering.md](./guides/development-policy/loop-engineering.md) — 目指す開発スタイル（Loop Engineering）
- [guides/development-policy/issue-operation-rules.md](./guides/development-policy/issue-operation-rules.md) — Issue 運用ルール
- [.github/skills/create-issue/SKILL.md](./.github/skills/create-issue/SKILL.md) — Issue を対話形式で起票するスキル
- [presentation/README.md](./presentation/README.md) — テーマから HTML スライドを生成するエージェント・スキル基盤
