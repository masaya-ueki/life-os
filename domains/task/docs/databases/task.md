# Notion: Task データベース定義

> Product Backlog Item（PBI）配下の子タスクを表すデータベース。
> [product-backlog.md](./product-backlog.md) の `Task` relation から参照される。

## 基本情報

| 項目 | 値 |
|------|------|
| データベース名 | Task |
| データベース URL | https://app.notion.com/p/4a20b08ceeb64e9794d30b5f8965edfe |
| Data Source URL | `collection://cdcc51b0-9c05-4c0a-9250-5329894f94c1` |
| デフォルトページテンプレート | https://app.notion.com/p/2e75f750ec0580f5bfa6dd89d79dd42b |
| アイコン | `/icons/checklist_yellow.svg` |

## プロパティ定義

### 入力プロパティ

| プロパティ名 | 型 | 内容 |
|---|---|---|
| `Name` | title | Task のタイトル |
| `Status` | status | 下記「Status のグループ」参照。既定は `New` |
| `Category` | select | `meeting`(pink) / `todo`(purple) / `task`(blue) |
| `Planned Date` | date | 予定日（`YYYY/MM/DD`、時刻 `H:mm`） |
| `Planned Hours` | number（precision 2） | 予定時間 (h) |
| `Actual Date` | date | 実績日（`YYYY/MM/DD`、時刻 `H:mm`） |
| `Acutual Hours` | number（precision 2） | 実績時間 (h) ※プロパティ名自体が `Acutual`（Notion側の原文ママのtypo） |
| `Active` | checkbox | 作業中フラグ |
| `Active At` | date | Active 開始日時（時刻 `H:mm`） |
| `Ad Hoc` | checkbox | 突発対応かどうか |
| `Note` | text | 備考 |
| `Member` | person（limit 1） | 担当者 |
| `Product Backlog` | relation（単一, limit 1） | 親 PBI → `collection://ec5e41b3-3c58-4b2b-acf8-9fc0655f094d` |
| `Parent item` | relation（自己参照, limit 1） | 親 Task |
| `Sub-item` | relation（自己参照, 複数） | 子 Task |

> `Tags`（multi_select, 300件超の他プロジェクト横断タグ）はこのタイミングで Notion 側から削除済み（life-os の PBI 運用に不要なため整理）。

#### Status のグループ

| グループ | 選択肢（色） |
|---|---|
| to_do | `New`(brown) / `Ready`(blue) |
| in_progress | `On Hold`(yellow) / `In Progress`(yellow) |
| complete | `Carryover`(green) / `Done`(green) / `Cancelled`(green) |

> Product Backlog の Status とは選択肢が微妙に異なる（`Cancel` ではなく `Cancelled`、`On Hold` が `in_progress` グループ）。

### 集計・自動プロパティ（読み取り専用）

| プロパティ名 | 型 | 説明 |
|---|---|---|
| `Project` | rollup | Product Backlog の `Project` relation を `show_unique` 集計。説明欄に「[リレーション] ProductBacklog」 |
| `Sprint` | rollup | Product Backlog の `Sprint` relation |
| `[Analytics] Ad Hoc Hours` | formula | — |
| `[Analytics] Carryover` | formula | — |
| `[Analytics] Meeting Hours` | formula | — |
| `Create Date` / `Created time` | created_time | 作成日時（2つ存在。原因不明の重複プロパティ） |
| `Update Date` | last_edited_time | 更新日時 |
| `+15 min` | button | クイック操作ボタン（+15分加算等） |

> `notAvailableInQuerySql`: `[Analytics] Carryover`, `Sprint`, `[Analytics] Meeting Hours`, `+15 min`, `Project`, `[Analytics] Ad Hoc Hours`

## SQLite テーブル定義（クエリ可能列）

```sql
CREATE TABLE IF NOT EXISTS "collection://cdcc51b0-9c05-4c0a-9250-5329894f94c1" (
    url TEXT UNIQUE,
    createdTime TEXT,
    "date:Planned Date:start" TEXT,
    "date:Planned Date:end" TEXT,
    "date:Planned Date:is_datetime" INTEGER,
    "Status" TEXT,      -- one of ["New", "Ready", "In Progress", "On Hold", "Carryover", "Done", "Cancelled"]
    "Ad Hoc" TEXT,       -- "__YES__" / "__NO__"
    "Acutual Hours" FLOAT,
    "Active" TEXT,       -- "__YES__" / "__NO__"
    "date:Actual Date:start" TEXT,
    "date:Actual Date:end" TEXT,
    "date:Actual Date:is_datetime" INTEGER,
    "date:Active At:start" TEXT,
    "date:Active At:end" TEXT,
    "date:Active At:is_datetime" INTEGER,
    "Sub-item" TEXT,     -- 自己参照 relation（配列）
    "Note" TEXT,
    "Create Date" TEXT NOT NULL,
    "Member" TEXT,       -- JSON文字列（単一ユーザーID）
    "Update Date" TEXT NOT NULL,
    "Parent item" TEXT,  -- 自己参照 relation（単一）
    "Category" TEXT,     -- one of ["meeting", "todo", "task"]
    "Product Backlog" TEXT, -- 親PBIへの relation（単一）
    "Planned Hours" FLOAT,
    "Created time" TEXT NOT NULL,
    "Name" TEXT
)
```

## 取得元

- MCP: `notion-fetch`（`collection://cdcc51b0-9c05-4c0a-9250-5329894f94c1`）
- 取得日: セッション内取得（2026-08-04 時点の Notion 側スキーマ）
