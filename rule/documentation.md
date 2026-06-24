# ドキュメント・README ルール

> **親**: [rule/README.md](./README.md)

ドキュメントが時間とともに食い違う最大の原因は「同じことを複数箇所に書く」こと。
これを構造で防ぐ。

---

## R-DOC-1: 単一の真実（Single Source of Truth）— 複製せず**リンク**せよ

**ある事実の正本は 1 ファイルだけ。他のファイルからは複製せずリンクで参照する。**
（ユーザー要望の「基本的に README.md に重複した記載は禁止」はこのルール。）

- ❌ ブランチ命名規約を README と guides の両方に本文で書く
- ✅ 正本は [guides/development-policy/issue-operation-rules.md](../guides/development-policy/issue-operation-rules.md)。README からはリンクのみ
- 判定: 同じ段落・コードブロックが 2 つ以上の Markdown に**逐語で**現れたら違反（`scripts/check_structure.py` が検出）

「どこが正本か」の目安：

| 種類の事実 | 正本 |
|---|---|
| なぜその設計か | [`docs/adr/`](../docs/adr/) の該当 ADR |
| 構造・配置はどうあるべきか | [`rule/`](./README.md) |
| 人の作業手順・運用ルール | [`guides/`](../guides/) |
| ある領域の内部仕様 | その領域の `README.md` / コード |
| リポジトリ全体の地図 | ルート [`README.md`](../README.md) |

---

## R-DOC-2: README の責務を階層で分ける

| README | 役割 | 書くこと | 書かないこと |
|---|---|---|---|
| **ルート `README.md`** | ハブ・索引 | 目的、領域一覧、構成図、主要ドキュメントへの**リンク** | 各領域の内部仕様の詳細 |
| **各領域/content の `README.md`** | その単位の所有 | 一行の目的、構成要素、実行/閲覧コマンド | リポジトリ全体方針の再掲（リンクで足りる） |

子 README にルート README の内容を再掲しない。逆も同じ。

---

## R-DOC-3: 種類で置き場所を分ける（Diátaxis）

ドキュメントは目的が違えば物理的に分ける。混在させない。

| 種類 | 目的 | 置き場所 |
|---|---|---|
| how-to（手順） | 作業を遂行する | [`guides/`](../guides/) |
| explanation（なぜ） | 背景・意思決定を理解する | [`docs/adr/`](../docs/adr/) |
| reference（仕様） | 事実を引く | 各領域 README / `domains/presentation/README.md` 等 |
| structure rule（規約） | あるべき構造を定める | [`rule/`](./README.md) |

---

## R-DOC-4: ADR と設計のリンクを必須にする

ADR に対応する設計・ルールがあるなら、設計側から ADR へ必ずリンクを張る。
手順とステータス運用の正本は [docs/adr/README.md](../docs/adr/README.md)（ここでは重複させない）。

---

## R-DOC-5: リンク切れを残さない

ドキュメント間の相対リンク・ADR リンクは生かしておく。ファイル移動・改名時は参照元も更新する
（directory-keeper が日次で相対リンクの健全性を確認する）。

> 関連: 構造は [directory-structure.md](./directory-structure.md)、命名は [naming.md](./naming.md)。
