"""AWS Lambda ハンドラ — FastAPI アプリを Mangum でラップする（P5）。

API Gateway(HTTP API) → Lambda のプロキシ統合で呼ばれる。
デプロイパッケージには api オプション依存（mangum / fastapi / boto3）が必要。

Terraform の handler 設定: ``certification.adapters.lambda_handler.handler``
"""

from __future__ import annotations

from mangum import Mangum

from .api import app

handler = Mangum(app)
