---
name: scrum-notion-pbi
description: Notion の Product Backlog データベースに PBI（Product Backlog Item）を対話形式で作成するスキル。Title 命名規則・Sprint 提案・Project 特定・本文テンプレートを一本化する。Use when: PBI を作成したい、Notion にバックログを起票したい、Sprint Planning でバックログを追加したい。Triggers on: PBI作成, scrum-notion-pbi, Notionバックログ登録, PBI起票, プロダクトバックログ追加.
---

# scrum-notion-pbi スキル

Notion の **Product Backlog** データベースに PBI を対話形式で作成するスキル。
命名規則は `scrum-notion-*`（Scrum 運用に関する Notion 連携スキル群の接頭辞）。

> 現時点はこのスキルの「器」の設計。実データベースへの書き込みロジックは、次回以降ユーザーと合意の上で実装する。

---

## スコープ（現時点）

- 対象は **PBI 作成のみ**。
- **Task 作成は対象外**。別スキル（`scrum-notion-task` 等、命名未確定）として今後別途検討する。
- Level / Point は今回の必須プロパティに含まれないため、本スキルでは設定しない（未設定のまま作成する）。

---

## 参照するデータベース定義・テンプレート

スキーマの一次情報とテンプレートは以下に記録済み（本スキルはこれらを参照し、内容の重複定義をしない）。

- [`domains/task/docs/databases/product-backlog.md`](../../../domains/task/docs/databases/product-backlog.md) — 作成先データベース
- [`domains/task/docs/databases/sprint.md`](../../../domains/task/docs/databases/sprint.md) — Sprint 提案に使用
- [`domains/task/docs/databases/project.md`](../../../domains/task/docs/databases/project.md) — Project 特定に使用
- [`domains/task/docs/template/pbi.md`](../../../domains/task/docs/template/pbi.md) — PBI 本文（content）テンプレート

| データベース | Data Source URL |
|---|---|
| Product Backlog（作成先） | `collection://ec5e41b3-3c58-4b2b-acf8-9fc0655f094d` |
| Sprint | `collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e` |
| Project | `collection://b270c90b-09d5-4a6c-8c9a-f660442743e0` |

---

## トリガー条件

- ユーザーが `/scrum-notion-pbi` を実行した場合
- 「PBI 作成して」「Notion にバックログ登録して」「PBI 起票して」と依頼された場合

---

## 必須プロパティと決定方法

| プロパティ | 型 | 決定方法 |
|---|---|---|
| `Status` | status | **`New` 固定**。初回作成時は常にこの値（ユーザーに確認しない） |
| `Title` | title | 下記「Title 命名規則」に従い組み立てる |
| `Sprint` | relation | 外部入力（ユーザー指定）。未指定なら「Sprint 提案ロジック」に従い候補を提示して確認を取る |
| `Project` | relation | 外部入力（ユーザー指定）。Project データベースを検索し該当ページを特定する |

---

## Title 命名規則

```
{Sprintの開始日 yyyymmdd}{半角空白}{プロジェクト名}{半角空白}{内容}
```

例: `20260803 JMAS AI WBS作成`

- 日付区切りなし8桁（`yyyymmdd`）、スペースは**半角**。
- 「プロジェクト名」は Project ページの `Project Name` をそのまま使う。
- 「内容」は PBI の要点を表す短いラベル（本文テンプレートの詳細説明とは別物）。ユーザーへのヒアリングで一言サマリを確認する。
- Sprint が未確定の間は Title を確定できないため、Sprint 決定 → Title 組み立ての順で進める。

---

## 本文（content）テンプレート

[`domains/task/docs/template/pbi.md`](../../../domains/task/docs/template/pbi.md) を使用する。

- 各セクションの中身は**顧客からの説明を受けて**埋める。
- 説明が不足しているセクションがあれば、作成前に必ずユーザーに質問する（憶測で埋めない）。
- 完了条件のチェックリスト項目数はテンプレートの3件が目安。内容に応じて増減してよい。

---

## ワークフロー概要（設計）

```
ステップ0: Project を特定する
     ↓
ステップ1: Sprint を決定する（外部入力 or 近しい日程のSprintを提案）
     ↓
ステップ2: 内容（Titleの要約ラベル）をヒアリングする
     ↓
ステップ3: Title を組み立てる（yyyymmdd + Project名 + 内容）
     ↓
ステップ4: 本文テンプレートを顧客説明に基づき埋める（不足があれば質問）
     ↓
ステップ5: 作成前プレビューをユーザーに提示し、確認を取る
     ↓
ステップ6: notion-create-pages で Product Backlog データソース配下に作成
```

### ステップ0: Project を特定する

- ユーザーに Project 名を確認する。
- Project データベース（`collection://b270c90b-09d5-4a6c-8c9a-f660442743e0`）を `query_data_sources` で検索し、`Project Name` が一致/部分一致するページを候補として提示する。
- 候補が複数、または見つからない場合はユーザーに確定させる。

### ステップ1: Sprint を決定する

- ユーザーが Sprint を明示した場合はそれを採用する。
- 未指定の場合は Sprint データベース（`collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e`）を `Start Day` 昇順でクエリし、次の優先順で提案する。
  1. 今日の日付が `Start Day`〜`End Day` の範囲に入る Sprint（進行中）
  2. 該当が無ければ、`Start Day` が今日以降で最も近い Sprint（次回）
- 提案した Sprint をユーザーに確認してもらい、必要なら別の Sprint に変更する。

### ステップ2〜4

- 上記「Title 命名規則」「本文（content）テンプレート」に従う。

### ステップ5: 作成前プレビュー

- Title / Status(`New`固定) / Sprint / Project / 本文の最終形をユーザーに提示し、承認を得てから作成する（Notion への書き込みは不可逆に近いため）。

### ステップ6: 作成

- `notion-create-pages` を用いて Product Backlog データソース（`collection://ec5e41b3-3c58-4b2b-acf8-9fc0655f094d`）配下にページを作成する。
- properties: `Title`, `Status`（`New`固定）, `Sprint`（relation）, `Project`（relation）
- content: [`domains/task/docs/template/pbi.md`](../../../domains/task/docs/template/pbi.md) を埋めたMarkdown

---

## 使用する Notion MCP ツール

| ツール | 用途 |
|---|---|
| `notion-query-data-sources` | Sprint 候補検索・Project 検索 |
| `notion-create-pages` | PBI ページ作成 |
| `notion-fetch` | 作成後の確認・スキーマ再確認 |

---

## 未確定・今後の検討事項

- Task 作成スキル（`scrum-notion-task` 等）は別途設計する。
- Level / Point の入力タイミング・ルールは未定義（本スキルの対象外）。
- Sprint 提案ロジックの「今日」の取得方法（実行時の現在日時をどう扱うか）は実装時に確定する。
- ステップ5のプレビュー形式（テキスト表示 vs 別確認手段）は実装時に確定する。
