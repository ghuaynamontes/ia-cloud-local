terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.67.0" # Forzamos la serie 4.x, que es 100% compatible con LocalStack 3.x
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true
  
  # Bloque de endpoints (Asegúrate de que estén todos)
  endpoints {
    s3       = "http://localhost:4566"
    lambda   = "http://localhost:4566"
    dynamodb = "http://localhost:4566"
    iam      = "http://localhost:4566"
  }
}

# Empaquetado automático de la Lambda
data "archive_file" "lambda_zip" {
  type        = "zip"
  # Cambiamos source_file por source_dir para que incluya TODO (librerías + código)
  source_dir  = "${path.module}/../services/processor"
  output_path = "${path.module}/../services/processor.zip"
}

# Bucket de S3
# 1. El Bucket sin configuraciones extra
resource "aws_s3_bucket" "input_bucket" {
  bucket = "ia-processed-bucket-v2"
  # Eliminamos cualquier bloque interno de configuration por ahora
}

# 2. La Tabla de DynamoDB
resource "aws_dynamodb_table" "results_table" {
  name           = "IA_Processing_Results"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "file_id"

  attribute {
    name = "file_id"
    type = "S"
  }

  # Añadimos un ciclo de vida para evitar que Terraform se desespere esperando
  lifecycle {
    create_before_destroy = true
  }
}

# Función Lambda
resource "aws_lambda_function" "processor" {
  filename      = data.archive_file.lambda_zip.output_path
  function_name = "ia_processor"
  role          = "arn:aws:iam::000000000000:role/lambda-role" # Mock ARN para LocalStack
  handler       = "handler.lambda_handler"
  runtime       = "python3.9"
  timeout       = 60 
  memory_size   = 256 # Un poco más de memoria ayuda al procesamiento
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