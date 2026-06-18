# presentation — プレゼン作成システム

テーマを与えると、Claude Code のサブエージェントとスキルが連携して**自己完結 HTML スライド**を生成する基盤。

> **設計根拠**: [ADR-0003 プレゼン作成システムをネイティブ Claude Code 構成で導入する](../docs/adr/0003-presentation-system.md)

この `presentation/` は Python コードを持たない **content 領域**（`docs/`・`guides/` と同類）。uv workspace member でも Bounded Context でもなく、`public.py` / `.importlinter` の管理対象外。

---

## 構成要素

| 要素 | 場所 | 役割 |
|------|------|------|
| スキル `slide-structure` | `.claude/skills/slide-structure/` | スライド全体構成（起承転結・課題/目的・1スライド1メッセージ） |
| スキル `slide-expression` | `.claude/skills/slide-expression/` | 表現方法の索引＋`references/`（比較/グラフ/フロー/構造/強調） |
| エージェント `slide-content-planner` | `.claude/agents/` | テーマ → `outline.yml`（内容まとめ） |
| エージェント `slide-html-renderer` | `.claude/agents/` | `outline.yml` → `index.html`（スライド化） |
| エージェント `slide-deck-builder` | `.claude/agents/` | 上記2つを統括するオーケストレーター |
| エージェント `slide-pptx-builder` | `.claude/agents/` | `outline.yml` → 編集可能 `.pptx`（pptx 出力） |
| スキル `slide-pptx` | `.claude/skills/slide-pptx/` | expression → ネイティブ pptx マッピングの索引 |
| ツール `deckgen` | `scripts/deckgen/` | `outline.yml` → `.pptx` を生成する python-pptx 製ツール（[ADR-0007](../docs/adr/0007-pptx-output.md)） |
| 生成物 | `presentation/decks/{slug}/` | `outline.yml` ＋ `index.html` ＋ `{slug}.pptx` |
| 配色トークン | `presentation/templates/theme-tokens.yml` | 配色の単一ソース（HTML/pptx 共有） |
| CSS 方針 | `presentation/templates/base.css.md` | 16:9・レイアウト・印刷の実装指針 |

## パイプライン

`outline.yml` を単一の真実として、HTML と pptx の2系統に出力できる。

```
テーマ
  └─ slide-deck-builder（統括）
       ├─① slide-content-planner → presentation/decks/{slug}/outline.yml
       ├─②a slide-html-renderer   → presentation/decks/{slug}/index.html   （閲覧・PDF用）
       └─②b slide-pptx-builder    → presentation/decks/{slug}/{slug}.pptx  （編集可能 PowerPoint）
```

## 使い方

`slide-deck-builder` エージェントにテーマを渡す（例:「スライドを作って: ○○について」）。または段階実行で `slide-content-planner` → `slide-html-renderer` / `slide-pptx-builder` を個別に呼ぶ。

生成後:
- **HTML 閲覧**: `presentation/decks/{slug}/index.html` をブラウザで開く。
- **HTML→PDF化**: ブラウザの印刷 → 用紙 landscape・余白なし・背景画像ON で PDF 保存（`@media print` 対応済み）。
- **PowerPoint**: `uv run --project scripts/deckgen -m deckgen {slug}` で `{slug}.pptx` を生成。文字・表・図形は**ネイティブ＝編集可能**。詳細は [scripts/deckgen/README.md](../scripts/deckgen/README.md)。

---

## YAML スキーマ（outline.yml）— 単一の真実

`slide-content-planner` が生成し `slide-html-renderer` が読む契約。ユーザー指定の **章・タイトル・概要・内容・表現** を表す。

```yaml
deck:
  title: "プレゼンのメインタイトル"      # 表紙の主張
  subtitle: "サブタイトル"               # 任意
  theme: default                         # 配色プリセット名（default / dark / ...）
  date: "2026-06-16"                     # 任意

chapters:                                # 章（ストーリーのブロック）
  - chapter: "課題提起"                  # 章名
    slides:
      - title: "スライド見出し"          # タイトル
        summary: "このスライドの主張（1メッセージ）"  # 概要＝結論
        content:                          # 内容（根拠・詳細。3〜5項目）
          - "要点1"
          - "要点2"
        expression: comparison            # 表現（下表の語彙）
        data:                             # 表現固有データ（expression により構造が変わる）
          mode: two-column
          left:  { label: "Before", items: ["..."] }
          right: { label: "After",  items: ["..."] }
```

### expression の語彙

| 値 | 用途 | data の参照 |
|----|------|------------|
| `title` | 表紙・章扉 | 不要 |
| `bullet` | 箇条書き（背景/アジェンダ/まとめ） | 不要（content を使う） |
| `comparison` | 比較・対比・Before/After | `.claude/skills/slide-expression/references/comparison.md` |
| `chart` | グラフ・数値 | `references/chart.md` |
| `flow` | フロー・手順・タイムライン | `references/flow.md` |
| `structure` | 階層・2x2・ピラミッド・ベン図 | `references/structure.md` |
| `emphasis` | 大きな数値・キーメッセージ・引用 | `references/emphasis.md` |

各 `expression` の `data` の詳細フィールドは対応する reference ファイルに定義する。

---

## サンプル

- [`decks/claude-code-security/`](./decks/claude-code-security/) — 「ClaudeCodeのセキュリティ懸念とその対策について」（`outline.yml` + `index.html`）
