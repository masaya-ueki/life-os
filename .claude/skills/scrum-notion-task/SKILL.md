---
name: scrum-notion-task
description: Notion の Task データベースに単発タスクを対話形式で作成するスキル。ステータス自動判定・Member固定値・入力パラメータを一本化する。Use when: タスクを作成したい、Notion に単発タスクを登録したい、PBI配下にタスクを追加したい。Triggers on: タスク作成, scrum-notion-task, Notionタスク登録, 単発タスク作成.
---

# scrum-notion-task スキル

Notion の **Task** データベースに単発タスクを対話形式で作成するスキル。
命名規則は `scrum-notion-*`（[scrum-notion-pbi](../scrum-notion-pbi/SKILL.md) と同一の接頭辞）。

> 現時点は「単発タスク作成」の器の設計。定型タスク・会議の繰り返し作成や、Task 更新・ログ追記は対象外（今後の検討事項）。

---

## スコープ（現時点）

- 対象は **単発タスクの新規作成のみ**。
- タスクは基本的にログを持たない。**進捗ログは Task 本文ではなく親 PBI の本文に追記する運用**（[pbi.md](../../../domains/task/docs/template/pbi.md) の「詳細」等）。よって Task 側に本文テンプレートは存在しない。
- 定型タスク・会議の繰り返し生成ロジックは対象外。

---

## 参照するデータベース定義

- [`domains/task/docs/databases/task.md`](../../../domains/task/docs/databases/task.md) — 作成先データベース
- [`domains/task/docs/databases/product-backlog.md`](../../../domains/task/docs/databases/product-backlog.md) — 親 PBI 特定に使用

| データベース | Data Source URL |
|---|---|
| Task（作成先） | `collection://cdcc51b0-9c05-4c0a-9250-5329894f94c1` |
| Product Backlog | `collection://ec5e41b3-3c58-4b2b-acf8-9fc0655f094d` |

---

## トリガー条件

- ユーザーが `/scrum-notion-task` を実行した場合
- 「タスク作成して」「Notion にタスク登録して」「PBI 配下にタスクを追加して」と依頼された場合

---

## 入力パラメータと決定方法

| プロパティ | 型 | 決定方法 |
|---|---|---|
| `Name` | title | **入力パラメータの一つ**。呼び出し時に指定が無ければヒアリングする。下記「Name 命名規則」に従う |
| `Product Backlog` | relation | 入力パラメータ。どの PBI 配下のタスクかを指定（未指定ならヒアリング） |
| `Planned Hours` | number | 入力パラメータ（未指定ならヒアリング） |
| `Category` | select | 入力パラメータ。`task` / `todo` / `meeting` から選択してもらう |
| `Planned Date` | date（任意） | 定型タスク・会議は入力、単発タスクは未入力（null） |
| `Status` | status | **自動判定**。`Planned Date` が null なら `New`、null でなければ `Ready`（ユーザーに確認しない） |
| `Member` | person | **固定値**。Ueki Masaya（User ID: `c87b9a1c-ef2a-44ef-87d2-5349e1eb8ef2`） |
| `Acutual Hours` | number | **デフォルト値 `0`**（プロパティ名は Notion 側の原文ママ `Acutual`） |

---

## Name 命名規則

```
{PBIを簡潔に表したラベル}|{タスク名}
```

例: `DBTリンター適用見直し|リリース`

- 「PBIを簡潔に表したラベル」は、親 PBI の Title（[scrum-notion-pbi](../scrum-notion-pbi/SKILL.md) の Title 命名規則を参照）から `yyyymmdd` とプロジェクト名を除いた「内容」部分をそのまま使う。
- 同一 PBI 配下の複数 Task では、このラベル部分をすべて揃える。
- 区切り文字は半角 `|`。

---

## ワークフロー概要（設計）

```
ステップ0: Product Backlog（親PBI）を特定する
     ↓
ステップ1: Name / Planned Hours / Category をヒアリングする（未指定分のみ）
     ↓
ステップ2: Planned Date の要否を確認する（定型/会議なら入力、単発ならnull）
     ↓
ステップ3: Status を自動判定する（Planned Date の有無で New/Ready）
     ↓
ステップ4: Member=Ueki Masaya, Acutual Hours=0 を固定値として設定する
     ↓
ステップ5: 作成前プレビューをユーザーに提示し、確認を取る
     ↓
ステップ6: notion-create-pages で Task データソース配下に作成（contentなし）
```

### ステップ0: Product Backlog を特定する

- ユーザーに対象 PBI を確認する。
- Product Backlog データベース（`collection://ec5e41b3-3c58-4b2b-acf8-9fc0655f094d`）を `query_data_sources` で検索し、`Title` が一致/部分一致するページを候補として提示する（[scrum-notion-pbi](../scrum-notion-pbi/SKILL.md) のステップ0と同様の要領）。

### ステップ1〜4

- 上記「入力パラメータと決定方法」に従う。`Name` は呼び出し時に渡されていればそれを使い、無ければその場でヒアリングする。

### ステップ5: 作成前プレビュー

- `Name` / `Product Backlog` / `Planned Hours` / `Category` / `Planned Date` / `Status`（自動判定結果） をユーザーに提示し、承認を得てから作成する（Notion への書き込みは不可逆に近いため）。

### ステップ6: 作成

- `notion-create-pages` を用いて Task データソース（`collection://cdcc51b0-9c05-4c0a-9250-5329894f94c1`）配下にページを作成する。
- content は指定しない（本文テンプレートなし）。

---

## 使用する Notion MCP ツール

| ツール | 用途 |
|---|---|
| `notion-query-data-sources` | Product Backlog 検索 |
| `notion-create-pages` | Task ページ作成 |
| `notion-fetch` | 作成後の確認・スキーマ再確認 |

---

## 未確定・今後の検討事項

- 定型タスク・会議の繰り返し作成ロジックは別途検討する。
- Task 完了時のステータス遷移（Ready → In Progress → Done 等）や Actual Hours 更新のフローは本スキルの対象外。
- 進捗ログを親 PBI 本文へ追記する具体的な運用（どのセクションに追記するか等）は別途設計する。
- Member を固定値とする現方針は Ueki Masaya 単独運用が前提。複数メンバー運用になった場合は要見直し。
