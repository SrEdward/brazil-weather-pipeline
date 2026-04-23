# Role IAM para o Snowflake acessar a Glue e o Iceberg
resource "aws_iam_role" "snowflake_iceberg_role" {
  name = "snowflake-iceberg-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::194317476460:user/k09d1000-s"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringLike = {
            "sts:ExternalId" = "TTB39921_SFCRole=2_*"
          }
        }
      }
    ]
  })

  tags = {
    Project = "brazil-weather-pipeline"
  }
}

# Política para acesso ao S3
resource "aws_iam_role_policy" "snowflake_s3_policy" {
  name = "snowflake-s3-iceberg-policy"
  role = aws_iam_role.snowflake_iceberg_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          "arn:aws:s3:::brazil-weather-pipeline-raw",
          "arn:aws:s3:::brazil-weather-pipeline-raw/*"
        ]
      }
    ]
  })
}

# Política para acesso ao Glue
resource "aws_iam_role_policy" "snowflake_glue_policy" {
  name = "snowflake-glue-iceberg-policy"
  role = aws_iam_role.snowflake_iceberg_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = {
      Effect = "Allow"
      Action = [
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:GetTable",
        "glue:GetTables",
        "glue:GetPartition",
        "glue:GetPartitions"
      ]
      Resource = [
        "arn:aws:glue:us-east-1:${var.aws_account_id}:catalog",
        "arn:aws:glue:us-east-1:${var.aws_account_id}:database/brazil_weather",
        "arn:aws:glue:us-east-1:${var.aws_account_id}:table/brazil_weather/*"
      ]
    }
  })
}

# Output da ARN da role do Snowflake
output "snowflake_role_arn" {
  value = aws_iam_role.snowflake_iceberg_role.arn
}
