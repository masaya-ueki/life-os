# 領域別レビュー早見表（domain-checklist）

[`code-review-general`](../SKILL.md) の補助。変更が属する**領域（Bounded Context / content領域）に応じた重点観点**を引く早見表。
領域の構成方針は [ADR-0002](../../../../docs/adr/0002-modular-monolith-bounded-context.md)、境界の機械的観点は [`code-review-architecture`](../../code-review-architecture/SKILL.md) を参照。

> 各領域はまだ**スケルトン段階**。観点は「肉付けが進んだときに崩してはいけない原則」を中心に置く。骨格の追加・空ファイル整備の段階では `[must]` を乱発しない。

---

## 領域 → アーキタイプ対応

| 領域（ディレクトリ / scope） | 種別 | アーキタイプ | レイヤ |
|------|------|------------|--------|
| `task` | Bounded Context | A（動く領域） | `domain` / `application` / `adapters` |
| `content-sales` | Bounded Context | A（動く領域） | `domain` / `application` / `adapters` |
| `media` | Bounded Context | B（データ領域） | `models` / `index` + `data/` |
| `travel` | Bounded Context | B（データ領域） | `models` / `index` + `data/` |
| `shared` | Shared Kernel | —（基盤） | 領域非依存の最小限 |
| `presentation` / `docs` / `guides` | content領域 | —（コード無し） | Markdown / HTML / 設定 |

---

## アーキタイプA（動く領域）: `task` / `content-sales`

軽量ヘキサゴナル。**依存の向き**が崩れていないかが核心。

- [ ] **依存方向**: `adapters → application → domain` の一方向か。`domain` が `application`/`adapters` や外部ライブラリ・I/O・フレームワークに依存していないか（`[must]`: 逆流・domain の汚染）
- [ ] **domain の純粋性**: ビジネスルール/エンティティ/値オブジェクトに DB・HTTP・ファイル・時刻取得などの副作用が混入していないか
- [ ] **application の責務**: ユースケース調整は `application` にあるか（`adapters` にロジックが漏れていないか）
- [ ] **adapters の責務**: 入出力（CLI・ストレージ・外部API）の変換に徹しているか
- [ ] **領域間連携**: 他領域を使うときは相手の `public.py` 経由か（内部 import は `[must]`、詳細は architecture スキル）
- [ ] **テスト**: domain はピュアに単体テストできる形か

---

## アーキタイプB（データ領域）: `media` / `travel`

薄い構成。**データ構造の安定性**と**薄さの維持**が核心。

- [ ] **薄さの維持**: `models`/`index` に過剰なロジック（動く領域並みのユースケース）を持ち込んでいないか。必要になったらアーキタイプAへの移行を ADR で検討する話であって、こっそり厚くしない（`[imo]`〜`[ask]`）
- [ ] **models**: データ表現（スキーマ/型）が明確か。後方互換を壊す変更は影響を明示しているか
- [ ] **index**: 検索・参照の責務に収まっているか
- [ ] **`data/`**: 実データとコード/スキーマの分離。大きなバイナリ・生成物・秘匿データを不用意にコミットしていないか（`[must]`: シークレット・巨大バイナリ）
- [ ] **領域間連携**: 他領域からの参照は `public.py` 経由か

---

## Shared Kernel: `shared`

- [ ] **領域非依存**: `shared` が `task`/`content_sales`/`media`/`travel` のいずれにも依存していないか（`[must]`: 依存は禁止。`.importlinter` の `shared-is-foundation` 契約）
- [ ] **最小限**: 「本当に領域横断で必要な基盤か」。特定領域の都合を持ち込んでいないか
- [ ] **安定性**: 多くの領域が依存する前提。破壊的変更は影響範囲を広く見る

---

## content領域: `presentation` / `docs` / `guides`

コードを持たない（uv workspace member でも Bounded Context でもない）。観点はコード規約ではなく**整合性**。

- [ ] **リンク整合**: 相互リンク・相対パスが切れていないか（移動/リネームに追従しているか）
- [ ] **ADR 整合**: 設計判断に対応する ADR があるか、設計側に ADR へのリンクがあるか（[docs/adr/README.md](../../../../docs/adr/README.md) のルール）
- [ ] **テンプレ準拠**: Issue/PR/ADR のテンプレート・命名規則に沿っているか
- [ ] **日本語**: ドキュメント・スキル・エージェントの説明は日本語で統一されているか
- [ ] **スキル/エージェント記法**（`.claude/`）: frontmatter（`name`/`description`/`Triggers on`、必要に応じ `tools`/`model`）が既存（`slide-*`・`issue-memory`）と整合しているか
- [ ] **presentation 固有**: 生成 HTML が自己完結（外部URL/依存なし・16:9・印刷対応）か（[domains/presentation/README.md](../../../../domains/presentation/README.md)）

---

## 横断（領域をまたぐ変更）

- 複数領域・共通基盤に触れる変更は `system: common`。
- 新トップレベルモジュール/領域の追加、`.importlinter`・`pyproject.toml` の変更を含む場合は必ず [`code-review-architecture`](../../code-review-architecture/SKILL.md) を併せて適用する。
