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
