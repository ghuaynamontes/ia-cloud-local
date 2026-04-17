import json
import boto3
import requests
import os

def lambda_handler(event, context):
    # LocalStack usa una URL interna para comunicarse con otros servicios
    s3_endpoint = "http://host.docker.internal:4566"
    db_endpoint = "http://host.docker.internal:4566"
    
    s3 = boto3.client('s3', endpoint_url=s3_endpoint)
    
    try:
        # 1. Extraer información del evento de S3
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # 2. Leer el archivo
        obj = s3.get_object(Bucket=bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        
        # 3. Llamada a Ollama (IA Local)
        # Importante: host.docker.internal permite salir del contenedor a tu Windows
        ollama_url = "http://host.docker.internal:11434/api/generate"
        payload = {
            "model": "llama3:8b",
            "prompt": f"Resume este texto brevemente: {content}",
            "stream": False
        }
        
        response = requests.post(ollama_url, json=payload)
        summary = response.json().get('response', 'No se pudo generar resumen')

        # 4. Guardar en DynamoDB
        dynamodb = boto3.resource('dynamodb', endpoint_url=db_endpoint)
        table = dynamodb.Table('IA_Processing_Results')
        table.put_item(Item={
            'file_id': key,
            'summary': summary,
            'status': 'processed'
        })

        return {"status": 200, "body": "Procesado correctamente"}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"status": 500, "body": str(e)}