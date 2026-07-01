#!/usr/bin/env bash
# Lambda デプロイパッケージ（build/lambda.zip）をビルドする。
# certification は shared 非依存のため、certification パッケージ + data + api 依存
# （fastapi / mangum 系。boto3 は Lambda ランタイム同梱のため除外）を Lambda 用に固める。
#
# 実行には uv が必要。Docker で回す例:
#   docker run --rm -v "$PWD/../../..":/w -w /w/domains/certification/infra \
#     ghcr.io/astral-sh/uv:python3.12-bookworm-slim bash build_lambda.sh
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
cert="$(cd "$here/.." && pwd)"
build="$here/build"

rm -rf "$build/pkg" "$build/lambda.zip"
mkdir -p "$build/pkg"

# Lambda(python3.12/x86_64) 向けの依存をターゲット install（バイナリwheel固定）
uv pip install \
  --target "$build/pkg" \
  --python-platform x86_64-manylinux2014 \
  --python-version 3.12 \
  --only-binary :all: \
  fastapi mangum

# アプリ本体とデータを同梱
cp -r "$cert/src/certification" "$build/pkg/certification"
cp -r "$cert/data" "$build/pkg/data"

# zip 化（zip バイナリ非依存で python の shutil を使う）
python - "$build" <<'PY'
import shutil, sys
build = sys.argv[1]
shutil.make_archive(f"{build}/lambda", "zip", f"{build}/pkg")
PY

echo "built: $build/lambda.zip"
