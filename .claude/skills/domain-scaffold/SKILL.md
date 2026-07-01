---
name: domain-scaffold
description: life-os に新しい Bounded Context（領域 / domain）を追加するときの横断更新をチェックリスト化した統括スキル。domains/<領域>/ の雛形作成（アーキタイプA/B）と、ルート pyproject.toml・.importlinter・docker/Dockerfile・README/rule/CLAUDE.md のツリー・system ラベル（運用ルール表 + setup-github-labels.sh）という N×N の付随更新を漏れなく行い、check_structure / lint-imports / pytest で検証する。設計根拠は ADR-0002 / ADR-0009。Use when: 新しい領域を追加したい、ドメインを新設したい、bounded context を足したい、/domain-scaffold 実行時。Triggers on: 領域追加, ドメイン追加, 新領域, 領域新設, bounded context 追加, domain scaffold, スキャフォールド.
---

# domain-scaffold — 新領域スキャフォールドスキル

life-os に新しい **Bounded Context（領域）** を追加するときの手順書。領域追加は
`domains/<領域>/` を作るだけでは完了せず、**ルート `pyproject.toml` / `.importlinter` /
`docker/Dockerfile` / ドキュメントのツリー / `system:` ラベル** を横断更新する必要がある
（更新箇所は領域数に比例して増える N×N の作業で、抜けやすい）。このスキルはその全手順を
チェックリスト化し、各段階に検証コマンドを埋め込む。

設計根拠: [ADR-0002](../../../docs/adr/0002-modular-monolith-bounded-context.md)（Modular Monolith / Bounded Context）、
[ADR-0009](../../../docs/adr/0009-group-domains-under-domains-dir.md)（領域は `domains/` 配下）。

---

## トリガー条件

- ユーザーが `/domain-scaffold` を実行した場合
- 「新しい領域を追加したい」「ドメインを新設したい」「bounded context を足したい」と依頼された場合
- ProductBacklog / Task Issue で新領域の追加（スキャフォールド）に着手する場合

---

## 前提: 2つのアーキタイプ

| アーキタイプ | 対象例 | src 構成 | いつ選ぶか |
|---|---|---|---|
| **A（動く領域）** | `task`, `content-sales` | `domain/ application/ adapters/` + `public.py` | 振る舞い（ユースケース・状態遷移）を持つ |
| **B（データ領域）** | `english`, `media`, `travel`, `presentation` | `models.py index.py` + `public.py` + `data/` | データ（一覧・検索）が主役で振る舞いが薄い |

迷ったら B から始め、振る舞いが増えたら A へ昇格（昇格は別 ADR に記録）。
命名: **ディレクトリは kebab-case**（`content-sales`）、**src パッケージは snake_case**（`content_sales`）。
根拠: `rule/naming.md`（R-NAME-1）。

---

## 手順

以下、追加する領域を `<領域>`（kebab-case ディレクトリ名）、`<pkg>`（snake_case パッケージ名）とする。
最小の実例テンプレートは [`domains/english`](../../../domains/english/)（アーキタイプB）と
[`domains/task`](../../../domains/task/)（アーキタイプA）。

### ステップ1: `domains/<領域>/` を作成

共通:
```
domains/<領域>/
├── pyproject.toml
├── README.md            # ADR-0002 リンク / ユビキタス言語 / 内部構成 / 境界メモ
├── data/.gitkeep        # データ領域は主役データ、動く領域は空でよい
├── src/<pkg>/
│   ├── __init__.py      # 「他領域からは <pkg>.public のみ参照」docstring
│   └── public.py        # ★他領域に公開する唯一の契約
└── tests/test_<pkg>.py  # スモークテスト
```
アーキタイプB は `src/<pkg>/models.py` `index.py` を追加。
アーキタイプA は `src/<pkg>/{domain,application,adapters}/__init__.py` を追加。

`pyproject.toml`（`domains/english/pyproject.toml` を基に `name` と `packages` のみ変更）:
```toml
[project]
name = "<領域>"
version = "0.0.0"
description = "…（Bounded Context / アーキタイプA|B）"
requires-python = ">=3.12"
dependencies = ["shared"]

[tool.uv.sources]
shared = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<pkg>"]
```

### ステップ2: ルート `pyproject.toml` を3箇所更新

[`/pyproject.toml`](../../../pyproject.toml):
1. `[project] dependencies` に `"<領域>"` を追加
2. `[tool.uv.workspace] members` に `"domains/<領域>"` を追加
3. `[tool.uv.sources]` に `<領域> = { workspace = true }` を追加

### ステップ3: `.importlinter` を更新（最重要・漏れやすい）

[`/.importlinter`](../../../.importlinter):
1. `[importlinter] root_packages` に `<pkg>` を追加
2. `shared-is-foundation` コントラクトの `forbidden_modules` に `<pkg>` を追加
3. **新コントラクトを追加**（他領域Aは `domain/application/adapters`、他領域Bは `models/index` を列挙して禁止）:
   ```ini
   [importlinter:contract:<pkg>-uses-only-public]
   name = <領域> は他領域を public 経由でのみ参照する
   type = forbidden
   source_modules =
       <pkg>
   forbidden_modules =
       task.domain
       task.application
       task.adapters
       content_sales.domain
       content_sales.application
       content_sales.adapters
       media.models
       media.index
       travel.models
       travel.index
       english.models
       english.index
       presentation.models
       presentation.index
       tools.csv_splitter
   ```
4. **既存の全領域コントラクトの `forbidden_modules` に、新領域 `<pkg>` の内部モジュールを追記**
   （アーキタイプA なら `<pkg>.domain` `<pkg>.application` `<pkg>.adapters`、B なら `<pkg>.models` `<pkg>.index`）。
   これが N×N の肝。既存領域数だけ追記箇所がある。

> 領域直下に `public.py` 以外の新規トップレベルモジュールを足したら、同様に各コントラクトへ追記する。

### ステップ4: `docker/Dockerfile`

[`/docker/Dockerfile`](../../../docker/Dockerfile) の依存キャッシュ層（既存 `COPY domains/*/pyproject.toml` の並び）に1行追加:
```dockerfile
COPY domains/<領域>/pyproject.toml domains/<領域>/
```
`compose.yaml` は領域を列挙しないため変更不要。

### ステップ5: ドキュメントのツリーを更新

- [`/README.md`](../../../README.md) の「ディレクトリ構成」ツリーに `domains/<領域>/` を追記（必要なら目的の領域リストにも）
- [`/rule/directory-structure.md`](../../../rule/directory-structure.md) のツリー
- [`/CLAUDE.md`](../../../CLAUDE.md) の領域リスト（アーキタイプ分類・`domains/` 配下の記載）

### ステップ6: `system:` ラベルを追加

- [`/guides/development-policy/issue-operation-rules.md`](../../../guides/development-policy/issue-operation-rules.md) の scope / `system:` ラベル表に `<領域>` を追加
- [`/scripts/setup-github-labels.sh`](../../../scripts/setup-github-labels.sh) に `system: <領域>` を追加
- GitHub 側にラベルが無ければ作成: `gh label create "system: <領域>" --repo masaya-ueki/life-os --color 7e57c2 --description "…"`

---

## ステップ7: 検証（必ず全て通す）

```bash
python scripts/check_structure.py        # 構造（C-DOMAIN: domains/ 直下は member のみ）
docker compose run --rm lint             # 境界（.importlinter / lint-imports）
docker compose run --rm test             # pytest スモーク
```

依存（members / pyproject）を変えたら `docker compose build` でイメージ再ビルドしてから lint / test。

---

## 完了チェックリスト（レビュー観点）

- [ ] `domains/<領域>/` を作成（pyproject / README / data / src/<pkg>/public.py / tests）
- [ ] ルート `pyproject.toml` 3箇所（dependencies / members / sources）
- [ ] `.importlinter`: root_packages / shared-is-foundation / 新コントラクト / **既存全領域の forbidden 追記**
- [ ] `docker/Dockerfile` の COPY
- [ ] README / rule/directory-structure.md / CLAUDE.md のツリー
- [ ] `system: <領域>` ラベル（運用ルール表 + setup-github-labels.sh + GitHub 側）
- [ ] `check_structure.py` / `lint-imports` / `pytest` が通る

> このチェックリストは `code-review-architecture` スキルの観点と対応する。境界・構造を伴う
> PR はそちらでレビューすると機械的に検証できる。

---

## 注意事項

- **`public.py` 以外を他領域から import しない**。契約は `public.py` に集約し `__all__` で明示公開する。
- **`shared/` に領域固有の語を持ち込まない**（Shared Kernel は領域非依存）。
- 一般的な慣習から外れる構造判断（例: 新しい実装言語・デプロイ形態の導入）をしたら **ADR を残す**
  （手順は [`docs/adr/README.md`](../../../docs/adr/README.md)）。
- ラベル・ブランチ・コミットの運用は [`guides/development-policy/issue-operation-rules.md`](../../../guides/development-policy/issue-operation-rules.md) に従う。
