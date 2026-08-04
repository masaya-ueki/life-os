# Notion: Project データベース定義

> PBI が属するプロジェクトを表すデータベース。

## 基本情報

| 項目 | 値 |
|------|------|
| データベース名 | Project |
| データベース URL | https://app.notion.com/p/b2cb8e833c6348fab027ee231e6c4159 |
| Data Source URL | `collection://b270c90b-09d5-4a6c-8c9a-f660442743e0` |
| アイコン | `/icons/movie-camera_yellow.svg` |

## プロパティ定義

| プロパティ名 | 型 | 内容 |
|---|---|---|
| `Project Name` | title | プロジェクト名 |
| `Customer` | select | 顧客企業名を簡略化した顧客コード（正式名称は非公開）。案件追加に伴い選択肢は今後も増える運用のため、本ドキュメントでは全量を列挙しない |
| `Type` | select | `private`(brown) / `work`(yellow) |
| `Term` | date | プロジェクト期間（`YYYY/MM/DD`、範囲指定可） |
| `Project` | relation（複数） | この Project に属する PBI 一覧 → `collection://ec5e41b3-3c58-4b2b-acf8-9fc0655f094d` |
| `Memo` | relation（複数） | 別データベース「MEMO」への relation → `collection://b025a955-6c94-405f-a82e-26a58872c5cb`（旧名: `M E M Oとのリレーション（project）`。life-os の PBI 作成には無関係） |

> `notAvailableInQuerySql` の指定なし＝上記プロパティはすべて SQL クエリ可能。

## SQLite テーブル定義

```sql
CREATE TABLE IF NOT EXISTS "collection://b270c90b-09d5-4a6c-8c9a-f660442743e0" (
    url TEXT UNIQUE,
    createdTime TEXT,
    "Project" TEXT, -- JSON配列、PBI relation
    "date:Term:start" TEXT,
    "date:Term:end" TEXT,
    "date:Term:is_datetime" INTEGER,
    "Customer" TEXT, -- select、顧客コード（非公開・可変のため選択肢は列挙しない）
    "Type" TEXT,     -- one of ["private", "work"]
    "Memo" TEXT,
    "Project Name" TEXT
)
```

## 取得元

- MCP: `notion-fetch`（`collection://b270c90b-09d5-4a6c-8c9a-f660442743e0`）
- 取得日: セッション内取得（2026-08-04 時点の Notion 側スキーマ）
