variable "region" {
  description = "デプロイ先 AWS リージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "aws_profile" {
  description = "使用する AWS プロファイル（aws configure --profile cls）"
  type        = string
  default     = "cls"
}

variable "name_prefix" {
  description = "リソース名の接頭辞"
  type        = string
  default     = "life-os-cert"
}

variable "lambda_zip_path" {
  description = "Lambda デプロイパッケージ（FastAPI + Mangum）の zip パス。P5 でビルドする。"
  type        = string
  default     = "build/lambda.zip"
}

variable "cert_user_email" {
  description = "単一ユーザーのログインメール"
  type        = string
  default     = ""
}

variable "cert_user_password_hash" {
  description = "単一ユーザーのパスワードハッシュ（平文は渡さない）"
  type        = string
  default     = ""
  sensitive   = true
}

variable "frontend_origins" {
  description = "CORS 許可オリジン（CloudFront/S3 の URL）"
  type        = list(string)
  default     = ["*"]
}
