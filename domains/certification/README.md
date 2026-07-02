# certification — 資格取得学習サイト

個人用の資格学習サイトの Bounded Context。**アーキタイプA（軽量ヘキサゴナル）**で構成する。
設計根拠: [ADR-0002](../../docs/adr/0002-modular-monolith-bounded-context.md)、
フロント/インフラの判断は [ADR-0011](../../docs/adr/0011-certification-react-frontend-serverless.md)。

## ユビキタス言語

| 用語 | 意味 |
|------|------|
| Certification（資格） | 学習対象の資格（初期は Snowflake SnowPro Core） |
| Genre（ジャンル） | 資格内の分野。出題の絞り込み単位 |
| Question（問題） | 4択の択一 / 複数選択。出題形式区分・正解・出題元リンクを持つ |
| Choice（選択肢） | 正解可否と NG 理由（誤答の理由）を持つ |
| QuizMode（出題モード） | ジャンルランダム / 全体試験 / 間違えた問題のみ（各10問） |
| AttemptRecord（出題履歴） | 出題済み・正誤フラグの根拠。問題集フィルタに使う |

## 内部構成（アーキタイプA）

```
src/certification/
├── public.py            # 他領域への唯一の契約（ADR-0002）
├── domain/              # 純粋ロジック（外部I/O非依存）
│   ├── models.py        # エンティティ・値オブジェクト
│   ├── quiz.py          # 選択肢シャッフル（ミリ秒シード）・出題選択
│   └── scoring.py       # 正誤判定・選択肢フィードバック
├── application/         # ユースケース
│   ├── ports.py         # リポジトリ抽象（ポート）
│   ├── auth.py          # 認証（単一ユーザー）
│   ├── quiz_service.py  # 出題・採点
│   └── question_bank.py # 問題集（ジャンル別・フィルタ）
└── adapters/            # 外部境界
    ├── repository.py    # JSON(問題)＋インメモリ(履歴)＋env(ユーザー)
    ├── security.py      # パスワードハッシュ（stdlib のみ）
    └── api.py           # FastAPI（オプション依存 `api`）

data/snowpro_core.json   # 初期問題データ（資格/ジャンル/問題）
frontend/                # React(Vite) フロント（Notion風・レスポンシブ）
infra/                   # Terraform（サーバレス。P5・後続）
```

## 境界（Context Map）

- 他領域からは `certification.public` のみ参照可（`.importlinter` で強制）。
- 現状は他領域連携なし。`public.py` は `CertificationSummary` のみ公開。

## 問題作成基盤（スキル＋サブエージェント＋整合性ゲート）

問題を全ジャンル分 網羅的に拡充するための再利用可能な基盤。方針の索引（スキル）と実行（サブエージェント）を分離し、データ品質はテストで機械的に守る。設計根拠は [ADR-0012](../../docs/adr/0012-certification-question-authoring-system.md)。

| 要素 | 場所 | 役割 |
|------|------|------|
| 問題作成スキル | [`.claude/skills/cert-question-authoring/`](../../.claude/skills/cert-question-authoring/SKILL.md) | 用途理解型の設問設計原則・NG理由・公式出典・採番規約・整合性ルールを索引化。`references/`（question-quality / schema-and-numbering / genre-doc-map）に各論。 |
| 登録サブエージェント | [`.claude/agents/snowpro-question-author.md`](../../.claude/agents/snowpro-question-author.md) | 指定ジャンルの問題を生成 → スキーマ/整合性検証 → `data/snowpro_core.json` へ登録。 |
| 整合性ゲート | [`tests/test_data_integrity.py`](tests/test_data_integrity.py) | id 一意・genre 整合・選択肢構造・正解数・NG理由・公式出典を `docker compose run --rm test` で強制。 |
| カバレッジ仕様 | `.claude/skills/cert-question-authoring/references/genre-doc-map.md` | ジャンル×主要トピック→公式ドキュメント(source_url) の被覆表。網羅性の基準。 |

**出題ジャンル（SnowPro Core COF-C03 の5ドメインに対応）**: `architecture` / `security` / `performance` / `data-loading` / `data-collaboration`（`data/snowpro_core.json` の `genres`）。

**使い方**: 特定ジャンルの問題を増やすときは `snowpro-question-author` に `genre_id` を渡す。全ジャンルを回すときは呼び出し側でジャンルごとにループし、都度スキル/エージェントの不足を改善する。

## ローカル実行

認証情報は環境変数で与える（平文パスワードはコミットしない）。

```bash
# バックエンド（FastAPI）
export CERT_USER_EMAIL="you@example.com"
export CERT_USER_PASSWORD="＜あなたのパスワード＞"   # or CERT_USER_PASSWORD_HASH
uv run --extra api uvicorn certification.adapters.api:app --reload --port 8000

# フロント（別ターミナル）
cd domains/certification/frontend && npm install && npm run dev
```

docker compose での起動は リポジトリルートの `compose.yaml`（`cert-backend` / `cert-frontend`）を参照。

## テスト・境界検査

```bash
docker compose run --rm test   # pytest（本領域のスモーク）
docker compose run --rm lint   # lint-imports（境界）
```
