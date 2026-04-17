import json
import boto3
import requests
import os

def lambda_handler(event, context):
    # CAMBIO 1: Para hablar con S3/Dynamo desde DENTRO de LocalStack usamos localhost
    # o mejor aún, dejamos que boto3 use los valores por defecto de LocalStack.
    s3_endpoint = "http://localhost:4566"
    db_endpoint = "http://localhost:4566"
    
    # CAMBIO 2: Ollama SÍ necesita host.docker.internal porque vive en Windows (fuera de Docker)
    ollama_url = "http://host.docker.internal:11434/api/generate"
    
    s3 = boto3.client('s3', endpoint_url=s3_endpoint)
    
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        obj = s3.get_object(Bucket=bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        
        payload = {
            "model": "llama3:8b",
            "prompt": f"Resume este texto brevemente: {content}",
            "stream": False
        }
        
        # Aumentamos el timeout del request para esperar a la IA
        response = requests.post(ollama_url, json=payload, timeout=120) 
        data = response.json()
        summary = data.get('response', 'No se pudo generar resumen')

        dynamodb = boto3.resource('dynamodb', endpoint_url=db_endpoint)
        table = dynamodb.Table('IA_Processing_Results')
        table.put_item(Item={
            'file_id': key,
            'summary': summary,
            'status': 'processed'
        })

        print(f"Éxito: Archivo {key} procesado.")
        return {"status": 200, "body": "Procesado correctamente"}

    except Exception as e:
        print(f"Error detallado: {str(e)}") # Esto saldrá en docker logs
        return {"status": 500, "body": str(e)}