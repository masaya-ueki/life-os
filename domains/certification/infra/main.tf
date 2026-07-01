# certification サーバレス基盤（雛形 / P5・後続）
# 設計根拠: docs/adr/0011-certification-react-frontend-serverless.md
#
# 構成: API Gateway(HTTP) + Lambda(FastAPI/Mangum) + DynamoDB + S3/CloudFront(フロント配信)
# 注意: これは雛形。apply は後続フェーズ（#82 P5）で行う。AWS 認証情報はコミットしない
#       （`aws configure --profile cls` のプロファイルを使う）。

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.region
  profile = var.aws_profile
}

# --- DynamoDB: 出題履歴（出題済み/正誤フラグの根拠） ---------------------------
resource "aws_dynamodb_table" "attempts" {
  name         = "${var.name_prefix}-attempts"
  billing_mode = "PAY_PER_REQUEST" # 単一ユーザー・散発利用に最適（待機コスト $0）
  hash_key     = "email"
  range_key    = "question_id"

  attribute {
    name = "email"
    type = "S"
  }
  attribute {
    name = "question_id"
    type = "S"
  }

  tags = local.tags
}

# --- Lambda: FastAPI アプリ（Mangum アダプタ経由） -----------------------------
# ハンドラは certification.adapters.lambda_handler（Mangum は P5 で実装）。
resource "aws_lambda_function" "api" {
  function_name = "${var.name_prefix}-api"
  runtime       = "python3.12"
  handler       = "certification.adapters.lambda_handler.handler"
  filename      = var.lambda_zip_path
  role          = aws_iam_role.lambda.arn
  timeout       = 15
  memory_size   = 256

  environment {
    variables = {
      CERT_USER_EMAIL         = var.cert_user_email
      CERT_USER_PASSWORD_HASH = var.cert_user_password_hash # 平文は渡さない
      ATTEMPTS_TABLE          = aws_dynamodb_table.attempts.name
    }
  }

  tags = local.tags
}

resource "aws_iam_role" "lambda" {
  name               = "${var.name_prefix}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = local.tags
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- API Gateway (HTTP API) → Lambda -----------------------------------------
resource "aws_apigatewayv2_api" "http" {
  name          = "${var.name_prefix}-http"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = var.frontend_origins
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["authorization", "content-type"]
  }
  tags = local.tags
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
  tags        = local.tags
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

# --- S3 + CloudFront: フロント(React ビルド成果物) 配信 -----------------------
# バケットは非公開（OAC 経由の CloudFront からのみ参照）。SPA のため 403/404 は index.html。
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.name_prefix}-frontend"
  tags   = local.tags
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.name_prefix}-frontend-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  default_root_object = "index.html"
  comment             = "${var.name_prefix} frontend"

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  # SPA: オブジェクト無し(403/404)は index.html を返す
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = local.tags
}

# CloudFront(OAC) からのみ S3 読み取りを許可するバケットポリシー
data "aws_iam_policy_document" "frontend_bucket" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_bucket.json
}

locals {
  tags = {
    system  = "certification"
    project = "life-os"
  }
}
