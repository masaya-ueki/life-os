# life-os

個人のための「なんでも」環境（personal life operating system）。
日々の暮らしと活動にまつわる情報・作業を、ひとつのリポジトリに集約して管理することを目的とする。

## 目的

このリポジトリは、以下の領域を横断的に扱う個人用の基盤を目指す。

- **タスク管理** — 日々のやること・プロジェクト・進捗の管理
- **旅行の行先管理** — 行きたい場所・旅程・記録の管理
- **画像・動画管理** — 写真や動画などのメディア資産の整理・管理
- **販売管理** — 自作ツールなどの販売に関する管理（今後展開予定）

## ステータス

現在は構築の初期段階。各領域はこれから対話的に設計・実装していく。

## ディレクトリ構成

現状は開発の「運用・ドキュメント基盤（メタ構造）」を整備した段階。各領域の機能ディレクトリは要件が固まり次第、順次追加する。

```
.
├── .github/
│   ├── ISSUE_TEMPLATE/        # Issue テンプレート（ProductBacklog / Task / 調査）
│   ├── skills/create-issue/   # Issue を対話形式で作成するスキル
│   └── pull_request_template.md
├── docs/
│   └── adr/                   # 設計決定記録（Architecture Decision Records）
├── guides/
│   └── development-policy/    # 開発運用ルール（Issue 運用など）
├── scripts/                   # 開発・運用を補助する自動化スクリプト群
└── README.md
```

今後、各領域（タスク管理・旅行・メディア・販売）の要件を整理しながら、`task/`・`travel/`・`media/`・`content-sales/` などの機能ディレクトリを順次追加していく。新しい領域を追加する際は、対応する `system: *` ラベル（scope）も併せて整備する。

## Git 戦略

純粋な **GitHub Flow（`main` ブランチのみ）** を採用する。

- 長命ブランチは `main` だけ
- 作業は `main` から `{type}/issue-{N}-{作業名}` の feature ブランチを切る
- PR（本文に `Closes #N`）でレビュー後、`main` に直接マージする

## 開発運用

- [Issue 運用ルール](./guides/development-policy/issue-operation-rules.md) — Issue の分類・ラベル・作業フロー
- [Issue 作成スキル](./.github/skills/create-issue/SKILL.md) — Issue を対話形式で起票する
- [ADR（設計決定記録）](./docs/adr/README.md) — 「なぜその設計にしたか」を残す
- ラベルの一括作成: `./scripts/setup-github-labels.sh --dry-run`（確認）/ `./scripts/setup-github-labels.sh`（適用）
