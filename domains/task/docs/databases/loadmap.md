# Notion: Loadmap データベース定義

> リリース時期を軸にした計画（ロードマップ）を表すデータベース。データベース名の表記は Notion 側の原文ママ `Loadmap`（`Roadmap` ではない）。
> [product-backlog.md](./product-backlog.md) の `Loadmap` relation から参照される。

## 基本情報

| 項目 | 値 |
|------|------|
| データベース名 | Loadmap |
| データベース URL | https://app.notion.com/p/2625f750ec0580bcbc91f114ccf97d7c |
| Data Source URL | `collection://2625f750-ec05-80f2-b4e3-000bd3a055d6` |
| アイコン | `/icons/map_yellow.svg` |

## プロパティ定義

| プロパティ名 | 型 | 内容 |
|---|---|---|
| `Loadmap` | title | ロードマップ項目のタイトル |
| `Release` | date | リリース予定日（`YYYY/MM/DD`、時刻 `H:mm`） |
| `Project` | relation（単一, limit 1） | 関連 Project → `collection://b270c90b-09d5-4a6c-8c9a-f660442743e0` |
| `Product Backlog` | relation（複数） | 紐づく PBI 一覧 → `collection://ec5e41b3-3c58-4b2b-acf8-9fc0655f094d` |

> `notAvailableInQuerySql` の指定なし＝上記プロパティはすべて SQL クエリ可能。

## SQLite テーブル定義

```sql
CREATE TABLE IF NOT EXISTS "collection://2625f750-ec05-80f2-b4e3-000bd3a055d6" (
    url TEXT UNIQUE,
    createdTime TEXT,
    "Project" TEXT, -- Project データソースへの relation（単一）
    "date:Release:start" TEXT,
    "date:Release:end" TEXT,
    "date:Release:is_datetime" INTEGER,
    "Product Backlog" TEXT, -- JSON配列、PBI relation
    "Loadmap" TEXT
)
```

## 取得元

- MCP: `notion-fetch`（`collection://2625f750-ec05-80f2-b4e3-000bd3a055d6`）
- 取得日: セッション内取得（2026-08-04 時点の Notion 側スキーマ）
