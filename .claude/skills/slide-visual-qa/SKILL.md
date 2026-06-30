---
name: slide-visual-qa
---

# slide-visual-qa スキル

生成した PPTX を PNG に変換し、モデルが画像を目視確認して `outline.yml` の修正提案を行うスキル。
「目隠し配置（コードだけで調整）」から「見ながら調整」への転換。視覚的品質の天井を上げる。

---

## 前提条件の確認

PNG 変換は Docker (pptx-convert) 経由で統一する。環境差異をなくすため**ローカル直接実行はしない**。

```bash
# pptx-convert イメージの確認
docker image inspect life-os-pptx-convert:local &>/dev/null && echo "OK" || echo "MISSING"
```

`MISSING` の場合は初回ビルドが必要（数分）:
```bash
docker compose build pptx-convert
```

---

## Step 1: PPTX → PNG 変換

```bash
# スクリプトが Docker に自動委譲する（ローカル直接実行不要）
bash scripts/deckgen/tools/pptx_to_png.sh <slug> [output_dir] [--dpi 150]
```

例:
```bash
bash scripts/deckgen/tools/pptx_to_png.sh ai-driven-handson
# → domains/presentation/decks/ai-driven-handson/preview/slide-01.png, slide-02.png, ...
```

---

## Step 2: 全スライドを Read ツールで読む

`preview/` ディレクトリの全 PNG を `Read` ツールで読む（スライド番号順）。  
Claude は multimodal モデルなので、ファイルを渡すだけで視覚的に確認できる。

```
Read: domains/presentation/decks/{slug}/preview/slide-01.png
Read: domains/presentation/decks/{slug}/preview/slide-02.png
...
```

---

## Step 3: 視覚品質チェックリスト

各スライドを読み終えたら、以下の観点で問題を抽出する。

### 3-A テキスト品質
| チェック項目 | 合格基準 |
|------------|---------|
| テキストオーバーフロー | テキストがボックス・スライド外にはみ出していない |
| 文字の視認性 | 背景色と文字色のコントラストが十分 |
| フォントサイズ | 同スライド内で極端にサイズが混在していない |
| テキスト余白 | ボックス内壁とテキストの間に最低でも 2–3mm 相当の隙間がある |

### 3-B 図解品質
| チェック項目 | 合格基準 |
|------------|---------|
| バッジ・ラベル重なり | flow 図のバッジ番号がラベルテキストと重なっていない |
| 矢印の配置 | 矢印がボックスとボックスの間に正しく収まっている |
| ピラミッド形状 | 最上段が三角形、下段に向かって幅が広がっている |
| ベン図の重なり | 2 つの楕円が適度に重なっており、ラベルが読める |
| 図形の意図と形 | 意図した形状（三角・台形・矩形）が正しく表示されている |

### 3-C レイアウト品質
| チェック項目 | 合格基準 |
|------------|---------|
| 余白バランス | 上下左右の余白がほぼ均等（左だけ詰まっているなどがない） |
| コンテンツ密度 | 大きな空白エリアがない / 逆に詰め込みすぎていない |
| 視覚的重心 | コンテンツが一方に偏っていない |
| スライド外はみ出し | 全要素がスライド境界内に収まっている |

### 3-D 全体統一性
| チェック項目 | 合格基準 |
|------------|---------|
| フォントサイズ統一 | デッキ全体でボディテキストのサイズが揃っている |
| 余白量の統一 | スライドをまたいで余白量が一定 |
| 色の一貫性 | テーマカラー以外の色が混入していない |

---

## Step 4: 問題の分類と修正方針

発見した問題を **A（outline.yml で修正可能）** / **B（deckgen コード修正が必要）** に分類する。

### A. outline.yml で修正できるもの → その場で修正

| 視覚的問題 | 修正方法 |
|-----------|---------|
| テキストがはみ出す | `content` 項目を 3〜5 個に減らす / 各項目を短縮 |
| スライドが情報過多 | スライドを 2 枚に分割（1スライド1メッセージ原則） |
| expression が内容に合わない | expression を変更（例: `flow` → `bullet`） |
| 水平フローのステップが 5 個以上 | `orientation: vertical` に変更 |
| ピラミッドの `layers` が多すぎ | 3〜4 層に絞る |
| 箇条書きが空 / 内容が薄い | `content` と `data` を充実させる |
| ベン図ラベルが長い | `sets` のラベルを短縮（12 文字以下推奨） |

### B. deckgen コードで修正が必要なもの → 課題として記録

以下は outline.yml を変えても解決しない構造的な問題。  
修正提案を箇条書きで記録し、エンジニアへフィードバックする。

| 視覚的問題 | 推定原因ファイル |
|-----------|---------------|
| ピラミッド最上段が三角形でない | `scripts/deckgen/src/deckgen/expressions/structure.py` |
| バッジとラベルが重なる | `layout.py` の BADGE_Y_OFFSET, FLOW_LABEL_FONT |
| 全スライドの余白が不均一 | `layout.py` の MARGIN, BODY_TOP 等の定数 |
| フォントサイズが統一されていない | 各 expression ファイルの SIZE 定数 |
| 矢印がボックスと重なる | `flow.py` の FLOW_ARROW_OFFSET_H 定数 |

---

## Step 5: outline.yml の修正とログ

修正を行う前に変更内容をログとして記録する:

```
[Visual QA Loop N] 修正内容:
- スライド3 「XXX」: content を 6 項目 → 4 項目に削減（テキストオーバーフロー解消）
- スライド7 「YYY」: orientation を horizontal → vertical に変更（5 ステップで幅不足）
- スライド12 「ZZZ」: expression を structure/pyramid → bullet に変更（層が読めない）
```

`Edit` ツールで該当箇所を直接修正する。  
変更が多い場合は `Write` で全体を書き直す（YAML 破損を防ぐため慎重に）。

---

## ループ終了条件

以下のいずれかで終了する:
1. **品質合格**: Step 3 の全チェック項目が合格
2. **上限到達**: 指定したループ回数（デフォルト 3 回）に達した
3. **変更なし**: 直前のループと同じ修正しか提案できない（収束判定）

終了時に以下を報告する:
- 実施したループ数と各ループの修正サマリー
- 残存する B 種問題のリスト（deckgen 改善タスク候補）
- 最終 PPTX のパス
