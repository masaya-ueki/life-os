# ADR-0015: 収益組織を life-os 内に置き、売り物だけを別リポジトリへ切り出す

- **ステータス**: `承認済み`
- **決定日**: 2026-08-14
- **決定者**: masaya-ueki
- **関連タスク**: #123 / #124

---

## コンテキスト

Claude Code を使って収益を上げるため、Claude のサブエージェント群で構成する「組織」を持ちたい。
このとき最初に決めなければならないのが **その組織をどのリポジトリに置くか** である。一度置き場所を決めると、
エージェント定義・運用ルール・収益データ・Issue 履歴がその場所に蓄積されるため、後からの移設コストが高い。

判断にあたっての前提は次の 3 点。

1. **組織の実体はコードではない。** 実体は `.claude/agents/` のエージェント定義・`.claude/skills/` のスキル・
   運用ルール（誰が何を入力にして何を出力するか）である。
2. **life-os には組織の実行基盤がすでに揃っている。** `issue-loop`（Issue → 実装 → PR）、`pr-reviewer` /
   `review-and-merge-pr`（レビュー → 検証 → マージ）、`close-task` / `continuous-learning`（知見の蓄積と昇華）、
   さらに `.importlinter` / `scripts/check_structure.py` / `directory-keeper` という
   「AI に自律的に書かせても構造が崩れないガードレール」がある。
3. **life-os は個人の私物リポジトリである。** 旅行・英語学習・資格勉強・メディア管理が同居しており、
   公開を前提としていない。

また [ADR-0002](./0002-modular-monolith-bounded-context.md) の Bounded Context として
`content-sales`（販売管理）がすでに定義済みで、スケルトンのまま空いている。収益の数字を置く器は既にある。

一方で、収益組織が生み出す**売り物そのもの**は性質が異なる。外部公開・ライセンス・デプロイ用シークレット・
顧客向けの Issue や問い合わせを伴う可能性があり、これらを私物リポジトリに混ぜると後から分離できない。

つまり「組織」と「売り物」は置き場所の要件が違う、というのがこの ADR が扱う論点である。

なお、**この repo には「育った領域を独立リポジトリへ昇格させる」先例がすでにある**。
[ADR-0014](./0014-deprecate-certification-own-repo.md) で `certification` 領域が独自ツールチェーン・独自デプロイを
持つに至った時点で独立リポジトリへ移管され、life-os 側の実体は削除された。
本 ADR が採る方針は、その昇格パターンを**売り物に対してあらかじめ宣言しておく**ものであり、新しい発明ではない。

## 決定事項

**収益組織（意思決定・エージェント・運用ルール・収益管理）は life-os 内に置く。**
組織が生む**売り物（外部公開するプロダクト）だけを、最初の 1 つが公開判断に至った時点で別リポジトリへ切り出す。**
この 2 層構成を採り、最初から売り物用のリポジトリを用意することはしない。

```
life-os（private）              ← 組織・意思決定・収益管理【正本】
├── .claude/agents/biz-*            組織のメンバー（エージェント）
├── .claude/skills/                 既存の loop 資産を実行基盤として再利用
├── guides/business/                組織の運用ルール（役割・loop・歯止め）
└── domains/content-sales/          売上・コスト・KPI（ADR-0002 の Bounded Context）

product-xxx（別リポジトリ）      ← 売り物。公開判断に至った時点で切り出す
```

あわせて、**新しい `system:` ラベル（`business` 等）は追加しない**。収益組織が扱う数字は `content-sales`
領域の概念であり、`system:` ラベルは Bounded Context と 1:1 で対応させる運用（[ADR-0002](./0002-modular-monolith-bounded-context.md)）のため、
新設は境界の二重定義になる。組織横断のインフラ変更は `system: common`、収益の数字は `system: content-sales` を使う。

## 検討した選択肢

### 選択肢A: 2 層構成 — 組織は life-os、売り物だけ別リポジトリ（採用）

- **メリット**:
  - 既存の loop 資産（`issue-loop` / `pr-reviewer` / `close-task` / `continuous-learning`）とガードレール
    （`.importlinter` / `check_structure.py` / `directory-keeper`）を**そのまま組織の実行基盤として使える**。
  - 収益データの器（`content-sales`）が既にあり、新しい Bounded Context を作らずに済む。
  - [Loop Engineering](../../guides/development-policy/loop-engineering.md) が掲げる Stage 3 に対して、
    欠けていた「**外部からのフィードバック（売上）**」を loop に接続できる。組織はこの指針の延長線上にある。
  - 私物と公開物の分離線を、後から**必要になった時点で**引ける。
- **デメリット**:
  - 売り物を切り出す際、履歴の分離作業が発生する（ただし切り出し対象は 1 プロダクト分に限定される）。
  - life-os の関心事が 1 つ増える（旅行・英語などと同居する）。

### 選択肢B: 収益組織ごと新規リポジトリを作る（不採用）

- **メリット**:
  - 収益に関するものが 1 箇所にまとまり、将来チームに開く場合の分離が容易。
  - life-os の私的な内容と完全に切り離せる。
- **デメリット**:
  - **組織の実行基盤をすべて作り直しになる。** `issue-loop` / `pr-reviewer` / `close-task` /
    `continuous-learning` / `directory-keeper` / `.importlinter` / Issue 運用ルール / ラベル体系 / Issue テンプレート
    ——これらは life-os で数十 Issue かけて育てた資産で、組織の価値の大半はここにある。
  - 資産をコピーすると二重管理になり、片方だけが育って乖離する（[R-DOC-1 単一の真実](../../rule/documentation.md)違反を
    リポジトリ間で起こす）。
- **不採用理由**: 新リポジトリで最初に発生する作業が「life-os の loop 資産の再構築」になる。
  **収益を生むための試行を始める前に、基盤の作り直しに時間を使うことになる**ため。
  分離の必要性はまだ発生しておらず、必要になったときに引けばよい（YAGNI）。

### 選択肢C: すべて life-os 内で完結させる（売り物も切り出さない）（不採用）

- **メリット**:
  - リポジトリが 1 つで済み、最も単純。切り出し作業が永遠に発生しない。
- **デメリット**:
  - 売り物を公開する段階で、私物リポジトリ全体を公開するか、履歴ごと分離するかの二択を迫られる。
  - 外部公開用のシークレット・CI・ライセンス・顧客向け Issue が個人の生活データと同じ場所に混ざる。
- **不採用理由**: 公開の瞬間に不可逆な選択を強いられる。**分離線をあらかじめ宣言しておくこと自体が安全装置**になるため、
  切り出し方針を先に決めておく選択肢A を採る。

## 結果・トレードオフ

**得られるもの**

- 収益 loop（仮説 → 実装 → 公開 → 売上 → 経営判断 → 次の仮説）を、既存の loop 資産の上に**追加するだけ**で構築できる。
  新規に作るのは欠けている両端（仮説の入口 `biz-market-scout`、公開の出口 `biz-launch`）のみ。
- 売上という外部フィードバックが loop の入力になり、Loop Engineering の Stage 3 に実質的に近づく。
- `content-sales` 領域が空スケルトンから脱し、`public.py` の契約が実需で埋まる。

**引き受けるコスト・注意点**

- life-os の関心事が増え、`directory-keeper` の監査対象・README の索引が広がる。
- **エージェント組織そのものは収益を生まない。** 収益を生むのは売れる商品であり、組織は試行回数を増やす装置に過ぎない。
  組織の作り込みが目的化していないかを、経営レビューで定期的に問う必要がある。
- **歯止めが必須。** 課金・外部公開・送金・実名での対外発信をエージェントに実行させない
  （[Loop Engineering](../../guides/development-policy/loop-engineering.md) の「歯止め」に該当）。
  運用ルールの正本は [guides/business/README.md](../../guides/business/README.md)。

**将来この決定を見直す条件**

- 売り物が複数になり、life-os 側の収益管理が `content-sales` 1 領域に収まらなくなったとき。
- 組織を個人以外（協業者・法人）に開く必要が生じたとき。この時点で選択肢B を再検討する。

## 関連ドキュメント・リンク

- [guides/business/README.md](../../guides/business/README.md) — 収益組織の運用ルール（役割・loop・歯止め）の正本
- [guides/development-policy/loop-engineering.md](../../guides/development-policy/loop-engineering.md) — 目指す開発スタイル
- [ADR-0002 複数領域を Modular Monolith × Bounded Context で共存させる](./0002-modular-monolith-bounded-context.md)
- [ADR-0008 PR の自動マージ/人間レビューをパスベースのスコープゲートで判定する](./0008-pr-auto-merge-scope-gate.md)
- [ADR-0014 certification 領域を廃止し独立リポジトリへ移管する](./0014-deprecate-certification-own-repo.md) — 「育った領域を独立リポジトリへ昇格させる」先例
- [rule/directory-structure.md](../../rule/directory-structure.md) — 配置ルール
