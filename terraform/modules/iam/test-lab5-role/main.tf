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
        Sid    = "DescribeTargetGroupsAndTags"
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:DescribeTargetGroups",
          "elasticloadbalancing:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Sid    = "DescribeLoadBalancersAndTags"
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:DescribeLoadBalancers",
          "elasticloadbalancing:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Sid    = "DescribeLaunchConfigurationsAndTags"
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Sid      = "DescribeAutoScalingGroups"
        Effect   = "Allow"
        Action   = "autoscaling:DescribeAutoScalingGroups"
        Resource = "*"
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