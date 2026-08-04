# Notion: Product Backlog データベース定義

> PBI（Product Backlog Item）作成を対話式で進めるための一次情報。
> Notion 側の実データベースからスキーマを取得して記録したもの（手書きではない）。

## 基本情報

| 項目 | 値 |
|------|------|
| データベース名 | Product Backlog |
| データベース URL | https://app.notion.com/p/a1517cc0e2b9447f89bd59dda3bda6eb |
| 親ページ | S C R U M (https://app.notion.com/p/2625f750ec05802d9593ea2a7207fe41) |
| Data Source URL | `collection://ec5e41b3-3c58-4b2b-acf8-9fc0655f094d` |
| デフォルトページテンプレート | https://app.notion.com/p/26f5f750ec05803082c2d515085c43d5 |
| アイコン | `/icons/subtask_yellow.svg` |

## プロパティ定義

### 入力プロパティ（PBI 作成時に指定する）

| プロパティ名 | 型 | 内容 |
|---|---|---|
| `Title` | title | PBI のタイトル |
| `Status` | status | 下記「Status のグループ」を参照。既定は `New` |
| `Level` | select | 難易度/規模の目安。選択肢: `5`(yellow) / `4`(purple) / `3`(pink) / `2`(brown)。`1` は選択肢に存在しない |
| `Point` | number | ストーリーポイント。説明欄に `1 < 2 < 3 < 5 < 8`（フィボナッチ的スケール） |
| `Project` | relation（単一, limit 1） | 関連 Project → `collection://b270c90b-09d5-4a6c-8c9a-f660442743e0` |
| `Sprint` | relation（単一, limit 1） | 関連 Sprint → `collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e` |
| `Loadmap` | relation（単一, limit 1） | 関連 Roadmap → `collection://2625f750-ec05-80f2-b4e3-000bd3a055d6`（表記は "Loadmap" だが実質ロードマップ） |
| `Task` | relation（複数） | 子 Task → `collection://cdcc51b0-9c05-4c0a-9250-5329894f94c1`。PBI 1件に対し Task 複数（実例では10件） |

#### Status のグループ

| グループ | 選択肢（色） |
|---|---|
| to_do | `Ready`(blue) / `New`(default) |
| in_progress | `In Progress`(yellow) / `On Hold`(gray) |
| complete | `Done`(green) / `Cancel`(green) / `Carryover`(green) |

> `On Hold` は元々 `complete` グループだったが、実態に合わせて `in_progress` グループに変更済み（Task 側の `Status` グループ分けと整合）。

### 集計・自動プロパティ（読み取り専用 / 直接更新不可）

| プロパティ名 | 型 | 説明 |
|---|---|---|
| `Planned Hours` | formula | 計算式ベース。Task 側の計画工数を集計した値 |
| `Actual Hours` | formula | 計算式ベース。Task 側の実績工数を集計した値 |
| `Planned Hours Origin` | rollup | Task の計画工数（number）を `sum` 集計 |
| `Actual Hours Origin` | rollup | Task の実績工数（number）を `sum` 集計 |
| `Ad Hock CT` | rollup | Task の `Ad Hoc` チェックボックスを `checked` 集計 |
| `[Analysis] Ad Hoc Hours` | rollup | Task の `[Analytics] Copy Ad Hoc Hours`（formula）を `sum` 集計 |
| `[Analysis] Carryover Hours` | rollup | Task の `[Analytics] Copy Carryover Hours`（formula）を `sum` 集計 |
| `[Analytics] Copy Ad Hoc Hours` | formula | — |
| `[Analytics] Copy Carryover Hours` | formula | — |
| `[Analytics] Copy Meeting Hours` | formula | — |
| `[Analytics] Meeting Hours` | rollup | Task の `[Analytics] Meeting Hours`（formula）を `sum` 集計 |

> これら formula/rollup 系プロパティは SQLite ビュー（後述）でクエリ不可（`notAvailableInQuerySql`）。ページ作成 API でも値を直接指定できない（自動計算のため）。

## SQLite テーブル定義（`query_data_sources` で使う実クエリ可能列）

```sql
CREATE TABLE IF NOT EXISTS "collection://ec5e41b3-3c58-4b2b-acf8-9fc0655f094d" (
    url TEXT UNIQUE,
    createdTime TEXT, -- ISO-8601、自動設定
    "Sprint" TEXT,   -- Sprint データソースへの relation（単一ページURLのJSON文字列）
    "Level" TEXT,    -- one of ["5", "4", "3", "2"]
    "Task" TEXT,     -- Task データソースへの relation（ページURL配列のJSON文字列）
    "Status" TEXT,   -- one of ["Ready", "New", "In Progress", "On Hold", "Done", "Cancel", "Carryover"]
    "Loadmap" TEXT,  -- Roadmap データソースへの relation
    "Point" FLOAT,
    "Project" TEXT,  -- Project データソースへの relation
    "Title" TEXT
)
```

## 関連データソース（他データベースの Data Source ID）

| データベース | Data Source URL |
|---|---|
| Task | `collection://cdcc51b0-9c05-4c0a-9250-5329894f94c1` |
| Project | `collection://b270c90b-09d5-4a6c-8c9a-f660442743e0` |
| Sprint | `collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e` |
| Loadmap（Roadmap） | `collection://2625f750-ec05-80f2-b4e3-000bd3a055d6` |

## ビュー（View）

| ビュー名 | 種別 | フィルタ | ソート | 表示プロパティ |
|---|---|---|---|---|
| Product Backlog（既定） | table | Sprint = 特定Sprint（例示）/ Status（値未指定） | Sprint 昇順 → Title 昇順 | Status, Project, Title, Sprint, Point, Planned Hours, Actual Hours |
| Add Product Backlog | table（デフォルトページテンプレート適用） | Sprint = 特定Sprint（例示） | Sprint 降順 → Project 昇順 → Title 昇順 | Status, Title, Sprint, Point, Loadmap, Project, Level |
| Add Task | table | Sprint = 特定Sprint（例示） | Sprint 昇順 → Title 昇順 | Title, Task |
| Open | table | Status が「To-do」または「In progress」グループ / Project（値未指定） | Project 昇順 → Title 昇順 | Status, Project, Title, Sprint, Point, Planned Hours, Actual Hours |

## 取得元

- MCP: `notion-fetch`
- 対象 URL: https://app.notion.com/p/a1517cc0e2b9447f89bd59dda3bda6eb?v=27f890659afa4bf09e6044771d24279e&source=copy_link
- 取得日: セッション内取得（2026-08-04 時点の Notion 側スキーマ）
