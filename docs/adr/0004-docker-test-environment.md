# ADR-0004: テスト実行環境を Docker（Compose）で提供する

- **ステータス**: `承認済み`
- **決定日**: 2026-06-17
- **決定者**: masaya_ueki
- **関連タスク**: -
- **置き換え**: -

---

## コンテキスト

life-os のテストは 2 種類ある。各 Bounded Context のスモークテスト（`pytest`）と、領域境界の機械的検査（`import-linter` / [`.importlinter`](../../.importlinter)）である。現状はいずれもローカルに [uv](https://docs.astral.sh/uv/) を導入し `uv run pytest` / `uv run lint-imports` で実行する前提になっている（[ADR-0002](./0002-modular-monolith-bounded-context.md) の uv workspace 構成）。

この方式は実行者ごとに uv と Python 3.12 の導入が必要で、環境差が生まれやすい。「Docker さえあれば誰でも同一条件でテスト・境界検査を回せる」状態にしたい。ここで決めるべき構造的な論点は次の 3 つで、いずれも一度決めると後から変えにくく、複数の有力な選択肢があるため ADR の対象（[ADR README の判断基準](./README.md#adr-の必要性判断基準)）に該当する。

1. **Docker 関連ファイルの配置**: ルート直下に平置きするか、専用ディレクトリに集約するか。
2. **イメージの作り方**: uv workspace をどう同期し、ローカル反復実行とビルド再現性をどう両立するか。
3. **Docker の位置づけ**: テスト環境は Bounded Context（uv workspace member）なのか、コードを持たないツール領域なのか。

## 決定事項

**ローカル実行用に、テスト実行用イメージ（[`docker/Dockerfile`](../../docker/Dockerfile)）とルートの [`compose.yaml`](../../compose.yaml) を用意する。** `compose.yaml` は同一イメージを共有する `test`（`pytest`）と `lint`（`lint-imports`）の 2 サービスを定義し、`docker compose run --rm test` / `lint` で実行する。**Docker はテスト/開発ツールであり Bounded Context ではない**ため、uv workspace member にも `.importlinter` にも追加しない（`docs/`・`scripts/` と同類のツール領域）。再現性のため **`uv.lock` を生成・コミット**し、イメージは `uv sync --frozen` で同期する。既存の `uv run` 実行も従来どおり使える（Docker は上乗せ・非破壊）。

## 検討した選択肢

### Docker 関連ファイルの配置

#### 選択肢A: `Dockerfile` は `docker/`、`compose.yaml` はルート（採用）
- **メリット**: `compose.yaml` はルートに置くのが慣習で、ビルドコンテキスト（= リポジトリルート）を自然に指せ、どのディレクトリからでも `docker compose` を実行しやすい。一方で `Dockerfile` を `docker/` に隔離することでルートの肥大化を抑え、将来 prod 用や複数イメージが増えても `docker/` 配下に集約できる。
- **デメリット**: ファイルが 2 箇所に分かれる（compose はルート、Dockerfile は `docker/`）。

#### 選択肢B: すべてルート直下に平置き（不採用）
- **メリット**: 最小構成で分かりやすい。
- **デメリット**: イメージが増えると `Dockerfile.test` `Dockerfile.prod` … とルートが散らかる。
- **不採用理由**: 拡張時の見通しを優先し、Dockerfile は専用ディレクトリに寄せる。

#### 選択肢C: compose も含め `docker/` に全部入れる（不採用）
- **メリット**: Docker 関連が 1 箇所に集約される。
- **デメリット**: `docker/compose.yaml` だと毎回 `-f docker/compose.yaml` 指定が要り、ビルドコンテキストも `..` 参照になって分かりにくい。
- **不採用理由**: compose をルートに置く慣習の利点（自動検出・素直なコンテキスト）を捨てるほどの利得がない。

### イメージの作り方

#### 選択肢A: uv 公式イメージ + 2 段同期 + ソースマウント（採用）
- **メリット**: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` は Python 3.12 と uv が同梱で構築が単純。先にマニフェスト＋`uv.lock` だけ入れて `uv sync --no-install-workspace` で dev 依存（pytest / import-linter）レイヤをキャッシュし、その後ソースを同期するためビルドが速い。ビルド時は `uv sync --frozen` でコミット済み `uv.lock` どおりに固定し、各領域は **editable** で導入される。実行時は `uv run --no-sync` で再同期を抑止するため、（a）実行時にネットワークが不要で、（b）compose でソースをマウントすると editable リンク越しにコード変更が再ビルド無しで即反映される（venv はマウント対象外の `/opt/venv`）。依存を変えたときだけイメージを `build` し直す。
- **デメリット**: マニフェストを列挙する `COPY` が領域数だけ並ぶ（領域追加時にメンテが要る）。

#### 選択肢B: 素の `python:3.12-slim` に uv を都度インストール（不採用）
- **メリット**: ベースイメージが汎用的。
- **デメリット**: uv の導入手順を自前で持つ必要があり、公式イメージより冗長。
- **不採用理由**: 公式イメージで足りる。

#### 選択肢C: ロック無し（`uv sync` を毎回解決）（不採用）
- **メリット**: `uv.lock` を管理しなくてよい。
- **デメリット**: ビルドごとに依存解決結果が変わりうる。[`.gitignore`](../../.gitignore) も「`uv.lock` は再現性のためコミットする」と明記している。
- **不採用理由**: 再現性を優先し `uv.lock` をコミットする。

### Docker の位置づけ

テスト実行環境は Python のプロダクトコードを持たない**ツール領域**であり、Bounded Context ではない。よって uv workspace の `members`・`.importlinter` のコントラクト・`public.py` の管理対象にしない（[ADR-0002](./0002-modular-monolith-bounded-context.md) の「コードを持たない領域」と同じ扱い）。これは [ADR-0003](./0003-presentation-system.md) が `presentation/` を BC 非該当としたのと同じ判断軸。

## 結果・トレードオフ

- **追加物**: [`docker/Dockerfile`](../../docker/Dockerfile)、ルート [`compose.yaml`](../../compose.yaml)、[`.dockerignore`](../../.dockerignore)、コミットした `uv.lock`。
- **実行**: `docker compose run --rm test`（pytest）/ `docker compose run --rm lint`（lint-imports）。実行時は `uv run --no-sync` でネットワーク不要・即時。従来の `uv run pytest` / `uv run lint-imports`（ローカル uv）も併用可能。
- **非破壊**: 既存の uv ベースのワークフローは変更しない。Docker は実行手段の追加。
- **メンテ**: 領域（Bounded Context）を追加したら、`Dockerfile` のマニフェスト `COPY` 行を 1 行追加する（[ADR-0002](./0002-modular-monolith-bounded-context.md) の領域追加手順に Docker も含める）。
- **CI への発展余地**: 同じイメージ・同じコマンドを CI でも使えるため、将来 GitHub Actions などへ展開しやすい（本 ADR のスコープ外）。

## 関連ドキュメント・リンク

- [README.md](../../README.md) — 開発セットアップ（Docker 実行手順）・ディレクトリ構成
- [ADR-0002](./0002-modular-monolith-bounded-context.md) — uv workspace / Bounded Context（テスト対象の構成と「コードを持たない領域」の扱い）
- [ADR-0003](./0003-presentation-system.md) — `presentation/` を BC 非該当のツール領域とした判断（同じ判断軸）
- [uv ドキュメント](https://docs.astral.sh/uv/) — workspace / `uv sync --frozen`
