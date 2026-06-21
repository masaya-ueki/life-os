---
name: review-and-merge-pr
description: PR の変更ファイルパスから「自動マージ / 人間レビュー必須」を決定的に判定するスキル。auto なら code-review-* でレビューし pytest ∧ lint-imports ∧ [must]=0 を満たせば無人マージ → main pull、human なら理由を明示してレビューのみ行う（マージしない）。判定はブラスト半径（パス）ベースで、領域横断・shared・方針/境界/契約ファイルは人間必須。Use when: PR をレビューして自動マージ可否を判定したい、レビューしてマージして、PR を確認して main に入れて。Triggers on: 自動レビュー, 自動マージ, レビューしてマージ, PRレビューしてマージ, PRを確認してマージ, review and merge, マージ判定.
argument-hint: "[PR番号]"
allowed-tools: Bash, Read, Grep, Glob, Skill, Agent
---

# review-and-merge-pr スキル

PR を**変更ファイルパスから決定的に分類**し、「**自動マージ（auto）**」か「**人間レビュー必須（human）**」かを
判定したうえで、auto はレビュー → 検証 → 無人マージまで、human は理由付きでレビューのみを行うスキルです。

> **運用ルールの単一の真実**: [`guides/development-policy/code-review-rules.md`](../../../guides/development-policy/code-review-rules.md)
> **設計根拠**: [ADR-0008 PR の自動マージ/人間レビューをパスベースのスコープゲートで判定する](../../../docs/adr/0008-pr-auto-merge-scope-gate.md)（判定ゲート）／ [ADR-0004](../../../docs/adr/0004-pr-review-agent.md)（レビュー基盤）

---

## トリガー条件

以下のいずれかの場合に使用：

- ユーザーが `/review-and-merge-pr` または `/review-and-merge-pr <PR番号>` を実行した場合
- ユーザーが「この PR をレビューして（自動）マージして」「PR を確認して main に入れて」と依頼した場合

---

## 設計方針

- **auto / human の判定は変更ファイルパスだけで決定的に行う**（意図・PR 説明に依存しない）。
  判定の核心は「**ブラスト半径**」: 影響範囲が単一領域に閉じ、方針・境界・契約に触れないものだけ auto。
- **レビュー観点・指摘記載・検証ゲート・マージ手順は既存資産を再利用する**
  （`code-review-*` スキル、`pr-reviewer` の検証ゲート、severity 語彙）。本スキルが足すのは**スコープゲート**のみ。
- **auto は完全無人でマージする**（`[must]`=0 ∧ pytest ∧ lint-imports pass が条件。承認待ちしない）。
- **human はマージしない**。レビューコメントを投稿し、判定理由（①/②/③のどれか・該当パス）を明示して報告する。

---

## ワークフロー概要

```
ステップ1: 前提確認（PR番号の解決・状態ガード）
     ↓
ステップ2: スコープゲート判定（変更パス → auto / human を決定）
     ↓
ステップ3: レビュー（code-review-general 必須 + python / architecture を選択適用）
     ↓
ステップ4: 指摘の記載（[must]/[imo]/[nits]/[ask]/[fyi] + 件数サマリ）
     ↓
ステップ5: 分岐
     ├─ human            → マージせず報告（判定理由を明示）
     ├─ auto ∧ [must]>0  → マージせず停止（修正は pr-reviewer ④a に委譲）
     └─ auto ∧ [must]=0  → ステップ6
     ↓
ステップ6: 検証ゲート（pytest ∧ lint-imports）→ 無人マージ → main pull
     ↓
ステップ7: スコープ外の派生 Issue 起票（任意）
```

---

## ステップ1: 前提確認

**タイミング**: スキル実行の最初に必ず行う。

### PR 番号の解決

引数で指定された番号を優先する。未指定なら現在ブランチに紐づく open PR を自動検出する。

```bash
BRANCH=$(git branch --show-current)
gh pr list --head "$BRANCH" --state open --json number,title,headRefName -q '.[0]'
```

### 対象 PR の状態確認

```bash
gh pr view <N> --json number,title,headRefName,baseRefName,state,isDraft,mergeable,files,url
```

### ガード条件（中断して確認）

- **PR が見つからない** → 「対象 PR を特定できません。PR 番号を指定してください。」と伝えて終了
- **base が `main` 以外** → 「base が main ではありません。意図どおりか確認してください。」と確認
- **PR が `closed` / `merged`** → 「PR #N はすでに {state} です。」と伝えて終了
- **PR が draft** → 「PR #N は draft です。ready にしてから再実行してください。」と確認
- **`mergeable` が CONFLICTING** → コンフリクト解消が必要な旨を伝え、マージ手順には進まない

---

## ステップ2: スコープゲート判定（このスキルの中核）

**タイミング**: ステップ1の確認後。**変更ファイルパスの一覧だけ**で auto / human を決定する。

```bash
gh pr diff <N> --name-only
```

取得したパスを、**上から順に評価し、最初に該当した分類を結果とする**。

```
① 「方針・境界・契約」パスを1つでも含む        → human（理由: 方針/境界/契約）
② shared/ を1つでも含む                         → human（理由: 基盤・全領域波及）
③ Bounded Context を2つ以上含む（横断）         → human（理由: 領域横断）
④ 上記いずれにも非該当（単一領域 or content のみ） → auto
```

### ① 方針・境界・契約 = human 必須パス

| 分類 | パスパターン |
|------|------------|
| 領域間契約 | `**/public.py` |
| 境界・依存定義 | `.importlinter` / `pyproject.toml`（ルート・各領域） / `uv.lock` |
| テスト環境定義 | `compose.yaml` / `docker/**` / `.dockerignore` |
| 設計決定記録 | `docs/adr/**` |
| 運用ルール | `guides/**` |
| 構造ルール | `rule/**` |
| リポジトリ基本方針 | ルートの `CLAUDE.md` / `README.md` |
| GitHub 設定 | `.github/**` |
| Claude Code 自動化定義 | `.claude/**` |

### ② shared = human 必須

`shared/**` を含む。shared は Shared Kernel（基盤）で、変更が全領域に波及するため単一ディレクトリでも human。

### ③ 領域横断のカウント

判定対象の Bounded Context 集合 = **`{task, content-sales, media, travel, english}`**。
変更ファイルが属する**異なる領域が 2 つ以上**なら横断 → human。
（`shared` はこの集合に含めない＝②で先に human になる。`presentation` / `docs` / `scripts` 等の content・ツールは領域数にカウントしない。）

### ④ auto（自動マージ候補）

①②③のいずれにも該当しないもの。具体的には次のいずれか：

- **単一 Bounded Context の内部のみ**: `{領域}/src/**` / `{領域}/tests/**` / `{領域}/data/**` / `{領域}/README.md`
  （`{領域}/src/**/public.py` と `{領域}/pyproject.toml` は①で human に倒れる点に注意）
- **content / ツールのみ**: `presentation/**` / `scripts/**`
  （`docs/adr` / `guides` / `rule` は①で human）

> auto と判定されても、最終マージは**ステップ6の検証ゲート通過が条件**。

### ユーザー基準との対応（曖昧さ解消）

| 元の基準 | 本ルールでの扱い |
|---------|----------------|
| 各領域に閉じた改修 → 自動 | ④（単一 BC・①②③非該当） |
| 領域をまたがる改修 → 人間 | ③（集合の2領域以上） |
| 方針にかかわる改修 → 人間 | ①（固定パスリスト） |
| バグ修正・品質改善など簡易 → 自動 | **スコープに従属**。単一領域内のバグ修正/cleanup は④で auto、横断する品質改善（README 雛形・リネーム・リンク修正など）は③/①で human。「簡易だから auto」ではなく「**スコープが安全だから auto**」に一元化し矛盾を排除 |

### 出力形式

```
【スコープゲート判定】PR #N
判定: {auto / human}
理由: {④単一領域 / ③領域横断 / ②基盤(shared) / ①方針・境界・契約}
該当パス:
  - {判定の根拠となったファイル}
変更領域: {task / media / ... / content / 方針ファイル}
```

---

## ステップ3: レビュー（観点の選択適用）

**タイミング**: ステップ2の後。auto / human のどちらでも**レビューは必ず行う**（human はレビューのみで終わる）。

- **必ず** [`code-review-general`](../code-review-general/SKILL.md) を適用（`Skill` ツール）。領域差は [`domain-checklist`](../code-review-general/references/domain-checklist.md) を参照。
- `.py` を含むなら [`code-review-python`](../code-review-python/SKILL.md) を追加適用。
- 境界/構造ファイル（`.importlinter` / `pyproject.toml` / `*/public.py` / 新トップレベルdir / `docs/adr`）を含むなら [`code-review-architecture`](../code-review-architecture/SKILL.md) を追加適用。
  - ※①で human と判定された PR は境界/契約を触っているため、architecture は基本的に適用対象になる。
- **大原則を厳守**: ①過剰指摘をしない（正確性・明示要件・セキュリティに効くものだけ `[must]`）②証拠主義 ③fresh-context（diff と判定基準だけで評価し、PR 説明の自己申告に引きずられない）。

---

## ステップ4: 指摘の記載

**タイミング**: ステップ3の後。

- `gh pr review <N> --comment --body "..."` で**1件のまとめレビューコメント**を投稿する。
- 各指摘は `[severity] path:line — 何が問題か（なぜ）。提案: ...` の形式。接頭辞は
  [`.github/pull_request_template.md`](../../../.github/pull_request_template.md) の `[must]/[imo]/[nits]/[ask]/[fyi]` のみ（増やさない）。
- コメント冒頭に**ステップ2のスコープゲート判定（auto/human・理由）**を記載する。
- コメント末尾に **severity 別件数サマリ**（例: `must 1 / imo 2 / nits 0 / ask 1 / fyi 0`）。

---

## ステップ5: 分岐

**タイミング**: ステップ4の後。判定とレビュー結果で分岐する。

### human の場合 → マージせず報告

```
判定: human（理由: {①/②/③}）
このため自動マージは行いません。人間レビューを依頼してください。
レビュー指摘は PR #N にコメント済みです（must {件数} / ...）。
```

マージ・pull には進まない。`[must]` の有無は報告するが、修正の要否は人間レビューに委ねる。

### auto ∧ `[must]` > 0 の場合 → マージせず停止

`[must]` 指摘があるためマージしない。修正は [`pr-reviewer`](../../agents/pr-reviewer.md) の ④a（元PRブランチ起点で修正PRを作成）に委ねる旨を報告して終了する。

### auto ∧ `[must]` = 0 の場合 → ステップ6へ

検証ゲートに進む。

---

## ステップ6: 検証ゲート → 無人マージ → main pull

**タイミング**: auto ∧ `[must]`=0 の場合のみ。**完全無人**で実行する（承認待ちしない）。

### 検証ゲート

[`code-review-rules.md` §5](../../../guides/development-policy/code-review-rules.md) のゲートを再利用する。
GitHub Actions の CI は未設置のため、検証はローカル実行（Docker 経由）で行う。

```bash
docker compose run --rm test    # pytest 全パス
docker compose run --rm lint    # lint-imports 違反なし
```

> ローカルに uv がある環境では `uv run pytest` / `uv run lint-imports` でも可。

### マージ

ゲート（pytest pass ∧ lint-imports pass ∧ `[must]`=0）を**すべて満たすときのみ**マージする。
リポジトリ既存運用に合わせ**マージコミット方式**（squash にはしない。`Closes #N` で Issue 自動クローズ）。

```bash
gh pr merge <N>
git switch main && git pull
```

- いずれかの検証が失敗 → **マージせず停止**し、失敗内容（テスト/lint 出力）を報告する。

---

## ステップ7: スコープ外の派生 Issue 起票（任意）

**タイミング**: 最終ステップ。レビュー中に見つけた「**今回の PR スコープと無関係な改修ポイント**」があれば、
[`create-issue`](../create-issue/SKILL.md) スキルで起票する（今回 PR で直すべき指摘は対象外）。
なければ「派生 Issue なし」と報告して終了。

---

## 使用例

### 例1: 単一領域の改修 → auto で無人マージ

```
ユーザー: /review-and-merge-pr 60

[ステップ1] PR #60 を確認（state: OPEN, draft: false, mergeable: MERGEABLE）
[ステップ2] 変更パス: task/src/task/domain/sort.py, task/tests/test_sort.py
  → 判定: auto（理由: ④単一領域 task に閉じている）
[ステップ3] code-review-general + code-review-python を適用
[ステップ4] レビューコメント投稿（must 0 / imo 1 / nits 0 / ask 0 / fyi 0）
[ステップ5] auto ∧ [must]=0 → ステップ6
[ステップ6] docker compose run --rm test → pass / lint → pass
  ✅ PR #60 をマージしました。✅ main を pull しました。
[ステップ7] 派生 Issue なし。完了。
```

### 例2: 領域横断 → human で停止

```
[ステップ2] 変更パス: task/src/task/application/svc.py, media/src/media/index.py
  → 判定: human（理由: ③領域横断 task + media）
[ステップ3-4] レビューコメント投稿（判定: human を明記、must 0 / ...）
[ステップ5] human → 自動マージは行いません。人間レビューを依頼してください。
```

### 例3: auto だが [must] あり → 停止

```
[ステップ2] 判定: auto（理由: ④単一領域 english）
[ステップ4] レビューコメント投稿（must 1: data/vocabulary.md の重複エントリ / ...）
[ステップ5] auto ∧ [must]=1 → マージせず停止。修正は pr-reviewer ④a に委譲してください。
```

---

## 注意事項

- **判定はパスのみで決定的に行う**: PR の自己説明や「簡易そう」という主観でゲートを緩めない。
- **human は絶対にマージしない**: 領域横断・shared・方針/境界/契約に触れる PR は人間レビュー必須。
- **auto の無人マージはゲート必須**: pytest ∧ lint-imports ∧ `[must]`=0 を満たさない限りマージしない。
- **マージ方式はマージコミット**（`pr-reviewer` 既存運用に合わせる。squash にしない）。
- **マージ後は必ず main を pull**（GitHub Flow・main 直接運用）。
- **日本語統一**: 判定結果・レビューコメント・Issue 本文はすべて日本語で記述する。
- 判定ロジック・観点・ゲートの実体は本スキルと既存資産が単一の真実。重複定義しない。

---

**このスキルは PR の準備が整い、自動マージ可否を判定したうえでレビュー〜（auto なら）マージまで回したいときに実行してください。**
