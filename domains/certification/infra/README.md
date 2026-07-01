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

## 残作業（P5）

- Lambda ハンドラ `certification.adapters.lambda_handler`（Mangum アダプタ）の実装
- `InMemoryAttemptRepository` を DynamoDB 実装に差し替え（ports は既に抽象化済み）
- Lambda デプロイパッケージ（`build/lambda.zip`）のビルド手順
- CloudFront ディストリビューションと OAC、S3 バケットポリシー
- CI/CD（さらに後）
