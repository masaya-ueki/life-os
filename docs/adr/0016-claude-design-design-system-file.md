# ADR-0016: Claude Design への入力（デザインシステム／指示書）を docs/design/ に集約する

- **ステータス**: `承認済み`
- **決定日**: 2026-09-08
- **決定者**: masaya_ueki
- **関連 ADR**: [ADR-0013](./0013-deprecate-presentation-adopt-claude-design.md)（本 ADR はその積み残しに対応する）
  - 指示書の形式は [ADR-0017](./0017-slide-spec-claim-materials-deck-types.md) で改訂

---

## コンテキスト

[ADR-0013](./0013-deprecate-presentation-adopt-claude-design.md) で `domains/presentation` と `scripts/deckgen` を廃止し、プレゼン作成を Claude Design へ移行した。その際「Claude Design 専用の skill / template の整備は本 ADR の範囲外」として保留していた。

現状、スライドの指示書を作る `slide-spec-writer` スキルは claude.ai 側の**個人スキル**として存在し、Claude Design に渡す YAML を生成する（プログラムで pptx を作らない構成にはなっている）。しかし次の 2 点が未解決だった。

1. **デザイン定義がスライド指示書の中に埋まっている** — 同じ Notion ライクな見た目をドキュメントや UI モックに使いたくても、スライド用 YAML から切り出せない。案件ごとに YAML が増えるたびにデザイン値が複製される。
2. **リポジトリ側にデザインの正本が無い** — 個人スキルは claude.ai 側で同期されるためリポジトリで版管理できず、「なぜこの配色・この余白なのか」がレビューにも履歴にも残らない。
3. **案件ごとの指示書に置き場所が無い** — ADR-0013 の廃止後も `domains/presentation/decks/` に Claude Design 用の指示書が置かれていた（`f2922c1`）。コードを持たないものが `domains/` 直下にあるため `scripts/check_structure.py` の C-DOMAIN が警告し続けていた。一方でスキルの出力先 `/mnt/user-data/outputs/` はセッション終了で消えるため、放っておくと指示書はどこにも残らない。

また Claude Design 側では、組織のデザインシステムを**発行（Published）**しておけば以降の成果物に自動適用される。適用先はスライドに限らない。

## 決定事項

**Claude Design への入力を content 領域 `docs/design/` に集約する。** デザインシステムは `DESIGN.md` 形式（9 セクション）の単一ファイル [design-system-notion-like.md](../design/design-system-notion-like.md)、案件ごとの指示書と素材は `docs/design/decks/<案件名>/`（`spec.yml` ＋ `materials/`）として管理し、「どう見えるか」と「何を話すか」を 2 層に分離する。Anthropic 公式のデザイン系プラグインは導入しない。

## 検討した選択肢

### 選択肢A: `docs/design/` に集約し、デザインシステムは `DESIGN.md` 形式の単一ファイルにする（採用）

- **メリット**: デザインの正本がリポジトリに 1 ファイルで存在し、変更が PR とコミット履歴に残る。スライド／ドキュメント／UI モックのどれにも同じ 1 枚で適用できる。`DESIGN.md`（Visual Theme / Color / Typography / Components / Layout / Elevation / Do's & Don'ts / Responsive / Agent Prompt Guide の 9 セクション）は Claude Design 界隈で事実上の共通形式になっており、Claude 側が解釈しやすい。案件ごとの指示書はデザイン値を持たず構成と内容だけを持てばよくなる。
- **デメリット**: リポジトリを直しても Claude Design 側には自動反映されない（アップロードし直す運用が要る）。デザインシステムはファイルの粒度が大きく、部分更新でも全体を読む必要がある。

### 選択肢B: Anthropic 公式マーケットプレイスの `design` プラグインを導入する（不採用）

- **メリット**: 公式配布で保守が不要。design-system / design-handoff / design-critique などのスキルが揃っている。
- **デメリット**: 中身は Figma を前提とした UX ワークフロー支援（クリティーク・ハンドオフ・アクセシビリティ監査）で、**スライドの指示フォーマットもデザインシステム定義フォーマットも持たない**。Figma / Notion / Slack など多数の MCP サーバーが同梱され、必要のない接続面が増える。
- **不採用理由**: 探していた「スライド用の指示フォーマット」を提供しないため、導入しても本 ADR の課題（デザイン定義の切り出し）は解決しない。接続面だけが増える。

### 選択肢C: 現状維持（スライド指示書 YAML にデザイン定義を埋めたままにする）（不採用）

- **メリット**: 追加ファイルが不要。指示書 1 枚を渡せば完結する。
- **デメリット**: デザイン値が案件ごとの YAML に複製され、更新すると全案件がズレる。スライド以外の成果物に再利用できない。個人スキル側にあるためリポジトリでレビューも版管理もできない。
- **不採用理由**: [R-DOC-1（単一の真実）](../../rule/documentation.md)に反する。デザインの一貫性を保つという目的そのものを損なう。

### 選択肢D: デザインシステムも指示書も Claude Design 側だけで持つ（リポジトリに置かない）（不採用）

- **メリット**: 二重管理が起きない。Claude Design の UI 上で完結する。
- **デメリット**: 変更履歴・変更理由が残らず、差分レビューもできない。設定が失われたときに復元できない。指示書が残らないため「昨年の資料を今年版に作り直す」ときに元の構成をゼロから起こすことになる。
- **不採用理由**: 「なぜこの制約なのか」を残せない。リポジトリを正本、Claude Design を配布先とするほうが life-os の運用（ADR + PR レビュー）と整合する。

### 選択肢E: 指示書をトップレベル `decks/` に独立した content 領域として切り出す（不採用）

- **メリット**: デッキ成果物の所在が一目で分かる。将来デッキが増えて画像等を持つ場合に拡張しやすい。
- **デメリット**: トップレベルが 1 つ増える。デザインシステムと指示書という**同じ用途（Claude Design への入力）**が 2 か所に分かれる。
- **不採用理由**: 現状のデッキ数では [R-STRUCT-6（深さは浅く一定に）](../../rule/directory-structure.md)より凝集を優先したほうがよい。デッキが増えて書き出し物や素材を伴うようになったら見直す。

## 結果・トレードオフ

- **新設**: content 領域 `docs/design/`（コードを持たない。uv workspace member でも Bounded Context でもないため `pyproject.toml` / `.importlinter` の更新は不要）。
- **2 層構成**: デザインシステム（`docs/design/`・不変に近い）／ 案件ごとの指示書と素材（`docs/design/decks/<案件名>/`・案件ごとに増える）。指示書は `design_system.source` でデザインシステムを参照し、値を複製しない。
- **1 案件 1 ディレクトリ**: 画像・xlsx などユーザー入力の素材を伴うため、ファイル数を固定しない。`spec.yml` と `materials/` を同じディレクトリに置く。
- **移動**: `domains/presentation/decks/data-analysis-platform/outline.yml` を `docs/design/decks/data-analysis-platform/spec.yml` へ移し、空になった `domains/presentation/` を削除した。これで C-DOMAIN 警告が解消する。中身は旧 `deckgen` 形式（`expression` / `data`）のままで、次に使うときに `slide-spec-writer` 形式へ書き換える。
- **書き出し物は置かない**: PDF / PPTX / HTML は Claude Design 側に残し、リポジトリにはコミットしない（[R-STRUCT-4](../../rule/directory-structure.md)）。
- **スキルをリポジトリ管理へ移した**: 指示書が自動でリポジトリに残るよう、claude.ai 側の個人スキルだった `slide-spec-writer` を [`.claude/skills/slide-spec-writer/`](../../.claude/skills/slide-spec-writer/SKILL.md) に取り込み、出力先を `docs/design/decks/<案件名>/spec.yml` に固定した。あわせてテンプレートの `design_system` ブロック（色・タイポの値を丸ごと持っていた）を `source` 参照に置き換え、コンテキスト 1 の複製問題を解消した。
- **残る制約**: life-os の外（claude.ai のチャット等）でスキルを使う場合はリポジトリに書き込めないため、従来どおり `/mnt/user-data/outputs/` に出力して手で移す運用になる。claude.ai 側の同名の個人スキルは重複するので削除するか無効化する。
- **同期は手動**: リポジトリのファイルを更新したら Claude Design 側のデザインシステムを差し替える必要がある。自動同期は行わない（`DesignSync` 相当の仕組みはコンポーネントライブラリ向けで、Markdown 1 枚の運用には過剰）。
- **プラグインは入れない**: 公式・非公式を問わずデザイン系プラグインは導入しない。将来 Anthropic がスライドの指示フォーマットを公式提供したら本 ADR を見直す。
- **見直し条件**: (1) Claude Design がデザインシステムの公式ファイル形式を定義したとき、(2) デザイン資産がコンポーネント単位の管理を要する規模になったとき、(3) デッキが増えて書き出し物や素材を伴い、選択肢E（トップレベル `decks/`）が見合うようになったとき。

## 関連ドキュメント・リンク

- [docs/design/README.md](../design/README.md) — デザイン資産の索引と使い方
- [docs/design/design-system-notion-like.md](../design/design-system-notion-like.md) — デザインシステム本体
- [ADR-0013](./0013-deprecate-presentation-adopt-claude-design.md) — presentation 領域を廃止し Claude Design へ移行する
- [rule/documentation.md](../../rule/documentation.md) — 単一の真実（R-DOC-1）・Diátaxis（R-DOC-3）
