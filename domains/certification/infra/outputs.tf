output "api_endpoint" {
  description = "API Gateway のエンドポイント URL"
  value       = aws_apigatewayv2_api.http.api_endpoint
}

output "attempts_table" {
  description = "出題履歴テーブル名"
  value       = aws_dynamodb_table.attempts.name
}

output "frontend_bucket" {
  description = "フロント配信 S3 バケット"
  value       = aws_s3_bucket.frontend.bucket
}
