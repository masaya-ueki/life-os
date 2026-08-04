# Notion: KPAA データベース定義

> KPT のアレンジ版。Keep / Problem / Aspiration（もっとこうしたい）とそれに対する Action をまとめたデータベース。

## 運用ルール

- **概要**: KPT のアレンジ版。Keep, Problem, Aspiration（もっとこうしたい）に対する Action をまとめる
- **更新**: 思いついた際に随時入力する（Sprint 期間中いつでも追加可）
- **整理**: レトロスペクティブ（Sprint 振り返り）で Problem や Aspiration を PBI に昇華する

> [sprint.md](./sprint.md) の `Reflection notes` によるテキストの振り返りメモとは別に、KPAA は Keep/Problem/Aspiration を個別レコードとして構造化して残す位置づけ。

## 基本情報

| 項目 | 値 |
|------|------|
| データベース名 | KPAA |
| データベース URL | https://app.notion.com/p/2eb5f750ec05802987b7da06e5770db2 |
| Data Source URL | `collection://2eb5f750-ec05-8076-a363-000bbd997c95` |
| アイコン | `/icons/fireworks_yellow.svg` |

## プロパティ定義

| プロパティ名 | 型 | 内容 |
|---|---|---|
| `Title` | title | KPAA 項目のタイトル |
| `KPA` | select | `KEEP`(blue) / `PROBLEM`(pink) / `ASPIRATION`(yellow) の3分類 |
| `Action` | text | KPA に対する Action（自由記述） |
| `Status` | status | Action に対する進捗状況。下記「Status のグループ」参照 |
| `Close` | checkbox | クローズ済みかどうか |
| `Sprint` | relation（単一, limit 1） | どの Sprint での気づきか → `collection://6d0c2a31-6647-47db-8447-fad0b3b8e83e` |

#### Status のグループ

| グループ | 選択肢（色） |
|---|---|
| to_do | `NEW`(pink) / `Ready`(blue) |
| in_progress | `In progress`(yellow) |
| complete | `Done`(green) |

> `notAvailableInQuerySql` の指定なし＝上記プロパティはすべて SQL クエリ可能。

## SQLite テーブル定義

```sql
CREATE TABLE IF NOT EXISTS "collection://2eb5f750-ec05-8076-a363-000bbd997c95" (
    url TEXT UNIQUE,
    createdTime TEXT,
    "Status" TEXT, -- one of ["NEW", "Ready", "In progress", "Done"]
    "Action" TEXT,
    "Close" TEXT,  -- "__YES__" / "__NO__"
    "KPA" TEXT,    -- one of ["KEEP", "PROBLEM", "ASPIRATION"]
    "Sprint" TEXT, -- Sprint データソースへの relation（単一）
    "Title" TEXT
)
```

## 取得元

- MCP: `notion-fetch`（`collection://2eb5f750-ec05-8076-a363-000bbd997c95`）
- 取得日: セッション内取得（2026-08-04 時点の Notion 側スキーマ）
