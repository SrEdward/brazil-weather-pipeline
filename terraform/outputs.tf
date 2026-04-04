output "s3_bucket_name" {
  description = "ARN of the S3 bucket"
  value = aws_s3_bucket.weather_raw.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value = aws_s3_bucket.weather_raw.arn
}

output "iam_user_name" {
  description = "IAM user name"
  value = aws_iam_user.weather_pipeline.name
}

output "iam_access_key_id" {
  description = "IAM access key ID"
  value = aws_iam_access_key.weather_pipeline.id
}

output "iam_secret_access_key" {
  description = "IAM secret access key"
  value = aws_iam_access_key.weather_pipeline.secret
  sensitive = true
}
