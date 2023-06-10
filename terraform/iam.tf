resource "aws_iam_role" "lambda-dynamodb-role" {
  name = "LambdaDynamoDBRole"
  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Action" : "sts:AssumeRole",
        "Principal" : {
          "Service" : "lambda.amazonaws.com"
        },
        "Effect" : "Allow",
        "Sid" : ""
      }
    ]
  })
}

resource "aws_iam_policy" "policy" {
  name        = "LambdaDynamoDBPolicy"
  path        = "/"
  description = "AWS IAM Policy for managing IAM Role"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow"
        "Action" : [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "ec2:DescribeNetworkInterfaces",
          "ec2:CreateNetworkInterface",
          "ec2:DeleteNetworkInterface",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem",
          "dynamodb:BatchGetItem",
          "sqs:ReceiveMessage",
          "s3:GetObject",
          "events:*",
          "schemas:*",
          "scheduler:*",
          "pipes:*",
          "sqs:SendMessage"
        ],
        "Resource" : [
          "*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "policy-attachment" {
  role       = aws_iam_role.lambda-dynamodb-role.name
  policy_arn = aws_iam_policy.policy.arn
}