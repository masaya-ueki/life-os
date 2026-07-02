# スキーマ・採番規約・整合性ルール

問題データ `domains/certification/data/snowpro_core.json` の厳密仕様と、登録手順。

## JSON スキーマ

トップレベルは 3 キー。

```jsonc
{
  "certification": { "id": "snowpro-core", "code": "COF-C03", "name": "Snowflake SnowPro Core" },
  "genres": [ { "id": "architecture", "name": "AIデータクラウドの機能とアーキテクチャ" } ],
  "questions": [
    {
      "id": "arch-013",                 // データ全体で一意
      "genre_id": "architecture",       // genres の id を参照
      "format": "single",               // "single" | "multiple"
      "text": "…要件を示した設問…",
      "choices": [
        { "id": "a", "text": "…", "is_correct": false, "ng_reason": "なぜ不正解か" },
        { "id": "b", "text": "…", "is_correct": true,  "ng_reason": "正解。なぜ正しいか" },
        { "id": "c", "text": "…", "is_correct": false, "ng_reason": "…" },
        { "id": "d", "text": "…", "is_correct": false, "ng_reason": "…" }
      ],
      "source_url": "https://docs.snowflake.com/en/user-guide/…",
      "explanation": "正解の核心を1〜2文で。"
    }
  ]
}
```

### フィールド仕様

| フィールド | 型 | 必須 | 規則 |
|---|---|---|---|
| `id` | string | ○ | `<接頭辞>-NNN`（3桁ゼロ詰め）。全問で一意 |
| `genre_id` | string | ○ | `genres[].id` のいずれか |
| `format` | string | ○ | `single` または `multiple` のみ |
| `text` | string | ○ | 用途理解型の設問。非空 |
| `choices` | array | ○ | ちょうど 4 件、`id` は `a`,`b`,`c`,`d` |
| `choices[].is_correct` | bool | ○ | single=1件 true / multiple=2件以上 true |
| `choices[].ng_reason` | string | ○ | 全選択肢で非空 |
| `source_url` | string | ○ | `https://docs.snowflake.com/` 始まりの一次情報 |
| `explanation` | string | ○ | 非空 |

> ローダー（`adapters/repository.py`）は必須キー欠落で `KeyError`、`format` 不正で `ValueError` を出す。それ以外（id 重複・正解数・ng_reason・source_url など）は `tests/test_data_integrity.py` が検査する。

## id 採番規約

`genre_id` ごとに**接頭辞**が異なる（既存慣習を踏襲。id ≠ genre_id）。

| genre_id | id 接頭辞 |
|---|---|
| `architecture` | `arch-` |
| `security` | `sec-` |
| `performance` | `perf-` |
| `data-loading` | `load-` |
| `data-collaboration` | `collab-` |

- 番号は接頭辞ごとの**連番**（`arch-001` から）。既存の最大番号 +1 から採番する。
- 新ジャンルを足すときは接頭辞も本表に追記する。

## 登録手順

1. 対象ジャンルの既存 id の最大連番を確認する:
   ```bash
   python3 -c "import json;d=json.load(open('domains/certification/data/snowpro_core.json'));print(sorted(q['id'] for q in d['questions'] if q['genre_id']=='data-collaboration'))"
   ```
2. 次番号から採番して `questions` 配列末尾に追記する（既存問題は変更しない）。
3. インラインで整合性を自己検査する（重複 id・正解数・ng_reason・source_url・JSON 妥当性）。
4. 検証ゲートを通す:
   ```bash
   docker compose run --rm test    # test_data_integrity.py 含む
   docker compose run --rm lint
   ```
