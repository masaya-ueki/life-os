# certification インフラ（Terraform・サーバレス）

**雛形（P5・後続）**。ローカル MVP（docker compose）が動いたあと、本番相当をサーバレスで構築する。
設計根拠: [ADR-0011](../../../docs/adr/0011-certification-react-frontend-serverless.md)。

## 構成

- **API Gateway (HTTP API)** → **Lambda**（FastAPI を Mangum でラップ）
- **DynamoDB**（`*-attempts`: 出題履歴 = 出題済み/正誤の根拠）
- **S3 + CloudFront**（React ビルド成果物の配信・SPA）

いずれも待機コストがほぼ $0。ECS の「普段停止・ログイン時起動」の鶏卵問題を回避する。

## 使い方（後続フェーズで実施）

```bash
# 認証情報はコミットしない。専用アカウントのプロファイルを使う。
aws configure --profile cls

cd domains/certification/infra
terraform init
terraform plan  -var "cert_user_email=you@example.com" -var "cert_user_password_hash=<hash>"
terraform apply -var "cert_user_email=you@example.com" -var "cert_user_password_hash=<hash>"
```

## 実装済み（P5 コード / IaC）

- Lambda ハンドラ `certification.adapters.lambda_handler.handler`（Mangum）✅
- DynamoDB リポジトリ `DynamoAttemptRepository`（`ATTEMPTS_TABLE` があれば api.py が自動採用）✅
- CloudFront + OAC + S3 バケットポリシー（SPA・非公開バケット）✅

## デプロイ（ワンコマンド）

`~/.aws` に `cls` プロファイル（静的キー）と docker があれば、`deploy.sh` が
Lambda パッケージビルド → `terraform apply` → フロントビルド → S3 同期 → CloudFront invalidation
までを一括で実行する（terraform/uv/node/aws-cli はすべて Docker で動く）。

```bash
CERT_USER_EMAIL='you@example.com' CERT_USER_PASSWORD='＜ログインPW＞' \
  bash domains/certification/infra/deploy.sh
```

平文パスワードは環境変数でのみ受け取り、ハッシュ化して Lambda 環境変数に入れる（リポジトリ・state に平文は残さない）。
完了時にフロント URL（CloudFront）と API URL を表示する。

### 個別実行（手動）

```bash
bash build_lambda.sh                      # Lambda zip をビルド
terraform init
terraform apply -var 'cert_user_email=...' -var 'cert_user_password_hash=...'
```

### クリーンアップ

```bash
terraform destroy   # 作成したリソースを削除（課金停止）
```

## 残作業

- CI/CD への deploy ステージ組み込み（さらに後）
- terraform state のリモート化（S3 backend）— 現状はローカル state
