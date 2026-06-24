# ディレクトリ構成ルール

> **親**: [rule/README.md](./README.md) ／ **根拠**: [ADR-0002](../../docs/adr/0002-modular-monolith-bounded-context.md)・[ADR-0005](../../docs/adr/0005-directory-governance-daily-keeper.md)・[ADR-0006](../../docs/adr/0006-docker-test-environment.md)

「リポジトリの正典構成」と「どこに何を置くか」を定める。検査は `scripts/check_structure.py`。

---

## 正典トップレベル構成

トップ階層に置けるのは **(1) 領域（Bounded Context）**・**(2) content 領域**・**(3) 支援ディレクトリ**・
**(4) 許可されたルートファイル** の4種だけ。これ以外をルート直下に増やさない。
領域（Bounded Context）は数が増えてもトップ階層を散らかさないよう **`domains/` コンテナ配下**にまとめる
（`shared` は Shared Kernel = 領域非依存のため例外的にルート直下に置く）。根拠は [ADR-0009](../../docs/adr/0009-group-domains-under-domains-dir.md)。

```
life-os/
├── domains/           # 領域コンテナ: Bounded Context をまとめる親（直下は member だけ）
│   ├── task/              # (1) 領域: タスク管理（archetype A）          ※ workspace member
│   ├── content-sales/     # (1) 領域: 販売管理（archetype A）            ※ workspace member
│   ├── media/             # (1) 領域: 画像・動画管理（archetype B）       ※ workspace member
│   ├── travel/            # (1) 領域: 旅行の行先管理（archetype B）       ※ workspace member
│   └── english/           # (1) 領域: 英語学習（archetype B）             ※ workspace member
├── shared/            # (1) Shared Kernel（領域非依存の最小基盤）※ workspace member・ルート直下
├── presentation/      # (2) content 領域（コード無し）
├── docs/              # (2) content: 設計ドキュメント（adr/ など）
├── guides/            # (2) content: 開発運用の手順・ルール
├── scripts/           # (3) 支援: 自動化スクリプト
├── docker/            # (3) 支援: テスト実行用 Dockerfile（ADR-0006）
├── .claude/           # (3) 支援: Claude Code エージェント/スキル/構造ルール
├── .github/           # (3) 支援: Issue/PR/workflow 設定
├── README.md          # (4) ルートファイル（ハブ・索引）
├── CLAUDE.md          # (4) Claude Code のプロジェクト指示書
├── pyproject.toml     # (4) uv workspace ルート
├── uv.lock            # (4) 生成物だが再現性のためコミット
├── compose.yaml       # (4) ローカル実行用 Docker Compose（ADR-0006）
├── .importlinter      # (4) 領域境界の強制
├── .dockerignore      # (4) Docker ビルドコンテキスト除外
└── .gitignore         # (4)
```

### 種別の定義

| 種別 | 性質 | 内部構成の決まり |
|---|---|---|
| **領域コンテナ `domains/`** | (1) の領域をまとめる親ディレクトリ。それ自体はコードを持たない。 | 直下には領域（member）だけを置く。`scripts/check_structure.py` の C-DOMAIN で検査。 |
| **領域（Bounded Context）** | Python コードを持つ。uv workspace member。`domains/<領域>/` に置く（`shared` のみルート直下）。 | archetype A or B（下記）。`public.py` が唯一の対外契約。 |
| **content 領域** | コードを持たない成果物・資料。member でも BC でもない。 | 自由だが浅く・命名一貫。 |
| **支援ディレクトリ** | ツール・設定。 | 各ツールの規約に従う。 |
| **ルートファイル** | リポジトリ全体の入口・設定。 | 許可リスト（下記 root hygiene）のみ。 |

---

## 配置ルール

### R-STRUCT-1: 領域内は archetype に従い同形を保つ
領域の内部構成は [ADR-0002](../../docs/adr/0002-modular-monolith-bounded-context.md) の 2 archetype を使い分ける（詳細・根拠は ADR を正本とし、ここでは要約のみ）。

- **archetype A（動く領域）**: `src/<pkg>/` に `domain` / `application` / `adapters` ＋ `public.py`（例: `task` / `content-sales`）
- **archetype B（データ領域）**: `src/<pkg>/` に `models` / `index` ＋ `public.py` ＋ `data/`（例: `media` / `travel`）

同一 archetype の領域どうしは**同じ形**にする（規約優先）。

### R-STRUCT-2: 領域間の越境は `public.py` のみ
他領域の内部（`*.domain` / `*.application` / `*.adapters` / `*.models` / `*.index`）を直接 import しない。
これは [`.importlinter`](../../.importlinter) で機械強制される。領域直下に `public.py` 以外のトップレベルモジュールを増やしたら `.importlinter` に追記する。

### R-STRUCT-3: code と data を分離する
データ・固定値・成果物はコードに混ぜず、領域の `data/` 等に置く。コードツリーにデータを散らさない。

### R-STRUCT-4: 生成物はコミットしない（gitignore する）
ビルド/キャッシュ/仮想環境などの生成物は [`.gitignore`](../../.gitignore) で除外する。
例外は **再現性のために必要なロックファイル**（`uv.lock`）のみ。生成物をリポジトリに置かない。

### R-STRUCT-5: ルート直下を汚さない（root hygiene）
リポジトリ直下に置けるファイルは次の許可リストだけ。**それ以外の単発ファイルをルートに置かない。**

```
README.md  CLAUDE.md  pyproject.toml  uv.lock  .importlinter  .gitignore
compose.yaml  .dockerignore   （← テスト実行環境 / ADR-0006）
.python-version  LICENSE  .pre-commit-config.yaml   （← 必要になれば許可）
```

置き場所が無いものをルートに退避させない。置き場所が無いこと自体が設計の綻びのサイン。

### R-STRUCT-6: 深さは浅く一定に保つ
階層は必要最小限にする。同種のものが領域ごとにバラバラの深さにならないようにする（規約優先）。

### R-STRUCT-7: 不要物はアーカイブまたは削除
使われなくなったものを「念のため」放置しない。役目を終えたものは削除し、履歴として残すべき意思決定は
[ADR](../../docs/adr/) に `置き換え済み` 等で残す（ADR 自体は削除しない）。

---

## 領域・content 領域の追加

- **新領域（BC）の追加**: `domains/<領域>/` を作成 → `pyproject.toml` の `members` に `domains/<領域>` を追加 → `.importlinter` のコントラクト更新 → `system: *` ラベル整備。**手順の正本は [ADR-0002](../../docs/adr/0002-modular-monolith-bounded-context.md)**（配置先は [ADR-0009](../../docs/adr/0009-group-domains-under-domains-dir.md)。ここでは重複させない）。
- **新 content 領域の追加**: コードを持たないなら member/`.importlinter`/`public.py` は不要（[ADR-0003](../../docs/adr/0003-presentation-system.md) の `presentation/` が前例）。

> 関連: ドキュメントの置き方は [documentation.md](./documentation.md)、命名は [naming.md](./naming.md)。
