terraform {
	required_providers {
		aws = {
			source = "hashicorp/aws"
			version = "-> 5.0"
		}
	}
}

provider "aws" {
	region = var.aws_region
}



# S3 Bucket

resource "aws_s3_bucket" "weather_raw" {
  bucket = var.s3_bucket_name

  tags = {
    Project = "brazil-weather-pipeline"
    Environment = "dev"
    ManagedBy = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "weather_raw" {
  bucket = aws_s3_bucket.weather_raw.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "weather_raw" {
  bucket = aws_s3_bucket.weather_raw.id

  rule {
    id = "expire-old-raw-data"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    transition {
      days = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days = 180
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "weather_raw" {
  bucket = aws_s3_bucket.weather_raw.id

  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}



# IAM User

resource "aws_iam_user" "weather_pipeline" {
  name = "weather-pipeline-user"

  tags = {
    Project = "brazil-weather-pipeline"
    ManagedBy = "terraform"
  }
}

resource "aws_iam_user_policy" "weather_pipeline_s3" {
  name = "weather-pipeline-s3-policy"
  user = aws_iam_user.weather_pipeline.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.weather_raw.arn,
          "${aws_s3_bucket.weather_raw.arn}/*"
        ]
      }
    ]
  })
}
