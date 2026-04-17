import json
import boto3
import requests
import os

def lambda_handler(event, context):
    # LOCALSTACK_HOSTNAME es la IP del "cerebro" de LocalStack dentro de la red de Docker.
    # Si no existe, usamos 'localhost' por defecto.
    lh = os.environ.get('LOCALSTACK_HOSTNAME', 'localhost')
    
    # Endpoints internos para servicios de AWS
    s3_endpoint = f"http://{lh}:4566"
    db_endpoint = f"http://{lh}:4566"
    
    # Endpoint para Ollama (Windows/Host externo a Docker)
    ollama_url = "http://host.docker.internal:11434/api/generate"
    
    # Configuración de clientes con los endpoints dinámicos
    s3 = boto3.client('s3', endpoint_url=s3_endpoint)
    
    try:
        # 1. Extraer información del evento de S3
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # 2. Descargar el contenido del archivo desde S3
        print(f"Descargando {key} desde el bucket {bucket}...")
        obj = s3.get_object(Bucket=bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        
        # 3. Preparar la petición para Ollama (IA Local)
        payload = {
            "model": "llama3:8b",
            "prompt": f"Resume este texto brevemente: {content}",
            "stream": False
        }
        
        print(f"Enviando contenido a Ollama en {ollama_url}...")
        # Aumentamos timeout a 120s porque la IA en la GTX 1650 puede tardar un poco
        response = requests.post(ollama_url, json=payload, timeout=120) 
        
        # Validar si la respuesta de Ollama es exitosa
        response.raise_for_status()
        
        data = response.json()
        summary = data.get('response', 'No se pudo generar el resumen')

        # 4. Guardar el resultado en DynamoDB
        print(f"Guardando resumen en DynamoDB...")
        dynamodb = boto3.resource('dynamodb', endpoint_url=db_endpoint)
        table = dynamodb.Table('IA_Processing_Results')
        table.put_item(Item={
            'file_id': key,
            'summary': summary,
            'status': 'processed'
        })

        print(f"Éxito: Archivo {key} procesado y guardado.")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Procesado correctamente", "file": key})
        }

    except Exception as e:
        # Este print es vital: aparecerá en 'docker logs localstack_main'
        print(f"Error detallado: {str(e)}") 
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }