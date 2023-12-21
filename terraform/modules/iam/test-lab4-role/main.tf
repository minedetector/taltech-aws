resource "aws_iam_role" "this" {
  name               = "${var.name}-role"
  assume_role_policy = data.aws_iam_policy_document.this.json

}

data "aws_iam_policy_document" "this" {
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
        Sid    = "GetNetworkData"
        Effect = "Allow"
        Action = [
          "ec2:DescribeRouteTables",
          "ec2:DescribeInternetGateways",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeSubnets"
        ]
        Resource = "*"
      },
      {
        Sid    = "DescribeInstances"
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Sid      = "UpdateLambdaFunction"
        Effect   = "Allow"
        Action   = "lambda:UpdateFunctionConfiguration"
        Resource = "arn:aws:lambda:eu-north-1:943666862273:function:test-lab4"
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