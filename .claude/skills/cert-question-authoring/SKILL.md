---
name: cert-question-authoring
description: 資格試験の問題（4択の単一/複数選択）を「用途理解型」で設計し、スキーマ準拠で問題データ（domains/certification/data/*.json）に登録するための索引スキル。設問設計原則・NG理由・公式出典・採番規約・整合性ルールを references/ に持つ。Use when: 資格問題を作成・追加・更新する、SnowPro Core の問題を書く、問題の品質基準や採番規約を確認する、snowpro-question-author が問題を生成・登録する。Triggers on: 資格問題作成, 問題作成, 問題追加, 問題登録, quiz作成, SnowPro問題, cert question, question authoring.
---

# 資格問題作成スキル（索引）

資格試験の問題を**用途理解型**（暗記でなく「どう使うか／何が必要か」を測る）で設計し、既存スキーマに厳密準拠して `domains/certification/data/*.json` に登録するための方針の索引。**実行（生成→検証→登録）は [`snowpro-question-author`](../../agents/snowpro-question-author.md) サブエージェントが担当**し、本スキルはその判断基準を提供する。

データ／スキーマの正（単一の真実）は [`domains/certification/README.md`](../../../domains/certification/README.md) と実データ `snowpro_core.json`。整合性は `domains/certification/tests/test_data_integrity.py` が `docker compose run --rm test` で機械的に強制する。

各論は `references/` に詳述する（progressive disclosure: 必要な参照だけ読む）。

---

## 参照の早見表

| 参照ファイル | 何を見るか | いつ読むか |
|---|---|---|
| [question-quality.md](references/question-quality.md) | 用途理解型の設問型・誤答(distractor)設計・NG理由・explanation の書き方・single/multiple の使い分け | 問題文と選択肢を作るとき |
| [schema-and-numbering.md](references/schema-and-numbering.md) | JSON スキーマの厳密仕様・id/genre_id 採番規約・登録前の整合性ルールと手順 | データに追記・登録するとき |
| [genre-doc-map.md](references/genre-doc-map.md) | ジャンル×主要トピック→公式ドキュメント(source_url) の被覆表 | どのトピックを出題し、どの URL を出典にするか決めるとき |

---

## 品質の大原則

1. **用途理解型を志向する**: 「*** を満たすためには何が必要か？」「どの機能／設定を使うべきか？」「なぜ X が適切か？」のように、知識の暗記でなく**使いどころの理解**を測る。単なる用語当て・数値暗記は避ける（型と例は question-quality.md）。
2. **4択**: 選択肢は必ず a–d の4件。`format` は `single`（正解ちょうど1件）か `multiple`（「当てはまるものをすべて選べ」・正解2件以上）。
3. **全選択肢に `ng_reason`**: 誤答には「なぜ不正解か」を、正解肢には「正解。〜」で理由を書く（学習フィードバックの根拠。空文字は不可）。
4. **`source_url` は公式ドキュメント**: `https://docs.snowflake.com/...` の一次情報のみ。genre-doc-map の**検証済み URL**を使い、URL を捏造しない。
5. **`explanation`**: 正解の核心を1〜2文で簡潔に。
6. **網羅性を優先**: 件数の下限より、genre-doc-map の各主要トピックを最低1問ずつ被覆することを優先する。出典が特定ページに偏らないようにする。

---

## 登録前チェックリスト

- [ ] `id` がデータ全体で一意（採番規約は schema-and-numbering.md）
- [ ] `genre_id` が `genres` に定義済み
- [ ] `choices` が a–d の4件、`format` に応じた正解数（single=1 / multiple≥2）
- [ ] すべての `choices[].ng_reason` が非空
- [ ] `source_url` が `https://docs.snowflake.com/` 始まりで、genre-doc-map の検証済み URL
- [ ] `text` と `explanation` が非空・用途理解型
- [ ] `docker compose run --rm test`（`test_data_integrity.py` 含む）と `docker compose run --rm lint` が green
