# 命名規約

> **親**: [rule/README.md](./README.md)

層ごとに 1 つの流儀を選び、混在させない。

---

## R-NAME-1: ディレクトリ・ドキュメント・スクリプトは kebab-case

リポジトリのディレクトリ名、`docs/` `guides/` `rule/` 配下の Markdown、`scripts/` のファイルは
小文字の **kebab-case**（`a-z 0-9 -`、必要に応じて `.`）。

- ✅ `directory-structure.md` / `content-sales/` / `setup-github-labels.sh`
- ❌ `DirectoryStructure.md` / `contentSales/` / `Setup_Labels.sh`

## R-NAME-2: Python パッケージ・モジュールは snake_case

Python の import 対象は **snake_case**（PEP 8）。
領域ディレクトリが kebab-case でも、その中の import パッケージは snake_case にする。

- 例: ディレクトリ `content-sales/` ／ パッケージ `content_sales`（`src/content_sales/`）

## R-NAME-3: ADR ファイル名は `NNNN-kebab-title.md`

ADR は連番 4 桁 + kebab-case タイトル。例: `0005-directory-governance-daily-keeper.md`。
詳細手順の正本は [docs/adr/README.md](../docs/adr/README.md)。

## R-NAME-4: ブランチ・コミットの命名

ブランチ（`{type}/issue-{N}-{kebab}`）とコミット（Conventional Commits）の命名は
**正本を [guides/development-policy/issue-operation-rules.md](../guides/development-policy/issue-operation-rules.md) とし、ここでは重複させない**（[R-DOC-1](./documentation.md)）。

## R-NAME-5: 名前は役割を表す（叫ぶ）

ディレクトリ・ファイル名は中身の「何であるか」を表す。`utils/` `common/` `misc/` のような
何でも入る曖昧な入れ物を作らない（凝集を壊す）。`shared/` は ADR-0002 で意図的に最小に保つ例外。
