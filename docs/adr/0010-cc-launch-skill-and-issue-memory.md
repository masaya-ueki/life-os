# ADR-0010: 作業起動フローをモード選択式スキル + Issue 自動読み込みで標準化する

- **ステータス**: `承認済み`
- **決定日**: 2026-06-21
- **決定者**: masaya_ueki
- **関連タスク**: #54

---

## コンテキスト

作業セッションを開始するたびに以下を手動で判断していた：

1. **モデル選択**: Sonnet と Opus のどちらで進めるか
2. **Issue 読み込み**: 対象 Issue の背景・方針・完了条件を読む
3. **進め方**: 計画を立ててから実装するか、直接実装するか

判断基準が明文化されていないため、セッションごとに判断の質にばらつきが生じていた。
また、`all_common_data_analysis_platform` では `/cc-launch` + `issue-memory` スキルで
この問題を解決していることが確認できた。

## 決定事項

作業起動を `/cc-launch <モード> [Issue番号]` コマンドに一本化し、
`issue-memory` スキルで Issue の自動読み込みを行う。
モードは `plan` / `simple` / `interactive` / `fable` の 4 種類とし、
`plan` モードでは Sonnet / Opus の推奨モデルを自動判定する。

## 検討した選択肢

### 選択肢A: /cc-launch + issue-memory スキルを導入（採用）

- **メリット**:
  - 「どのモードで・どのモデルで」の判断を明文化し、毎回一貫した判断ができる
  - `all_common_data_analysis_platform` での実績があり、移植コストが低い
  - Issue の読み込みが自動化されるため、前のセッションのコンテキストを素早く復元できる
- **デメリット**:
  - スキルのメンテナンスコストが生じる
  - モデル判定の基準が陳腐化する可能性がある

### 選択肢B: 現状維持（毎回手動で判断）（不採用）

- **メリット**: 運用コストゼロ
- **デメリット**: 判断の質にばらつきが残る
- **不採用理由**: 繰り返し行う判断の標準化はLoop Engineering の基本原則に沿う

### 選択肢C: モード選択なし・Issue 自動読み込みのみ（不採用）

- **メリット**: 実装がシンプル
- **デメリット**: モデル選択の判断基準が明文化されない
- **不採用理由**: モデル選択の基準化が主要な課題であり、それを省略する意義が薄い

## 結果・トレードオフ

**メリット:**
- セッション開始の判断が標準化され、ばらつきが減る
- 「Opus が計画し、Sonnet が実装する」分業パターンを明示的に活用できる
- Issue の読み込みが自動化されセッション復元が速くなる

**デメリット・注意点:**
- モデル判定の基準（ステップ数しきい値・思考量定義）は将来見直しが必要になる可能性がある
- Fable モデルは現時点で実験的機能のため、利用時は最新仕様を確認すること

**将来の変更条件:**
- Claude Code の標準機能（Agent View / Agent Teams / worktree）が大きく変わった場合
- life-os のドメイン構成が増え、モデル判定の「思考量」基準を更新する必要が生じた場合

## 関連ドキュメント・リンク

- [.claude/skills/cc-launch/SKILL.md](../../.claude/skills/cc-launch/SKILL.md)
- [.claude/skills/issue-memory/SKILL.md](../../.claude/skills/issue-memory/SKILL.md)
- [guides/development-policy/loop-engineering.md](../../guides/development-policy/loop-engineering.md)
- 参考: `all_common_data_analysis_platform` ADR-0017（cc-launch スキルの原典）
