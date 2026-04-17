provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3       = var.localstack_endpoint
    lambda   = var.localstack_endpoint
    dynamodb = var.localstack_endpoint
    iam      = var.localstack_endpoint
  }
}

# Empaquetado automático de la Lambda
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../services/processor/handler.py"
  output_path = "${path.module}/../services/processor/handler.zip"
}

# Bucket de S3
resource "aws_s3_bucket" "input_bucket" {
  bucket = "ia-input-bucket"
}

# Tabla de DynamoDB
resource "aws_dynamodb_table" "results_table" {
  name         = "IA_Processing_Results"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "file_id"

  attribute {
    name = "file_id"
    type = "S"
  }
}

# Función Lambda
resource "aws_lambda_function" "processor" {
  filename      = data.archive_file.lambda_zip.output_path
  function_name = "ia_processor"
  role          = "arn:aws:iam::000000000000:role/lambda-role" # Mock ARN para LocalStack
  handler       = "handler.lambda_handler"
  runtime       = "python3.9"

  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
}

# Configuración de notificación: S3 activa la Lambda
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.input_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor.arn
    events              = ["s3:ObjectCreated:*"]
  }
}

# Permiso para que S3 invoque la Lambda
resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.input_bucket.arn
}