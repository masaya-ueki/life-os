# スライド共通 CSS 方針（base.css.md）

`slide-html-renderer` が `index.html` にインラインする CSS の実装指針。**ファイルを読み込ませるのではなく、この方針に沿って `<style>` を生成する**（自己完結を保つため）。

## 設計値
- 基準サイズ: **1280 × 720px（16:9）**。`.slide { aspect-ratio: 16/9 }`。
- 1スライド = 1 `<section class="slide">`。縦スクロールで並べ、印刷時に1枚=1ページ。
- 本文 ≥ 24px、見出し(h2) ≥ 40px、表紙(h1) ≥ 64px、ビッグナンバー 96〜160px。
- フォントは OS 標準のみ（`system-ui, -apple-system, "Hiragana Sans", "Yu Gothic", sans-serif`）。Webフォント禁止。

## 配色トークン（CSS 変数で `deck.theme` を切替）

配色の**単一ソースは [`theme-tokens.yml`](./theme-tokens.yml)**（HTML/pptx 共有）。ここに色値は持たない。
`slide-html-renderer` は `theme-tokens.yml` を読み、各テーマを CSS 変数ブロックへ展開する:

- `themes.default` → `:root { --bg: …; --fg: …; … }`（`#rrggbb` をそのまま CSS 値に使う）
- それ以外の各テーマ → `[data-theme="<name>"] { … }`（例: `dark`）
- トークン名はそのまま CSS 変数名にする（`accent` → `--accent`、`on_accent` → `--on-accent`）

トークンの意味（`accent`=強調/After、`muted`=補足/Before、`good`/`bad`=良/悪、`card`=カード背景、
`line`=罫線、`on_accent`=アクセント面上の文字色 など）は `theme-tokens.yml` のコメントを参照。
新テーマの追加は `theme-tokens.yml` に 1 ブロック足すだけでよい（HTML/pptx 両方に反映される）。

## 必須レイアウト

```css
* { box-sizing: border-box; margin: 0; }
body { background:#33373f; color:var(--fg);
       font-family: system-ui,-apple-system,"Hiragana Sans","Yu Gothic",sans-serif; }
.slide {
  position: relative; width: 1280px; max-width: 100%; aspect-ratio: 16/9;
  margin: 24px auto; padding: 56px 72px; background: var(--bg);
  box-shadow: 0 4px 24px rgba(0,0,0,.3); overflow: hidden;
}
.slide h2 { font-size: 44px; color: var(--accent); border-bottom: 3px solid var(--line); padding-bottom: 12px; }
.slide .lead { font-size: 28px; font-weight: 700; margin: 20px 0; }
.slide ul { font-size: 26px; line-height: 1.8; padding-left: 1.2em; }
.slide--title { display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; }
.slide--title h1 { font-size: 64px; }
.slide--emphasis { background: var(--accent); color: var(--on-accent); display:flex; flex-direction:column;
  justify-content:center; align-items:center; text-align:center; }
.big-number { font-size: 140px; font-weight: 800; line-height: 1; }
```

## 印刷（PDF化）対応

```css
@media print {
  body { background:#fff; }
  .controls, .pager { display: none !important; }
  .slide { margin:0; box-shadow:none; page-break-after: always; width:100%; }
  @page { size: 1280px 720px; margin: 0; }
}
```

## 任意の操作 JS（最小・インライン）

キーボード ←/→ で前後スライドへスクロールする程度に留める。フレームワーク不要。

```html
<script>
  const slides=[...document.querySelectorAll('.slide')];let i=0;
  addEventListener('keydown',e=>{
    if(e.key==='ArrowRight')i=Math.min(i+1,slides.length-1);
    if(e.key==='ArrowLeft')i=Math.max(i-1,0);
    slides[i]?.scrollIntoView({behavior:'smooth'});
  });
</script>
```

## 禁止事項
- 外部 CSS/JS/フォント/画像 URL の参照（`<link href="http...">`, CDN, Google Fonts 等）。
- reveal.js などフレームワーク依存。
- 1スライドへの情報詰め込み（1スライド1メッセージを守る）。
