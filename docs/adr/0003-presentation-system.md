# ADR-0003: プレゼン作成システムをネイティブ Claude Code 構成で導入する

- **ステータス**: `承認済み`
- **決定日**: 2026-06-16
- **決定者**: masaya_ueki
- **関連タスク**: #3
- **置き換え**: -

---

## コンテキスト

life-os に新テーマとして「プレゼンテーション作成」基盤を追加する。テーマを与えると、エージェントとスキルが連携して HTML スライドを自動生成し、まず実物を出してから生成物ベースで改善していくことを狙う。

ここで決めるべき構造的な論点は次の4つで、いずれも「一度決めると後から変えにくい」「複数の有力な選択肢があり自明でない」ため ADR の対象（[ADR README の判断基準](./README.md#adr-の必要性判断基準)）に該当する。

1. **エージェント／スキルの配置場所**: Claude Code がネイティブに自動認識するのは `.claude/agents/` と `.claude/skills/`。一方で既存の `create-issue` スキルは独自に `.github/skills/` に置かれており、配置規約が割れている。
2. **スライドの出力形式**: HTML で作る方針は確定。その実装をフレームワーク（reveal.js 等）に乗せるか、依存なしの単一ファイルにするか。
3. **生成パイプラインの分割**: 内容設計と描画を 1 エージェントで一気に作るか、段階分割するか。
4. **`presentation/` の位置づけ**: [ADR-0002](./0002-modular-monolith-bounded-context.md) の Bounded Context（uv workspace member）として扱うか、コードを持たない content 領域として扱うか。

前提として、Anthropic 公式の既存構成を調査した（#3）。`anthropics/skills` の `pptx` スキルは `SKILL.md` ＋参照 `.md` ＋ `scripts/` 構成。Claude Code のサブエージェントは `.claude/agents/*.md`（frontmatter `name`/`description` 必須、`tools`/`model` 任意）、スキルは `SKILL.md`（`name`/`description` 必須）で `.claude/skills/` が自動認識パス。

## 決定事項

**エージェントは `.claude/agents/`、スキルは `.claude/skills/`（ネイティブ配置）に置く。** スライドは**依存ライブラリなしの自己完結 HTML（16:9・`@media print`）**で生成する。生成は **`内容まとめ(outline.yml)` → `スライド化(index.html)` の2段パイプライン**（planner / renderer を `slide-deck-builder` が統括）とする。**`presentation/` は Python コードを持たない content 領域**として扱い、uv workspace / `.importlinter` / `public.py` の管理対象にしない。

## 検討した選択肢

### 配置場所

#### 選択肢A: ネイティブ `.claude/` 配置（採用）
- **メリット**: Claude Code がサブエージェント・スキルを自動認識・委譲できる（機能が実際に動く）。公式仕様・`anthropics/skills` の構成と一致。プラグイン化への移行も容易。
- **デメリット**: 既存 `create-issue`（`.github/skills/`）と配置が割れる不整合が残る。

#### 選択肢B: 既存に合わせ `.github/skills/` 配置（不採用）
- **メリット**: リポジトリ内の配置が `create-issue` と統一される。
- **デメリット**: `.github/skills/` は Claude Code のネイティブ自動認識パスではなく、サブエージェント（`.claude/agents/`）とは結局分離する。スキルとエージェントの配置が二重管理になる。
- **不採用理由**: 「エージェントとスキルが連携して動く」という本件の目的に対し、自動認識されない場所に置くのは本末転倒。

#### 選択肢C: プラグインとして同梱（将来余地として保留）
- **メリット**: `.claude-plugin/plugin.json` で agents/skills を1単位として配布・再利用できる。
- **デメリット**: 初期のボイラープレートが増え、まず実物を出して改善するという進め方と相性が悪い。
- **不採用理由**: 現段階では過剰。ネイティブ配置なら後からプラグインへ束ね直せるため、必要になった時点で移行する。

> **既存 `create-issue` 配置との不整合について**: 本 ADR では `create-issue` の `.github/skills/` 配置を変更しない（スコープ外）。新規のプレゼン関連のみネイティブ配置とし、配置規約の統一は別途検討する。

### 出力形式

#### 選択肢A: 自己完結の単一 HTML + CSS（採用）
- **メリット**: 依存ゼロで可搬性が高く、1ファイルで共有・バージョン管理できる。「生成物から改善」しやすい。`@media print` でPDF化可能。
- **デメリット**: アニメーション・スピーカーノート等の高機能は手作りになる。

#### 選択肢B: reveal.js 等フレームワーク（不採用）
- **メリット**: アニメ・ノート・PDF出力が組み込み。
- **デメリット**: Node/CDN 依存が増え、単一ファイル化が難しく、生成物の差分レビュー・改善がしづらい。
- **不採用理由**: 本件の主眼は「まず実物を出して改善」。可搬性と差分の見やすさを優先する。

### 生成パイプライン

#### 選択肢A: 2段（内容まとめ → スライド化）（採用）
- **メリット**: 内容設計（構成）と描画（表現）を分離でき、各段を独立に改善・再実行できる。`outline.yml` が中間成果物としてレビュー対象になる。
- **デメリット**: エージェント定義とスキーマ（YAML）の整備が必要。
- **採用理由**: ユーザー指定の構成（内容を `.yml` にまとめ→ yml をスライド化）と一致し、改善ループを回しやすい。

### `presentation/` の位置づけ

Python コードを持たないため **content 領域**とする（`docs/`・`guides/`・`scripts/` と同類）。Bounded Context ではないので `pyproject.toml` の members・`.importlinter` のコントラクト・`public.py` は追加不要。将来、生成ロジックを Python 実装する必要が出たら、その時点で領域昇格を別 ADR で判断する。

## 結果・トレードオフ

- **配置**: `.claude/agents/{slide-deck-builder,slide-content-planner,slide-html-renderer}.md`、`.claude/skills/{slide-structure,slide-expression}/`。`slide-expression` は親 SKILL.md ＋ `references/{comparison,chart,flow,structure,emphasis}.md`（progressive disclosure、`pptx` スキルに倣う）。
- **YAML スキーマの単一の真実**は [`presentation/README.md`](../../presentation/README.md)。planner と renderer はこれを契約として参照する。
- **不整合**: `create-issue`（`.github/skills/`）と新規スキル（`.claude/skills/`）の配置が割れる。配置規約の統一は今後の課題として残す。
- **注意点**: ネイティブ自動認識はエージェント定義・スキルが `main` にマージされ各環境で読み込まれて初めて有効。サブエージェント機能の仕様変更に追従が必要。
- **拡張**: 必要になれば `.claude-plugin/plugin.json` で agents/skills をプラグインへ束ね直せる（選択肢C への移行余地）。

## 関連ドキュメント・リンク

- [presentation/README.md](../../presentation/README.md) — システム概要・YAMLスキーマ・HTML規約
- [ADR-0002](./0002-modular-monolith-bounded-context.md) — Modular Monolith × Bounded Context（`presentation/` を BC 非該当とする根拠）
- [ADR-0001](./0001-claude-code-native-multi-session.md) — Claude Code ネイティブ機能への移行方針
- Anthropic Agent Skills（`anthropics/skills` の `pptx` 構成）/ Claude Code サブエージェント・スキル仕様（#3 調査）

## 追記（2026-06-17）

「結果・トレードオフ」で*今後の課題*として残した `create-issue` スキルの配置不整合を解消した。GitHub Copilot を使用しない方針に伴い、`.github/skills/create-issue/` を Claude Code ネイティブ認識パスの `.claude/skills/create-issue/` へ移設し、`.github/skills/` を廃止。これによりスキルの配置規約が `.claude/skills/`（slide-structure / slide-expression と同所）に統一された。本 ADR の決定（ネイティブ `.claude/` 配置）自体に変更はない。
