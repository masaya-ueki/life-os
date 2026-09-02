---
name: scrum-notion-sprint-goal
description: 対象 Sprint の Sprint Goal をユーザーにヒアリングし、文章を整形して Sprint ページ本文の「Sprint Goal」セクションに記載するスキル。Sprint は事前に先の日付まで作成済みのため、Sprint 新規作成（scrum-notion-sprint）とは別タイミング・別スキルとして運用する。Use when: Sprint Goal を決めたい、Sprint Goal を書きたい、Sprint Planning で目標を設定したいとき。Triggers on: Sprint Goal, sprint-goal, スプリントゴール, scrum-notion-sprint-goal, 目標設定.
---

# scrum-notion-sprint-goal スキル

対象 Sprint の **Sprint Goal** をユーザーにヒアリングし、文章を整形した上で Sprint ページ本文（content）の「Sprint Goal」セクションに記載するスキル。
命名規則は `scrum-notion-*`（[scrum-notion-sprint](../scrum-notion-sprint/SKILL.md) と同一の接頭辞）。

> 現時点はこのスキルの「器」の設計。実データベースへの書き込みロジックは、次回以降ユーザーと合意の上で実装する。

---

## スコープ（現時点）

- 対象は **Sprint Goal の記載のみ**。
- Sprint そのものの新規作成は対象外（[scrum-notion-sprint](../scrum-notion-sprint/SKILL.md) が担当）。Sprint は事前に先の日付まで作成済みの運用のため、本スキルは既存 Sprint に対して Sprint Goal を後から設定する用途を想定する。
- 本文の「レトロスペクティブ」セクションの記載は対象外（Sprint 終了後の振り返りで別途扱う。本スキルでは触れない）。

---

## 参照するデータベース定義・テンプレート

- [`domains/task/docs/databases/sprint.md`](../../../domains/task/docs/databases/sprint.md) — 対象 Sprint の特定に使用
- [`domains/task/docs/template/sprint.md`](../../../domains/task/docs/template/sprint.md) — Sprint 本文テンプレート。「Sprint Goal」セクションの見出しはこのテンプレートに従う

| データソース | Data Source URL |
|---|---|
| Sprint | `collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e` |

---

## トリガー条件

- ユーザーが `/scrum-notion-sprint-goal` を実行した場合
- 「Sprint Goal 決めたい」「Sprint Goal 書いて」「Sprint Planning で目標を設定して」と依頼された場合
- 通常は [scrum-notion-sprint-planning](../../agents/scrum-notion-sprint-planning.md) エージェントから呼び出される想定

---

## 入力パラメータと決定方法

| 項目 | 決定方法 |
|---|---|
| 対象 Sprint | 呼び出し時に指定されていればそれを使う。未指定なら下記「対象 Sprint の特定」に従い提案し、ユーザーに確認する |
| Sprint Goal（原文） | ユーザーへのヒアリングで取得する（自由記述） |

### 対象 Sprint の特定

- ユーザーが Sprint を明示した場合はそれを採用する。
- 未指定の場合は Sprint データベースを `Start Day` 昇順でクエリし、次の優先順で提案する（[scrum-notion-pbi](../scrum-notion-pbi/SKILL.md) の Sprint 提案ロジックと同様）。
  1. 今日の日付が `Start Day`〜`End Day` の範囲に入る Sprint（進行中）
  2. 該当が無ければ、`Start Day` が今日以降で最も近い Sprint（次回）
- 提案した Sprint をユーザーに確認してもらい、必要なら別の Sprint に変更する。

---

## Sprint Goal 整形ルール（現時点の方針）

ユーザーから受け取った原文の**意味を変えず**、以下の観点で整形する。

- 文体は常体（「〜する」「〜を目指す」等の言い切り）に統一する。
- 1〜3文程度の簡潔な宣言文にまとめる（Sprint Goal は「この Sprint で何を達成するか」を端的に表すもの）。
- 誤字脱字・口語表現・冗長な言い回しを整える程度に留め、要約による情報の欠落や意図の変更はしない。
- 原文が箇条書き等ですでに複数の要素に分かれている場合、1文にまとめるか箇条書きのまま整えるかをユーザーに確認してから決める（憶測でまとめない）。

整形後は必ずユーザーにプレビューを提示し、承認（または修正指示）を得てから本文に反映する。

---

## ワークフロー概要（設計）

```
ステップ0: 対象Sprintを特定する
     ↓
ステップ1: Sprint Goal をヒアリングする
     ↓
ステップ2: 整形する（上記ルールに従う）
     ↓
ステップ3: 整形後プレビューをユーザーに提示し、確認/修正を取る
     ↓
ステップ4: 対象Sprintの本文の状態を確認する
     ↓
ステップ5: 本文の「Sprint Goal」セクションに反映する
```

### ステップ0〜3

- 上記「入力パラメータと決定方法」「Sprint Goal 整形ルール」に従う。

### ステップ4: 対象 Sprint の本文の状態を確認する

- `notion-fetch` で対象 Sprint ページの本文を取得する。
- **テンプレート適用済み**（`## Sprint Goal` 見出しが存在する）場合 → ステップ5でそのセクションのみを書き換える。
- **テンプレート未適用**（本文が空、または `## Sprint Goal` 見出しが存在しない。本文テンプレート導入前に作成された既存 Sprint が該当しうる）場合 → ステップ5で [`domains/task/docs/template/sprint.md`](../../../domains/task/docs/template/sprint.md) の構造ごと反映する（「レトロスペクティブ」セクションは空のまま追加する）。

### ステップ5: 本文へ反映する

- `notion-update-page` を使用する。
- テンプレート適用済みの場合: `command: "update_content"` で `content_updates`（`old_str`/`new_str`）を使い、既存の「Sprint Goal」セクション（`## Sprint Goal` から次の見出し直前まで)の文字列をそのまま `old_str` とし、整形後の文章を含む同構造の文字列を `new_str` として置換する。
- テンプレート未適用の場合: `command: "insert_content"`（`position: {"type": "start"}`）または `command: "replace_content"` で、テンプレート構造（`## Sprint Goal` + 整形後の文章 + `## レトロスペクティブ`）を本文に反映する。
- 反映後 `notion-fetch` で本文を再取得し、意図通りに反映されたことを確認する。

---

## 使用する Notion MCP ツール

| ツール | 用途 |
|---|---|
| `notion-query-data-sources` | 対象 Sprint の特定 |
| `notion-fetch` | 対象 Sprint の本文状態の確認・反映後の確認 |
| `notion-update-page` | 「Sprint Goal」セクションへの反映（`update_content` / `insert_content` / `replace_content`） |

---

## 未確定・今後の検討事項

- Sprint Goal の整形粒度（どこまで要約してよいか）はユーザーの感覚によるところが大きく、現時点のルールは仮置き。運用しながら調整する。
- 本文テンプレート導入前に作成済みの既存 Sprint（本文なし）に対する遡及適用の要否・タイミングは未確定（本スキルは対象 Sprint に対して呼ばれた時点で都度フォールバック対応する方針のみ）。
- Sprint Goal の更新（既に記載済みの Sprint Goal を書き直す場合）の確認フロー（差分表示の要否等）は実装時に確定する。
