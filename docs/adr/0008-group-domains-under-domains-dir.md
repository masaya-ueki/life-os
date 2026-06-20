# ADR-0008: 領域（Bounded Context）を `domains/` コンテナ配下にまとめる

- **ステータス**: `承認済み`
- **決定日**: 2026-06-20
- **決定者**: agardentree
- **関連タスク**: （なし）

---

## コンテキスト

[ADR-0002](./0002-modular-monolith-bounded-context.md) では各領域（Bounded Context）をトップレベルディレクトリ＝uv workspace member として並べてきた。領域は `task` / `content-sales` / `media` / `travel` / `english` と増え、これに `shared`（Shared Kernel）・content領域（`presentation` / `docs` / `guides`）・支援ディレクトリ（`rule` / `scripts` / `docker` / `.claude` / `.github`）・ルートファイル群が同じトップ階層に混在する。

結果として **「どれが業務領域なのか」がトップ階層を見ても一目で分からず、領域が増えるほど統制（C-TOPDIR の許可リスト管理・レビュー時の見通し）が効きづらく**なってきた。領域だけをひとまとめにし、トップ階層の認知負荷を下げたい。

## 決定事項

領域（Bounded Context）を **`domains/` コンテナディレクトリ配下**に集約する（`domains/task/`, `domains/content-sales/`, `domains/media/`, `domains/travel/`, `domains/english/`）。`shared` は領域非依存の Shared Kernel であり「領域」ではないため、例外として**ルート直下に残す**。当面 `domains/` 配下はフラット（カテゴリ分けは将来必要になれば追加）。

## 検討した選択肢

### 選択肢A: `domains/` 配下にまとめる（採用）

- **メリット**: トップ階層が「コンテナ＋種別」で整理され領域の増加に強い。`domains/` を見れば業務領域が一覧できる。Python パッケージ名（snake_case）は `src/<pkg>/` にあるため不変で、import 文・`.importlinter` の `root_packages`・contract は無改修。変更は `members` パス・Dockerfile の `COPY` パス・構成チェッカー・ドキュメントに限定。
- **デメリット**: 領域が一段深くなり相対パス（各領域 README → `docs/` 等）の深さ調整が必要。Screaming Architecture（トップが「何をやるか」を叫ぶ）がトップ直下では一段弱まる（`domains/` の一段下で回復）。

### 選択肢B: 英語以外の名前（`領域/`）を使う（不採用）

- **メリット**: リポジトリの語彙「領域」と完全一致。
- **不採用理由**: ディレクトリ名は kebab-case 英語（[R-NAME-1](../../rule/naming.md)）に揃える方針。非 ASCII 名はツール・パスの扱いで不確実性が残る。

### 選択肢C: `contexts/` / `bounded-contexts/` を使う（不採用）

- **メリット**: DDD 用語に忠実。
- **不採用理由**: repo の一次語彙は「領域」。最も素直な対訳 `domains` が README/CLAUDE.md の語彙と噛み合う。`bounded-contexts` は冗長。

### 選択肢D: `shared` も `domains/` に入れる（不採用）

- **不採用理由**: `shared` は「領域非依存の Shared Kernel」と定義され（ADR-0002）、領域ではない。領域コンテナに混ぜると定義が濁る。ルート直下に残すことで「領域 vs カーネル」の区別を構造で表す。

## 結果・トレードオフ

- **不変**: `.importlinter`（パッケージ名ベース）、`pyproject.toml` の `[tool.uv.sources]` / `[project] dependencies`（パッケージ名キー）、各領域内の `src/` 構造・archetype・import 文。
- **変更**: `pyproject.toml` の `[tool.uv.workspace] members`（`domains/<領域>`）、`docker/Dockerfile` の依存キャッシュ用 `COPY`、`scripts/check_structure.py`（トップレベル許可をメンバーパス先頭セグメントから導出＋`domains/` 直下を member だけに限定する **C-DOMAIN** チェック追加）、`rule/directory-structure.md`・`README.md`・`CLAUDE.md` のツリーと新領域追加手順。
- **新領域の追加手順**（更新後）: `domains/<領域>/` を作成 → `members` に `domains/<領域>` を追加 → `.importlinter` contract 更新 → `system: *` ラベル整備。
- 検証は `python scripts/check_structure.py`（構造）＋ `docker compose run --rm lint`（境界）＋ `docker compose run --rm test`（pytest）。

## 関連ドキュメント・リンク

- [ADR-0002 複数領域を Modular Monolith × Bounded Context で共存させる](./0002-modular-monolith-bounded-context.md)（本 ADR が物理配置を更新する元の決定）
- [rule/directory-structure.md](../../rule/directory-structure.md)（正典トップレベル構成）
- [rule/naming.md](../../rule/naming.md)（R-NAME-1: kebab-case 英語）
