---
name: directory-keeper
description: life-os のディレクトリ構成を rule/ に照らして監査し、状態をきれいに保つ統括管理スキル。決定的チェック(scripts/check_structure.py)＋判断系の監査を行い、安全な機械的修正は1つのPRに、判断が要る指摘はレポートにまとめる。Use when ディレクトリの掃除・構成監査・日次の自動整頓をしたいとき、/directory-keeper 実行時、Routines（クラウド定期実行）時。Triggers on ディレクトリ監査, 構成チェック, 整理, directory keeper, 構成を整える, 散らかり.
---

# directory-keeper — ディレクトリ統括管理スキル

life-os のディレクトリを [`rule/`](../../../rule/README.md) で定めた構成論に照らして監査し、
**1日1回**実行して状態をきれいに保つ。対話起動（`/directory-keeper`）と Routines
（クラウド定期実行・常時起動PC不要）の両方で同じ手順を使う。Routines は本リポジトリを
フレッシュにクローンしてこのスキルを実行するため、ルール・チェッカー・スキルが repo に
入っていれば追加設定なしで動く。

> **設計根拠**: [ADR-0005 ディレクトリ統治と日次 directory-keeper](../../../docs/adr/0005-directory-governance-daily-keeper.md)
> **掃除の契約（チェックリストと対応方針の正本）**: [rule/maintenance.md](../../../rule/maintenance.md)

---

## 手順

### ステップ1: ルールを読み込む
[`rule/maintenance.md`](../../../rule/maintenance.md) の監査チェックリストを正本として読む。
各ルールの詳細が必要なら [`rule/`](../../../rule/README.md) の該当ファイルを参照する。

### ステップ2: 決定的チェックを実行
```bash
python scripts/check_structure.py --json
```
JSON の `findings` を取得する。各 finding は `check`（C-ROOT 等）・`severity`（error/warning）・
`path`・`message` を持つ。**ここでトークンを使わず機械的に拾える違反を確定させる**
（全ソースを読まずに済ませ、コストを抑える狙い）。

### ステップ3: 判断系の監査
`scripts/check_structure.py` では判定できない `judge` 項目（[rule/maintenance.md](../../../rule/maintenance.md) の表参照）を、
**rule/ ＋ 各 README ＋ ディレクトリ構造のみ**を読んで確認する。全ソースコードは読まない。

- C-ARCHETYPE: 領域内構成が archetype A/B に沿うか
- C-DOC-PLACE: ドキュメントが種類に応じた場所にあるか（Diátaxis）
- C-ADR-LINK: ADR と対応設計が相互リンクされているか
- C-STALE: 空雛形の放置・未使用物・「念のため」残置が無いか
- C-UTILS: `utils/`/`common/`/`misc/` 等の曖昧な入れ物が無いか

### ステップ4: 仕分け（fix / report）
検出を [rule/maintenance.md](../../../rule/maintenance.md) の「対応方針」に従って仕分ける。

- **fix**: 機械的・安全・可逆な修正のみ（雛形 README の追加、kebab-case への改名と参照更新、
  明確なリンク切れの修正）。
- **report**: 設計判断・破壊的変更・意味解釈を伴うもの（ファイル削除/移動、archetype 逸脱、
  ドキュメント重複の解消方針）。**自動で変更しない**。
- 迷ったら **report 側に倒す**。directory-keeper は掃除であって設計変更ではない。

### ステップ5: 出力（自律度 = レポート＋PR）

- **違反ゼロ** → 何もせず終了。PR も Issue も作らない（無駄な通知・コストを出さない）。
- **fix がある** → feature ブランチを切って修正を適用し、**1回の実行＝1つの PR** を作る。
  - ブランチ名・コミットは [guides/development-policy/issue-operation-rules.md](../../../guides/development-policy/issue-operation-rules.md) に従う（例: `chore/issue-N-directory-keeper`、`chore(common): ...`）。
  - PR 本文に「適用した fix の一覧（根拠ルールID付き）」＋「report 項目（人の判断が必要な指摘）」を記載する。
  - PR には `system: common` と `type: chore` のラベルを付ける。
- **fix は無いが report だけある** → 修正用 PR は作らず、指摘を**PR 本文相当のレポートとして提示**する
  （対話時は会話に出力、無人時は Issue 化してよい）。

---

## レポート様式

```markdown
## directory-keeper 監査結果（YYYY-MM-DD）

### 自動修正（この PR に含む）
- [C-MEMBER-README] shared/README.md を雛形作成
- [C-LINK] foo.md:12 のリンク切れを修正

### 要判断（人のレビューが必要・未変更）
- [C-STALE] task/data/.gitkeep のまま空。要否を判断
- [C-DOC-PLACE] guides/x.md は reference 的内容。docs/ へ移すか検討

### 指摘なしの項目
- C-ROOT / C-TOPDIR / C-DOC-DUP: クリーン
```

違反ゼロのときは「指摘なし（クリーン）。対応不要。」とだけ述べて終了する。

---

## 原則

- **読む範囲を最小化**: rule/ ＋ README ＋ 構造に限定し、全ソースは読まない（速度・コスト）。
- **安全側に倒す**: 破壊的・解釈を伴う変更はしない。fix は機械的で可逆なものだけ。
- **冪等**: 既に直っているものを再修正しない。クリーンなら無出力で終わる。
