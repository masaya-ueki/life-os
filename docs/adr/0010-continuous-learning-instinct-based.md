# ADR-0010: Continuous Learning — instinct ベースの段階的学習機構

- **ステータス**: `承認済み`
- **決定日**: 2026-06-21
- **決定者**: masaya_ueki
- **関連タスク**: （なし）

---

## コンテキスト

Claude Code のセッションは `/clear` でコンテキストがリセットされる。
開発中に得られる「行動パターン（次回も同じ判断をすべき再発性の知見）」はセッションをまたいで蓄積されるべきだが、既存の auto memory（`memory/MEMORY.md`）は「事実・人物像」を対象とした仕組みであり、行動パターンの管理には向いていない。

具体的な課題：
- 「領域間連携は必ず public.py 経由」のような設計判断を毎回説明し直す手間がある
- Docker 経由テストという運用ルールが浸透するまでに時間がかかる
- PR レビューで得た学びが次のセッションでは消えてしまう

これを解決するため、**instinct（行動パターン）** を auto memory とは別に管理し、confidence スコアで品質を保ちながら最終的に team artifact（skill / rule / ADR）へ昇華する仕組みが必要と判断した。

## 決定事項

`/learn` `/instinct-status` `/evolve` の 3 コマンドと `continuous-learning` スキルを導入する。observation → instinct YAML（personal scope）→ team artifact（Git 管理）という段階的な進化フローを手動トリガーで運用する。

## 検討した選択肢

### 選択肢 A: instinct ベース手動トリガー（採用）

- **メリット**: 低品質な観測の蓄積を防げる。ユーザーが意図的に「重要な気づき」を選別するため、信号対雑音比が高い。confidence スコアで昇華タイミングを制御できる。
- **デメリット**: 手動なのでセッション末尾に `/learn` を忘れると蓄積されない。

### 選択肢 B: auto memory に行動パターンも混在させる（不採用）

- **メリット**: 新しいインフラが不要。
- **デメリット**: 事実と行動パターンが混在して可読性が落ちる。昇華（team scope への移行）の仕組みが作れない。
- **不採用理由**: 概念の分離と昇華フローが実現できない。

### 選択肢 C: PostToolUse hook による全自動観測（不採用）

- **メリット**: 忘れずに記録できる。
- **デメリット**: 低品質な観測が大量に蓄積される。どの観測が「重要な気づき」かをフィルタリングするコストが高い。
- **不採用理由**: MVP では品質を優先し手動にする。自動化は v2 で段階導入する。

## 結果・トレードオフ

**メリット**:
- セッションをまたいだ知見の継続的蓄積が可能になる
- confidence スコアによる品質管理で「よい instinct だけが昇華する」
- personal scope → team scope の段階により、個人の試行錯誤を組織知化できる

**デメリット・注意点**:
- `/learn` を意識的に実行する運用規律が必要
- instinct ディレクトリは Git 管理外のため、開発環境を変えると引き継げない
- 同一 ID の採番（`<domain>-<verb>-<object>`）を一貫させないと confidence が蓄積されない

**将来の見直し条件**:
- instinct が 50 件を超えて検索コストが増大した場合 → 自動クラスタリングを検討
- 手動実行の忘れが多い場合 → v2（Stop hook による半自動発火）を前倒しで実装

## 関連ドキュメント・リンク

- [docs/ai/continuous-learning.md](../ai/continuous-learning.md) — 思想設計の詳細
- [.claude/skills/continuous-learning/SKILL.md](../../.claude/skills/continuous-learning/SKILL.md) — スキル定義
- [.claude/commands/learn.md](../../.claude/commands/learn.md) — `/learn` コマンド
- [.claude/commands/instinct-status.md](../../.claude/commands/instinct-status.md) — `/instinct-status` コマンド
- [.claude/commands/evolve.md](../../.claude/commands/evolve.md) — `/evolve` コマンド
