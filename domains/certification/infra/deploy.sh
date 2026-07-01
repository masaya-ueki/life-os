#!/usr/bin/env bash
# 資格学習サイトを AWS(サーバレス) に一括デプロイする。
#
# 前提:
#   - docker が使えること（terraform/uv/node/aws-cli はすべて Docker で実行）
#   - ~/.aws に `cls` プロファイル（静的キー）が設定済み
#
# 使い方:
#   CERT_USER_EMAIL='you@example.com' CERT_USER_PASSWORD='＜ログインPW＞' \
#     bash domains/certification/infra/deploy.sh
#
# 平文パスワードは環境変数でのみ受け取り、ハッシュ化して Lambda 環境変数に入れる
# （リポジトリ・state に平文は残さない）。terraform state はこの infra/ 配下に作られる。
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../.." && pwd)"

: "${CERT_USER_EMAIL:?CERT_USER_EMAIL を指定してください}"
: "${CERT_USER_PASSWORD:?CERT_USER_PASSWORD を指定してください}"

UV=ghcr.io/astral-sh/uv:python3.12-bookworm-slim
TF=hashicorp/terraform:1.9
NODE=node:20-slim
AWSCLI=amazon/aws-cli:latest

echo "==> [1/6] Lambda デプロイパッケージをビルド"
docker run --rm -v "$root":/w -w /w/domains/certification/infra -e UV_LINK_MODE=copy \
  "$UV" bash build_lambda.sh

echo "==> [2/6] パスワードハッシュを生成"
HASH=$(docker run --rm -v "$root":/w -w /w \
  -e UV_PROJECT_ENVIRONMENT=/opt/venv -e UV_LINK_MODE=copy \
  -e CERT_USER_PASSWORD="$CERT_USER_PASSWORD" \
  "$UV" bash -c 'uv sync --frozen --quiet >/dev/null 2>&1; \
    /opt/venv/bin/python -c "import os; from certification.adapters.security import hash_password; print(hash_password(os.environ[\"CERT_USER_PASSWORD\"]))"')

echo "==> [3/6] terraform apply（インフラ作成）"
docker run --rm --entrypoint sh \
  -v "$here":/w -v "$HOME/.aws":/root/.aws:ro -w /w \
  -e AWS_PROFILE=cls \
  -e TF_VAR_cert_user_email="$CERT_USER_EMAIL" \
  -e TF_VAR_cert_user_password_hash="$HASH" \
  "$TF" -c "terraform init -input=false && terraform apply -auto-approve -input=false"

echo "==> [4/6] terraform output を取得"
get_output() {
  docker run --rm --entrypoint sh -v "$here":/w -w /w "$TF" -c "terraform output -raw $1"
}
API=$(get_output api_endpoint)
BUCKET=$(get_output frontend_bucket)
DIST=$(get_output cloudfront_distribution_id)
URL=$(get_output frontend_url)

echo "==> [5/6] フロントをビルド（VITE_API_BASE=$API）"
docker run --rm -v "$root/domains/certification/frontend":/app -w /app \
  -e VITE_API_BASE="$API" \
  "$NODE" sh -c "npm ci || npm install --no-audit --no-fund; npm run build"

echo "==> [6/6] S3 へ同期 + CloudFront invalidation"
docker run --rm -v "$root/domains/certification/frontend/dist":/dist \
  -v "$HOME/.aws":/root/.aws:ro -e AWS_PROFILE=cls \
  "$AWSCLI" s3 sync /dist "s3://$BUCKET" --delete
docker run --rm -v "$HOME/.aws":/root/.aws:ro -e AWS_PROFILE=cls \
  "$AWSCLI" cloudfront create-invalidation --distribution-id "$DIST" --paths "/*"

echo
echo "✅ デプロイ完了"
echo "   フロント: $URL"
echo "   API:     $API"
echo "   ※ CloudFront の反映に数分かかる場合があります。ログインは $CERT_USER_EMAIL。"
