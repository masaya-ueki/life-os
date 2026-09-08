# design — Claude Design 用のデザイン資産

life-os のプレゼン・ドキュメント・UI モックは **[Claude Design](https://claude.ai/design) で作る**（プログラムで pptx / HTML を生成しない）。
このディレクトリは、その Claude Design に読み込ませる**入力ファイル**を置く場所。コードは持たない content 領域。

> **採用理由**: [ADR-0016](../adr/0016-claude-design-design-system-file.md)（前提となる移行判断は [ADR-0013](../adr/0013-deprecate-presentation-adopt-claude-design.md)）

---

## ファイル一覧

| パス | 役割 | 変わる頻度 |
|---|---|---|
| [design-system-notion-like.md](./design-system-notion-like.md) | **デザインシステム**（Notion ライク）。色・タイポ・余白・コンポーネント・禁止事項の唯一の基準 | ほぼ変わらない |
| `decks/<案件名>.yml` | **指示書**。案件ごとの構成・ページテンプレート・内容 | 案件ごとに増える |

---

## 2 層の分担

成果物の見た目がブレないよう、**「デザイン」と「中身」を別ファイルに分ける**。

| 層 | 何を決めるか | 正本 |
|---|---|---|
| **デザインシステム** | どう見えるか（色・文字・余白・部品） | [design-system-notion-like.md](./design-system-notion-like.md) |
| **指示書** | 何を何ページで話すか（構成・テンプレート・内容） | `decks/<案件名>.yml`（`slide-spec-writer` スキルが生成） |

内容が差し替わってもデザインは崩れず、デザインを更新しても構成は作り直さずに済む。

---

## 使い方

### A. 組織のデザインシステムとして常設する（推奨）

1. [claude.ai/design](https://claude.ai/design) を開き、組織を選ぶ
2. デザインシステム設定で [design-system-notion-like.md](./design-system-notion-like.md) をアップロードする
3. **Published をオンにする**

以降、その組織で作るデザインには自動でこの design system が適用される。

### B. 単発で適用する

Claude Design のチャットに [design-system-notion-like.md](./design-system-notion-like.md) を添付し、
「このデザインシステムに従って作って」と伝える。指示テンプレートはファイル内の
「9. Agent Prompt Guide」にある。

### スライドを作る場合

1. `slide-spec-writer` スキル（[claude.ai](https://claude.ai) 側の個人スキル）で指示書 YAML を作る
   — `[[スライド指示書]]` または「スライドの指示書を作りたい」で起動する
2. **`decks/<案件名>.yml` としてこのリポジトリにコミットする**
   — スキルの出力先（`/mnt/user-data/outputs/`）はセッション終了で消えるため、残すなら手で移す
3. Claude Design に **デザインシステム ＋ 指示書 YAML** の 2 つを渡す
4. Claude Design 上で仕上げ、PDF / PPTX / URL で書き出す

指示書 YAML はデザイン値を再定義せず、デザインシステムを参照する形で書く（二重管理を避ける）。

### `decks/` の決まり

- **1 案件 1 ファイル**。ファイル名は kebab-case（例: `data-analysis-platform.yml`）
- 置くのは**指示書（入力）だけ**。書き出した PDF / PPTX は Claude Design 側に置き、コミットしない（[R-STRUCT-4](../../rule/directory-structure.md)）
- 社外秘・個人情報を含む素材はそのまま貼らない。伏せる箇所は `※既存資料を記載` のようなプレースホルダにする

---

## 更新するとき

- デザインシステムを変えたら、**A の手順で Claude Design 側も差し替える**（リポジトリだけ直しても反映されない）
- 図表 3 色ルール・スペーシングスケールなど**制約そのものを変える**場合は ADR を追加する（[docs/adr/README.md](../adr/README.md)）
