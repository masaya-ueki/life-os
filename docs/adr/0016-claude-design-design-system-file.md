# ADR-0016: Claude Design のデザインシステムを単一ファイルで持ち docs/design/ に置く

- **ステータス**: `承認済み`
- **決定日**: 2026-09-08
- **決定者**: masaya_ueki
- **関連 ADR**: [ADR-0013](./0013-deprecate-presentation-adopt-claude-design.md)（本 ADR はその積み残しに対応する）

---

## コンテキスト

[ADR-0013](./0013-deprecate-presentation-adopt-claude-design.md) で `domains/presentation` と `scripts/deckgen` を廃止し、プレゼン作成を Claude Design へ移行した。その際「Claude Design 専用の skill / template の整備は本 ADR の範囲外」として保留していた。

現状、スライドの指示書を作る `slide-spec-writer` スキルは claude.ai 側の**個人スキル**として存在し、Claude Design に渡す YAML を生成する（プログラムで pptx を作らない構成にはなっている）。しかし次の 2 点が未解決だった。

1. **デザイン定義がスライド指示書の中に埋まっている** — 同じ Notion ライクな見た目をドキュメントや UI モックに使いたくても、スライド用 YAML から切り出せない。案件ごとに YAML が増えるたびにデザイン値が複製される。
2. **リポジトリ側にデザインの正本が無い** — 個人スキルは claude.ai 側で同期されるためリポジトリで版管理できず、「なぜこの配色・この余白なのか」がレビューにも履歴にも残らない。

また Claude Design 側では、組織のデザインシステムを**発行（Published）**しておけば以降の成果物に自動適用される。適用先はスライドに限らない。

## 決定事項

**Claude Design に読み込ませるデザイン資産を content 領域 `docs/design/` に置き、デザインシステムを `DESIGN.md` 形式（9 セクション）の単一ファイル [design-system-notion-like.md](../design/design-system-notion-like.md) として管理する。** 「どう見えるか（デザインシステム）」と「何を話すか（案件ごとの指示書）」を 2 層に分離し、Anthropic 公式のデザイン系プラグインは導入しない。

## 検討した選択肢

### 選択肢A: `docs/design/` に `DESIGN.md` 形式の単一ファイルとして置く（採用）

- **メリット**: デザインの正本がリポジトリに 1 ファイルで存在し、変更が PR とコミット履歴に残る。スライド／ドキュメント／UI モックのどれにも同じ 1 枚で適用できる。`DESIGN.md`（Visual Theme / Color / Typography / Components / Layout / Elevation / Do's & Don'ts / Responsive / Agent Prompt Guide の 9 セクション）は Claude Design 界隈で事実上の共通形式になっており、Claude 側が解釈しやすい。案件ごとの指示書はデザイン値を持たず構成と内容だけを持てばよくなる。
- **デメリット**: リポジトリを直しても Claude Design 側には自動反映されない（アップロードし直す運用が要る）。ファイルの粒度が大きく、部分更新でも全体を読む必要がある。

### 選択肢B: Anthropic 公式マーケットプレイスの `design` プラグインを導入する（不採用）

- **メリット**: 公式配布で保守が不要。design-system / design-handoff / design-critique などのスキルが揃っている。
- **デメリット**: 中身は Figma を前提とした UX ワークフロー支援（クリティーク・ハンドオフ・アクセシビリティ監査）で、**スライドの指示フォーマットもデザインシステム定義フォーマットも持たない**。Figma / Notion / Slack など多数の MCP サーバーが同梱され、必要のない接続面が増える。
- **不採用理由**: 探していた「スライド用の指示フォーマット」を提供しないため、導入しても本 ADR の課題（デザイン定義の切り出し）は解決しない。接続面だけが増える。

### 選択肢C: 現状維持（スライド指示書 YAML にデザイン定義を埋めたままにする）（不採用）

- **メリット**: 追加ファイルが不要。指示書 1 枚を渡せば完結する。
- **デメリット**: デザイン値が案件ごとの YAML に複製され、更新すると全案件がズレる。スライド以外の成果物に再利用できない。個人スキル側にあるためリポジトリでレビューも版管理もできない。
- **不採用理由**: [R-DOC-1（単一の真実）](../../rule/documentation.md)に反する。デザインの一貫性を保つという目的そのものを損なう。

### 選択肢D: デザインシステムを Claude Design 側だけで持つ（リポジトリに置かない）（不採用）

- **メリット**: 二重管理が起きない。Claude Design の UI 上で完結する。
- **デメリット**: 変更履歴・変更理由が残らず、差分レビューもできない。設定が失われたときに復元できない。
- **不採用理由**: 「なぜこの制約なのか」を残せない。リポジトリを正本、Claude Design を配布先とするほうが life-os の運用（ADR + PR レビュー）と整合する。

## 結果・トレードオフ

- **新設**: content 領域 `docs/design/`（コードを持たない。uv workspace member でも Bounded Context でもないため `pyproject.toml` / `.importlinter` の更新は不要）。
- **2 層構成**: デザインシステム（`docs/design/`・不変に近い）／ 案件ごとの指示書（`slide-spec-writer` が生成・使い捨て）。指示書はデザイン値を再定義せず参照する。
- **同期は手動**: リポジトリのファイルを更新したら Claude Design 側のデザインシステムを差し替える必要がある。自動同期は行わない（`DesignSync` 相当の仕組みはコンポーネントライブラリ向けで、Markdown 1 枚の運用には過剰）。
- **プラグインは入れない**: 公式・非公式を問わずデザイン系プラグインは導入しない。将来 Anthropic がスライドの指示フォーマットを公式提供したら本 ADR を見直す。
- **見直し条件**: (1) Claude Design がデザインシステムの公式ファイル形式を定義したとき、(2) デザイン資産がコンポーネント単位の管理を要する規模になったとき。

## 関連ドキュメント・リンク

- [docs/design/README.md](../design/README.md) — デザイン資産の索引と使い方
- [docs/design/design-system-notion-like.md](../design/design-system-notion-like.md) — デザインシステム本体
- [ADR-0013](./0013-deprecate-presentation-adopt-claude-design.md) — presentation 領域を廃止し Claude Design へ移行する
- [rule/documentation.md](../../rule/documentation.md) — 単一の真実（R-DOC-1）・Diátaxis（R-DOC-3）
