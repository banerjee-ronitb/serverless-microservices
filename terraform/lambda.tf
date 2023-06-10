resource "aws_lambda_layer_version" "lambda_layer" {
  filename            = "/home/runner/work/serverless-microservices/serverless-microservices/shared/libs/layers.zip"
  compatible_runtimes = ["python3.9"]
  layer_name          = "order-libs"
}
resource "aws_lambda_function" "create-order-function" {
  function_name    = "create-order-function"
  filename         = "/home/runner/work/serverless-microservices/serverless-microservices/create-order.zip"
  role             = aws_iam_role.lambda-dynamodb-role.arn
  description      = "Lambda Function"
  handler          = "services.order-service.create-order.main.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("/home/runner/work/serverless-microservices/serverless-microservices/create-order.zip")
  timeout          = 15
  memory_size      = 128
  layers           = ["arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:24", aws_lambda_layer_version.lambda_layer.arn]
}

resource "aws_lambda_function" "cancel-order-function" {
  function_name    = "cancel-order-function"
  role             = aws_iam_role.lambda-dynamodb-role.arn
  filename         = "/home/runner/work/serverless-microservices/serverless-microservices/cancel-order.zip"
  description      = "Lambda Function"
  handler          = "services.order-service.cancel-order.main.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("/home/runner/work/serverless-microservices/serverless-microservices/cancel-order.zip")
  timeout          = 15
  memory_size      = 128
  layers           = ["arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:24", aws_lambda_layer_version.lambda_layer.arn]
}
resource "aws_lambda_function" "confirm-order-function" {
  function_name    = "confirm-order-function"
  role             = aws_iam_role.lambda-dynamodb-role.arn
  filename         = "/home/runner/work/serverless-microservices/serverless-microservices/confirm-order.zip"
  description      = "Lambda Function"
  handler          = "services.order-service.confirm-order.main.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("/home/runner/work/serverless-microservices/serverless-microservices/confirm-order.zip")
  timeout          = 15
  memory_size      = 128
  layers           = ["arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:24", aws_lambda_layer_version.lambda_layer.arn]
}

resource "aws_lambda_function" "create-payment-intent-function" {
  function_name    = "create-payment-intent-function"
  role             = aws_iam_role.lambda-dynamodb-role.arn
  filename         = "/home/runner/work/serverless-microservices/serverless-microservices/create-payment-intent.zip"
  description      = "Lambda Function"
  handler          = "services.payment-service.create-payment-intent.main.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("/home/runner/work/serverless-microservices/serverless-microservices/create-payment-intent.zip")
  timeout          = 15
  memory_size      = 128
  layers           = ["arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:24", "arn:aws:lambda:us-east-1:251263185539:layer:stripe-layer:2"]
  environment {
    variables = {
      STRIPE_API_KEY =  var.stripe_api_key
    }
  }
}

resource "aws_lambda_function" "payment-intent-webhook-function" {
  function_name    = "payment-intent-webhook-function"
  role             = aws_iam_role.lambda-dynamodb-role.arn
  filename         = "/home/runner/work/serverless-microservices/serverless-microservices/payment-intent-webhook.zip"
  description      = "Lambda Function"
  handler          = "services.payment-service.payment-intent-webhook.main.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("/home/runner/work/serverless-microservices/serverless-microservices/payment-intent-webhook.zip")
  timeout          = 15
  memory_size      = 128
  layers           = ["arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:24", "arn:aws:lambda:us-east-1:251263185539:layer:stripe-layer:2"]
}

resource "aws_lambda_function" "retrieve-catalog-function" {
  function_name    = "retrieve-catalog-function"
  role             = aws_iam_role.lambda-dynamodb-role.arn
  filename         = "/home/runner/work/serverless-microservices/serverless-microservices/retrieve-catalog.zip"
  description      = "Lambda Function"
  handler          = "services.catalog-service.retrieve-catalog.main.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("/home/runner/work/serverless-microservices/serverless-microservices/retrieve-catalog.zip")
  timeout          = 15
  memory_size      = 128
  layers           = ["arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:24"]
}
resource "aws_lambda_function" "update-catalog-function" {
  function_name    = "update-catalog-function"
  role             = aws_iam_role.lambda-dynamodb-role.arn
  filename         = "/home/runner/work/serverless-microservices/serverless-microservices/update-catalog.zip"
  description      = "Lambda Function"
  handler          = "services.catalog-service.update-catalog.main.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("/home/runner/work/serverless-microservices/serverless-microservices/update-catalog.zip")
  timeout          = 15
  memory_size      = 128
  layers           = ["arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:24"]
}
resource "aws_lambda_function" "refund-payment-function" {
  function_name    = "refund-payment-function"
  role             = aws_iam_role.lambda-dynamodb-role.arn
  filename         = "/home/runner/work/serverless-microservices/serverless-microservices/refund-payment.zip"
  description      = "Lambda Function"
  handler          = "services.payment-service.refund-payment.main.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("/home/runner/work/serverless-microservices/serverless-microservices/refund-payment.zip")
  timeout          = 15
  memory_size      = 128
  layers           = ["arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:24", "arn:aws:lambda:us-east-1:251263185539:layer:stripe-layer:2"]

  environment {
    variables = {
      STRIPE_API_KEY =  var.stripe_api_key
    }
  }
}
#resource "aws_lambda_event_source_mapping" "sqs-event-source" {
#  event_source_arn = aws_sqs_queue.message_queue.arn
#  function_name    = aws_lambda_function.update-catalog-function
#
#  filter_criteria {
#    filter {
#      pattern = jsonencode({
#        body = {
#          Temperature : [{ numeric : [">", 0, "<=", 100] }]
#          Location : ["New York"]
#        }
#      })
#    }
#  }
#}