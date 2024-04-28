resource "aws_iam_policy" "this" {
  name = "${var.name}-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowS3BucketAccess"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:PutObjectTagging"
        ]
        Resource = [
          "${var.results_bucket_arn}",
          "${var.results_bucket_arn}/*"
        ]
      }
    ]
  })
}
