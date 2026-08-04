# Notion: Sprint データベース定義

> Sprint（時間箱）を表すデータベース。PBI はこの Sprint に紐づく（`Product Backlog.Sprint` relation）。

## 基本情報

| 項目 | 値 |
|------|------|
| データベース名 | Sprint |
| データベース URL | https://app.notion.com/p/d83cd24685004229aed9a6d304bee1ed |
| Data Source URL | `collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e` |
| デフォルトページテンプレート | https://app.notion.com/p/3085f750ec05807cbfa6e072bb01144c（"New page"） |
| アイコン | `/icons/run_yellow.svg` |

## プロパティ定義

### 入力プロパティ

| プロパティ名 | 型 | 内容 |
|---|---|---|
| `Sprint Name` | title | Sprint 名（実データ例: `Sprint 2026.06.08-21`） |
| `Start Day` | date | 開始日（`YYYY/MM/DD`、時刻 `H:mm`） |
| `End Day` | date | 終了日（`YYYY/MM/DD`、時刻 `H:mm`） |
| `Reflection notes` | text | Sprint 振り返りのメモ（旧名: `振り返りメモ`） |
| `Product Backlog` | relation（複数） | この Sprint に属する PBI 一覧 → `collection://ec5e41b3-3c58-4b2b-acf8-9fc0655f094d` |

### 集計・自動プロパティ（読み取り専用）

| プロパティ名 | 型 | 説明 |
|---|---|---|
| `Velocity` | rollup | 関連 PBI の `Point`（number）を `sum` 集計。**Sprint の実ベロシティ計測に使う** |
| `Planned Hours` | rollup | 関連 PBI の `Planned Hours`（formula）を `sum` 集計 |
| `Actual Hours` | rollup | 関連 PBI の `Actual Hours`（formula）を `sum` 集計 |
| `Carryover Hours` | rollup | 関連 PBI の `[Analytics] Copy Carryover Hours`（formula）を `sum` 集計 |
| `Ad Hoc Hours` | rollup | 関連 PBI の `[Analytics] Copy Ad Hoc Hours`（formula）を `sum` 集計 |
| `Meeting Hours` | rollup | 関連 PBI の `[Analytics] Copy Meeting Hours`（formula）を `sum` 集計 |
| `Rollup` | rollup | 関連 PBI の title を集計（用途不明、デバッグ用と推測） |
| `Add Task Template` | button | クイック操作ボタン |

> `notAvailableInQuerySql`: `Actual Hours`, `Carryover Hours`, `Planned Hours`, `Ad Hoc Hours`, `Meeting Hours`, `Add Task Template`, `Velocity`, `Rollup`（＝集計系はすべてSQLクエリ不可）

## SQLite テーブル定義（クエリ可能列）

```sql
CREATE TABLE IF NOT EXISTS "collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e" (
    url TEXT UNIQUE,
    createdTime TEXT,
    "Reflection notes" TEXT,
    "date:Start Day:start" TEXT,
    "date:Start Day:end" TEXT,
    "date:Start Day:is_datetime" INTEGER,
    "date:End Day:start" TEXT,
    "date:End Day:end" TEXT,
    "date:End Day:is_datetime" INTEGER,
    "Product Backlog" TEXT, -- JSON配列、PBI relation
    "Sprint Name" TEXT
)
```

## 取得元

- MCP: `notion-fetch`（`collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e`）
- 取得日: セッション内取得（2026-08-04 時点の Notion 側スキーマ）
