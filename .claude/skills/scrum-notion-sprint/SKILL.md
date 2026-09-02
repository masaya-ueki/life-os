---
name: scrum-notion-sprint
description: Notion の Sprint データベースに新しい Sprint を1件作成するスキル。直近Sprintから開始日・終了日を自動算出し（2週間固定・連続）、Sprint Name命名規則に従って作成する。Use when: 新しいSprintを作りたい、Sprintのホライズンを延ばしたい、scrum-notion-sprint-planningからSprint作成が必要になったとき。Triggers on: Sprint作成, scrum-notion-sprint, 新しいSprint, Sprintホライズン延長.
---

# scrum-notion-sprint スキル

Notion の **Sprint** データベースに新しい Sprint を1件作成するスキル。
命名規則は `scrum-notion-*`（[scrum-notion-pbi](../scrum-notion-pbi/SKILL.md) / [scrum-notion-task](../scrum-notion-task/SKILL.md) と同一の接頭辞）。

> 現時点はこのスキルの「器」の設計。実データベースへの書き込みロジックは、次回以降ユーザーと合意の上で実装する。

---

## スコープ（現時点）

- 対象は **Sprint の新規作成のみ**。
- 既存 Sprint の編集（`Product Backlog` relation の付け替え等）は対象外。これは Sprint Planning セレモニー全体を扱う [scrum-notion-sprint-planning](../../agents/scrum-notion-sprint-planning.md) エージェントが担当する。`Reflection notes` プロパティは本設計では使用しない（振り返りは Sprint 本文の `Retrospective` セクションで扱う想定。プロパティ自体の要否は将来見直す）。
- 通常運用は **2週間固定・月曜開始〜日曜終了・前 Sprint と連続（隙間なし）**。実データ（2025-10〜2026-12、計31件）で確認済みの安定パターン。この前提から外れる特殊な Sprint を作りたい場合は、その旨を明示的にユーザーに確認してから進める。
- Sprint のホライズン延長（新規 Sprint の事前作成）は人間が本スキルを都度実行し、**年1回1年分をまとめて作成する運用**とする。本スキル自体は1件ずつの作成のみを扱う。

---

## 参照するデータベース定義・テンプレート

- [`domains/task/docs/databases/sprint.md`](../../../domains/task/docs/databases/sprint.md) — 作成先データベース
- [`domains/task/docs/template/sprint.md`](../../../domains/task/docs/template/sprint.md) — Sprint 本文（content）テンプレート。作成時はこのテンプレートをそのまま（空のまま）本文に設定する

| データベース | Data Source URL |
|---|---|
| Sprint（作成先） | `collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e` |

---

## トリガー条件

- ユーザーが `/scrum-notion-sprint` を実行した場合
- 「Sprint 作って」「新しい Sprint を作成して」「Sprint のホライズンを延ばして」と依頼された場合
- 通常は [scrum-notion-sprint-planning](../../agents/scrum-notion-sprint-planning.md) エージェントから、対象 Sprint が存在しない場合に呼び出される想定

---

## 入力パラメータと決定方法

| プロパティ | 型 | 決定方法 |
|---|---|---|
| `Sprint Name` | title | **自動生成**。下記「Sprint Name 命名規則」に従い `Start Day` / `End Day` から組み立てる（ヒアリング不要） |
| `Start Day` | date | **自動算出 → ユーザー確認**。既定は「直近（`Start Day` が最大の）Sprint の `End Day` の翌日」。初回（Sprint が0件）の場合のみヒアリングする |
| `End Day` | date | **自動算出 → ユーザー確認**。`Start Day` の13日後（2週間固定） |
| `Reflection notes` | text | 新規作成時は未設定（空） |
| `Product Backlog` | relation | 新規作成時は未設定（空。PBI の紐付けは PBI 側の作成/更新で行う） |
| 本文（content） | - | [`domains/task/docs/template/sprint.md`](../../../domains/task/docs/template/sprint.md) をそのまま（各セクション空のまま）設定する。ヒアリング不要 |

---

## Sprint Name 命名規則

```
Sprint {Start Day: YYYY.MM.DD}-{End Day: DD}
```

例:
- `Sprint 2026.08.31-13`（Start `2026-08-31` / End `2026-09-13`）
- `Sprint 2026.12.21-03`（Start `2026-12-21` / End `2027-01-03`。月・年をまたいでも End 側は日にちの2桁のみ）

- 区切り文字は半角ハイフン。`End Day` は月・年をまたぐ場合でも常に日にち2桁のみを表記する（実データで確認済み）。

---

## ワークフロー概要（設計）

```
ステップ0: 直近 Sprint を特定する
     ↓
ステップ1: Start Day / End Day を自動算出し、ユーザーに確認する
     ↓
ステップ2: Sprint Name を組み立てる
     ↓
ステップ3: 作成前プレビューをユーザーに提示し、確認を取る
     ↓
ステップ4: notion-create-pages で Sprint データソース配下に作成
```

### ステップ0: 直近 Sprint を特定する

- Sprint データベース（`collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e`）を `Start Day` 降順で1件クエリし、直近 Sprint を取得する。
- 0件（初回作成）の場合は `Start Day` をユーザーにヒアリングする。

### ステップ1: Start Day / End Day を自動算出する

- 既定: 直近 Sprint の `End Day` の翌日を `Start Day` として提案し、その13日後を `End Day` として提案する。
- ユーザーが別日程を希望する場合は変更を受け付ける。ただし前 Sprint と連続しない（隙間/重複がある）、または2週間でない場合は、意図的なイレギュラーかを確認してから進める（憶測で通常運用から逸脱しない）。

### ステップ2〜3

- 上記「Sprint Name 命名規則」に従い `Sprint Name` を組み立てる。
- `Sprint Name` / `Start Day` / `End Day` をユーザーに提示し、承認を得てから作成する（Notion への書き込みは不可逆に近いため）。

### ステップ4: 作成

- `notion-create-pages` を用いて Sprint データソース（`collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e`）配下にページを作成する。
- properties: `Sprint Name`, `Start Day`, `End Day`（`Reflection notes` / `Product Backlog` は未設定のまま）。
- content: [`domains/task/docs/template/sprint.md`](../../../domains/task/docs/template/sprint.md) をそのまま設定する（各セクションは空のまま。Sprint Goal は後で [scrum-notion-sprint-goal](../scrum-notion-sprint-goal/SKILL.md) が埋める）。

---

## 使用する Notion MCP ツール

| ツール | 用途 |
|---|---|
| `notion-query-data-sources` | 直近 Sprint の特定 |
| `notion-create-pages` | Sprint ページ作成 |
| `notion-fetch` | 作成後の確認・スキーマ再確認 |

---

## 未確定・今後の検討事項

- 2週間固定でない特殊 Sprint（実データ上、運用初期の2025-09に短い/重複した Sprint の例あり）を作る場合の正式な運用ルールは未確定。現状は「直近運用（2025-10以降）の2週間固定パターンを既定とし、逸脱時は都度確認」という方針のみ。
- `Product Backlog` relation の更新は本スキルの対象外（[scrum-notion-sprint-planning](../../agents/scrum-notion-sprint-planning.md) が担当）。
- 本文テンプレート導入前に作成済みの既存 Sprint（本文テンプレートを持たない）への遡及適用は本スキルの対象外。[scrum-notion-sprint-goal](../scrum-notion-sprint-goal/SKILL.md) 側でテンプレート未適用時のフォールバックを扱う。
