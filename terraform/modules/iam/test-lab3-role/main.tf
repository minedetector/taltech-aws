resource "aws_iam_role" "this" {
  name               = "${var.name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = [
      "sts:AssumeRole",
    ]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_policy" "this" {
  name = "${var.name}-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ListAllBuckets"
        Effect   = "Allow"
        Action   = "s3:ListAllMyBuckets"
        Resource = "*"
      },
      {
        Sid    = "BucketLevelPermissions"
        Effect = "Allow"
        Action = [
          "s3:GetBucketTagging",
          "s3:GetBucketWebsite"

        ]
        Resource = [
          "arn:aws:s3:::ica0017-*"
        ]
      },
      {
        Sid      = "AllowToUpdateTheLambdaFunction"
        Effect   = "Allow",
        Action   = "lambda:UpdateFunctionConfiguration",
        Resource = "arn:aws:lambda:eu-north-1:943666862273:function:test-lab3"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "test_lab" {
  policy_arn = aws_iam_policy.this.arn
  role       = aws_iam_role.this.name
}

resource "aws_iam_role_policy_attachment" "grade_student" {
  policy_arn = var.pass_students_policy_arn
  role       = aws_iam_role.this.name
}