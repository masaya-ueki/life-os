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

## 残作業（実行のみ・要 AWS 認証情報）

- `terraform apply`（`aws configure --profile cls` の認証情報が必要）
- Lambda デプロイパッケージ（`build/lambda.zip`）のビルド
  例: `uv pip install --target build/pkg 'certification[api]'` 相当 + アプリを同梱して zip
- ビルド済みフロント（`frontend/dist`）を S3 バケットへ同期 + CloudFront invalidation
- CI/CD（さらに後）
