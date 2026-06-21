# ADR-0002: 複数領域を Modular Monolith × Bounded Context で共存させる

- **ステータス**: `承認済み`
- **決定日**: 2026-06-15
- **決定者**: masaya_ueki
- **関連タスク**: #1
- **置き換え**: -

---

## コンテキスト

life-os は task / travel / media / content-sales という**互いにほぼ無関係な複数領域**を 1 リポジトリに集約する「個人用のなんでも環境」を目指す（[README](../../README.md)）。

ここで本質的な課題は「巨大な単一ドメインをどうモデリングするか」ではなく、**性質の異なる複数システムを 1 つのリポジトリで破綻なく共存させること**である。素朴に進めると次の失敗に陥りやすい。

- 領域をまたいで共通モデルを作ろうとする（task の「タグ」と media の「タグ」、travel の「場所」と media の「撮影地」は同じ言葉でも意味が違う）。共通化した瞬間に各領域の都合が衝突し、変更が連鎖する。
- 技術レイヤー（model / view / controller）で横断的にディレクトリを切ると、領域の境界が溶けて密結合になる。
- 「規約として直接 import しない」と決めても、規約は必ず破られる。

加えて life-os 固有の前提として次が確定している。

- 領域の性質は**混在**する（task / content-sales は「動くコード」が主役、media / travel は「データ（メタ情報）」が主役）。
- 実装言語は **Python 中心**で統一する（既存 `scripts/` も Python）。
- 単独開発の個人プロジェクトであり、運用負荷は低く保ちたい。

## 決定事項

**DDD の戦略的設計（Bounded Context / Context Map）を骨子に、実装は Modular Monolith、リポジトリは領域＝トップレベルの Monorepo（Python / uv workspace）で構成する。** 領域の性質に応じて 2 つのアーキタイプ（動く領域＝軽量ヘキサゴナル / データ領域＝薄い構成）を使い分け、**領域間連携は各領域の `public.py`（契約）経由のみに限定し、その境界を import-linter で機械的に強制する。**

## 検討した選択肢

### 選択肢A: Modular Monolith × Bounded Context（採用）

各領域を独立した Bounded Context として 1 リポジトリ内のトップレベルモジュールに分け、内部のモデル・用語（ユビキタス言語）を意図的にバラバラに保つ。横断は最小限の Shared Kernel（`shared/`）と各領域の `public.py` 経由のみ。境界は import-linter で CI 検査する。

- **メリット**:
  - 領域ごとに最適なモデル・構造を選べ、変更が他領域に波及しない。
  - 1 リポジトリ・1 言語で運用負荷が低い（個人開発に適正）。
  - 境界が「願望」ではなく「検査対象」になり、時間が経っても崩れない。
  - 領域の性質差（動く/データ）をアーキタイプで吸収できる。
- **デメリット**:
  - 初期にボイラープレート（`public.py`・パッケージ分割・lint 設定）が要る。
  - 領域間連携時に ACL / `public.py` を介す一手間がかかる。

### 選択肢B: 単一統一ドメインモデル（不採用）

全領域を 1 つのドメインモデル・1 つの共通スキーマに統合する。

- **メリット**: 共通概念を 1 箇所で管理でき、初期は記述量が少ない。
- **デメリット**: 無関係な領域の都合が 1 モデルに同居し、変更が全体に連鎖する。「タグ」「場所」のような同名異義の概念が衝突する。
- **不採用理由**: 「全く異なる複数システム」という前提に真っ向から反し、典型的な密結合の泥団子に至る。

### 選択肢C: 領域ごとに別リポジトリ（Polyrepo）（不採用）

task / travel / media / content-sales をそれぞれ独立リポジトリにする。

- **メリット**: 境界が物理的に最強。領域ごとに独立リリース可能。
- **デメリット**: 「ひとつのリポジトリに集約する」という life-os の目的に反する。横断的な検索・運用・ADR・Issue 管理が分散し、個人利用には過剰。
- **不採用理由**: life-os の目的（集約）と運用負荷の観点で割に合わない。

### 選択肢D: 技術レイヤーで横断的に分割（不採用）

`models/` `services/` `views/` などの技術レイヤーをトップレベルに置き、その下に各領域を入れる。

- **メリット**: レイヤードアーキテクチャの一般的な見た目。
- **デメリット**: 領域の境界がレイヤーをまたいで分散し、1 領域の変更が複数ディレクトリに散る。境界が溶ける。
- **不採用理由**: Bounded Context の独立性を保てず、本 ADR の目的を達成できない。

## 結果・トレードオフ

### 全体構成

```
life-os/
├── pyproject.toml          # uv workspace ルート（各領域をメンバー化）
├── .importlinter           # 境界の強制（CI で検査）
├── shared/                 # Shared Kernel（意図的に貧弱に保つ）
│   └── src/shared/         #   ID 型・Result 型・日付など領域非依存の基盤のみ
├── task/                   # アーキタイプA（動く領域）
├── content-sales/          # アーキタイプA
├── media/                  # アーキタイプB（データ領域）
├── travel/                 # アーキタイプB
└── docs/adr/               # 設計決定記録
```

縦切り（領域）が一段目、技術レイヤーは各領域の内側だけに閉じる。

> **更新（[ADR-0009](./0009-group-domains-under-domains-dir.md)）**: 領域が増えてトップ階層の統制がしづらくなったため、領域（BC）は `domains/` コンテナ配下にまとめる構成へ変更した（`shared` は Shared Kernel として例外的にルート直下のまま）。Modular Monolith × Bounded Context の決定・境界強制の仕組み（`public.py` / `.importlinter`）は本 ADR のまま不変で、変わるのは物理配置と `members` パスのみ。上図の `task/` 等は現行では `domains/task/` を読み替える。

### 2 つのアーキタイプ

| | アーキタイプA（動く領域） | アーキタイプB（データ領域） |
|---|---|---|
| 対象 | task / content-sales | media / travel |
| 主役 | ロジック・ユースケース | データ（メタ情報） |
| 内部構成 | 軽量ヘキサゴナル（`domain` / `application` / `adapters`） | 薄い構成（`models` / `index`） |
| DDD 戦術的設計 | 適用する（Entity / 値オブジェクト / 集約） | 原則使わない（スキーマ中心） |

### 領域間連携の 3 原則（Modular Monolith の生命線）

1. **直接 import 禁止**: 他領域の内部（`*.domain` / `*.application` / `*.adapters` / `*.models` / `*.index`）を直接 import しない。
2. **`public.py` が唯一の契約境界**: 領域間の参照は各領域の `public.py` 経由のみ。内部構造を変えても外に波及しない。Context Map の「橋」を物理的にここへ集約する。
3. **`shared/` に領域概念を入れない**: ID 型・日付・Result 型まで。「タスク」「場所」のようなドメイン語が入った時点で失敗の兆候。

### 境界の機械的強制（Python ならではの決め手）

[import-linter](https://import-linter.readthedocs.io/) のコントラクトで上記原則を CI 検査する（`.importlinter`）。

- 各領域は他領域の**内部パッケージ**を import できない（`public.py` のみ許可）。
- `shared` はいかなる領域にも依存できない。
- 違反 import はビルドを失敗させる。

新たに領域内のサブパッケージ（例: `task/services/`）を増やす場合は内部パッケージとして扱われ既存コントラクトでカバーされるが、**領域直下に `public.py` 以外の新規トップレベルモジュールを足す場合は `.importlinter` の `forbidden_modules` に追記する**こと。

### Context Map のパターン適用

領域間で参照が発生したら、その関係がどのパターンかを当該領域の `README.md` と必要に応じて ADR に 1 行残す。

- **Shared Kernel**: `shared/`（最小限）。
- **Customer-Supplier / Conformist**: 参照される側の `public.py` 契約に合わせる。
- **Anti-Corruption Layer (ACL)**: 他領域の概念を自領域モデルへ翻訳する層（アーキタイプA は `adapters/acl/` に配置）。

### トレードオフ・注意点

- **ボイラープレートのコスト**: 領域追加ごとに `pyproject.toml` / `public.py` / README が要る。これは境界を守る対価として受け入れる。
- **領域追加時の手順**: 新領域を足す際は (1) トップレベルディレクトリ作成、(2) uv workspace `members` 追加、(3) `.importlinter` のコントラクト更新、(4) `system: *` ラベルを `scripts/setup-github-labels.sh` と運用ルールへ追加（[README](../../README.md) の方針）。
- **アーキタイプの境界は厳密でない**: データ領域が育って複雑なロジックを持ち始めたら、アーキタイプB → A へ昇格してよい（その判断は別 ADR に残す）。

## 関連ドキュメント・リンク

- [README](../../README.md) — life-os の目的・領域・`system: *` ラベル方針
- [ADR-0001](./0001-claude-code-native-multi-session.md) — Claude Code ネイティブ運用への移行
- [開発運用ルール](../../guides/development-policy/issue-operation-rules.md)
- import-linter: https://import-linter.readthedocs.io/
- uv workspaces: https://docs.astral.sh/uv/concepts/projects/workspaces/
- DDD 戦略的設計（Bounded Context / Context Map）: Eric Evans, *Domain-Driven Design*
