# ADR-0004: PRレビューをエージェント＋観点別スキルで運用する

- **ステータス**: `承認済み`
- **決定日**: 2026-06-17
- **決定者**: masaya_ueki
- **関連タスク**: #11
- **置き換え**: -

---

## コンテキスト

life-os は GitHub Flow（`main` のみ）で feature ブランチ → PR → `main` マージで運用している。現状 PR レビューは人手で、観点も毎回その場任せになっている。スライド生成（`slide-*`）と同様に、レビューも **Claude Code ネイティブのエージェント＋スキル**として基盤化し、「PR内容確認 → 領域に応じた観点でレビュー → 指摘記載 → 修正点があれば PR を作成 / 問題なければマージ → `main` を pull」を一貫運用したい。

ここで決めるべき構造的な論点は次の3つで、いずれも「複数の有力な選択肢があり自明でない」「一度決めると後から変えにくい」ため ADR の対象（[ADR README の判断基準](./README.md#adr-の必要性判断基準)）に該当する。

1. **領域ごとのレビュー観点をどう構成するか**: life-os は領域（Bounded Context）ごとにレビュー観点が異なる。一方で各領域はまだスケルトン段階。
2. **指摘の記載と修正点の扱い**: 接頭辞（`[must]/[imo]/[nits]/[ask]/[fyi]`）は [`.github/pull_request_template.md`](../../.github/pull_request_template.md) に既定。修正点があったときにどこまでエージェントが踏み込むか。
3. **マージの実行ゲート**: 「問題なければマージ」をどの条件で自動化するか。マージは取り消しにくい操作。

前提として、一般的なレビュー観点を Web 調査した（#11）。「Effective Claude Code」という固有記事は確認できず、**Anthropic「Best practices for Claude Code」＋ Google Engineering Practices（The Standard of Code Review / What to look for）**を一次情報源とした。中核原則は「過剰指摘の抑制」「証拠主義」「fresh-context でのレビュー」「code health による承認」。

## 決定事項

**レビュー観点は観点軸で 3 スキルに分割し（`code-review-general`／`code-review-python`／`code-review-architecture`）、領域差は `code-review-general/references/domain-checklist.md` の早見表で表現する。** 指摘は接頭辞付きで元PRにコメントし、**`[must]` の修正点があれば修正して新規PRを作成**（元PRはマージしない）、**`[must]` が無ければ `uv run pytest` ∧ `uv run lint-imports` が pass のときのみ自動マージ → `main` pull**（検証付き自動マージ）とする。これらを統括する `pr-reviewer` エージェントを `.claude/agents/` に置く（[ADR-0003](./0003-presentation-system.md) のネイティブ配置方針に従う）。

## 検討した選択肢

### 論点1: レビュー観点の構成

#### 選択肢A: 観点軸スキル＋領域早見表（採用）
- **メリット**: `general`（言語非依存）/`python`（言語）/`architecture`（境界）の直交した軸で再利用しやすい。領域差は早見表の行追加だけで拡張でき、領域が骨格段階の現状にスキル数が見合う。`slide-expression` の「索引＋references」と設計が一致。
- **デメリット**: 「領域固有の深い観点」を持つには早見表では粒度が足りなくなる可能性（肉付けが進んだら別 ADR で見直す）。

#### 選択肢B: 索引1本＋領域別 references（不採用）
- **メリット**: スキル1本に集約され、`slide-expression` と完全同型でシンプル。
- **デメリット**: 言語観点（python）と領域観点が同階層の references に混在し、軸が交差して見通しが悪い。
- **不採用理由**: 「言語 × 領域 × 境界」の異なる軸を1階層に潰すと、適用条件（`.py` のとき/境界ファイルのとき）の表現が曖昧になる。

#### 選択肢C: 領域ごとに独立スキル（不採用）
- **メリット**: 領域ごとの粒度が最も明確。
- **デメリット**: 領域数だけスキルが増え、骨格段階では中身がほぼ重複する。共通観点の二重管理。
- **不採用理由**: 各領域がスケルトンの現状では過剰。各領域が肉付けされてから移行を検討すれば足りる。

### 論点2: 指摘の記載と修正点の扱い

#### 選択肢A: コメント記載＋修正は新規PRで作成（採用）
- **メリット**: 「指摘して終わり」ではなく**修正点があれば PR まで作成**する。修正は別ブランチ→新規PRなので、未レビューの変更を元PRに直接積まない（fresh-context・人の最終確認を保てる）。
- **デメリット**: PR が増える（元PR＋修正PR）。

#### 選択肢B: 元PRブランチに直接修正コミット（不採用）
- **メリット**: PR が増えない。
- **デメリット**: エージェントの修正が未レビューのまま元PRに積まれ、マージへ進みうる。レビュアー（生成元）と修正者が同一になり fresh-context が崩れる。
- **不採用理由**: 「人/別エージェントの最終確認」を挟めるよう、修正は独立PRに分ける。

#### 選択肢C: コメント記載のみ（不採用）
- **メリット**: 最もシンプルで安全。
- **デメリット**: 「修正点があれば PR まで作成」という今回の要件を満たさない。
- **不採用理由**: 要件（修正点があれば PR 作成）に合わない。

### 論点3: マージの実行ゲート

#### 選択肢A: 検証付き自動マージ（採用）
- **メリット**: `uv run pytest` ∧ `uv run lint-imports` pass ∧ `[must]`=0 を満たすときだけマージ。安全性と自動化のバランスが良い。
- **デメリット**: GitHub Actions の CI が未設置のため、検証はローカル実行に依存する。

#### 選択肢B: 確認後マージ（不採用）
- **メリット**: 最も安全（人が毎回ゲート）。
- **デメリット**: 毎回手が止まり、自動運用にならない。
- **不採用理由**: 「問題なければマージ」を自動で回す狙いに対し過剰に保守的。検証ゲートで実用上の安全は確保できる。

#### 選択肢C: 即自動マージ（[must]=0 のみ）（不採用）
- **メリット**: 要件に最も忠実でシンプル。
- **デメリット**: テスト/境界の機械検査を挟まずマージしうる。
- **不採用理由**: マージは取り消しにくい。検証を1枚挟むコストは小さく、リスク低減効果が大きい。

## 結果・トレードオフ

- **配置**: エージェント `.claude/agents/pr-reviewer.md`、スキル `.claude/skills/code-review-{general,python,architecture}/`（general は `references/domain-checklist.md` を持つ）。運用ルールの単一の真実は [`guides/development-policy/code-review-rules.md`](../../guides/development-policy/code-review-rules.md)。
- **severity 語彙の単一の真実**は [`.github/pull_request_template.md`](../../.github/pull_request_template.md)。スキル・エージェントはこれと一致させ、独自に増やさない。
- **検証ゲートはローカル実行**（`uv run ...`）。GitHub Actions の CI を導入したら、ゲートを CI 結果へ置き換える（その判断は必要時に別途）。
- **注意点**: ネイティブ自動認識は、エージェント・スキルが `main` にマージされ各環境で読み込まれて初めて有効（ADR-0003 と同じ）。サブエージェント仕様の変更に追従が必要。
- **拡張**: 領域が肉付けされ早見表で足りなくなったら、論点1を選択肢C（領域別スキル）へ見直す余地を残す。必要になれば `.claude-plugin` でプラグイン化も可能。

## 関連ドキュメント・リンク

- [guides/development-policy/code-review-rules.md](../../guides/development-policy/code-review-rules.md) — レビュー運用ルール（単一の真実）
- [.claude/agents/pr-reviewer.md](../../.claude/agents/pr-reviewer.md) — レビュー統括エージェント
- [.claude/skills/code-review-general/SKILL.md](../../.claude/skills/code-review-general/SKILL.md) ほか `code-review-*` スキル
- [.github/pull_request_template.md](../../.github/pull_request_template.md) — 指摘の接頭辞（severity 語彙）
- [ADR-0002](./0002-modular-monolith-bounded-context.md) — 領域境界（architecture 観点の根拠） / [ADR-0003](./0003-presentation-system.md) — ネイティブ `.claude/` 配置方針
- 出典: Anthropic「Best practices for Claude Code」/ Google Engineering Practices（Code Review）（#11 調査）
