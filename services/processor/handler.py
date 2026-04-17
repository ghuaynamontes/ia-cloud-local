import json
import boto3
import urllib3  # Librería nativa, no necesita pip install
import os

def lambda_handler(event, context):
    lh = os.environ.get('LOCALSTACK_HOSTNAME', 'localhost')
    s3_endpoint = f"http://{lh}:4566"
    db_endpoint = f"http://{lh}:4566"
    
    # URL de Ollama en tu Windows
    ollama_url = "http://host.docker.internal:11434/api/generate"
    
    s3 = boto3.client('s3', endpoint_url=s3_endpoint)
    http = urllib3.PoolManager()
    
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        print(f"Descargando {key}...")
        obj = s3.get_object(Bucket=bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        
        payload = {
            "model": "llama3:8b",
            "prompt": f"Resume este texto brevemente: {content}",
            "stream": False
        }
        
        print(f"Llamando a Ollama en {ollama_url}...")
        encoded_data = json.dumps(payload).encode('utf-8')
        
        # Petición usando urllib3 (nativa)
        response = http.request(
            'POST', 
            ollama_url, 
            body=encoded_data, 
            headers={'Content-Type': 'application/json'},
            timeout=120.0
        )
        
        data = json.loads(response.data.decode('utf-8'))
        summary = data.get('response', 'No se pudo generar el resumen')

        print(f"Guardando en DynamoDB...")
        dynamodb = boto3.resource('dynamodb', endpoint_url=db_endpoint)
        table = dynamodb.Table('IA_Processing_Results')
        table.put_item(Item={
            'file_id': key,
            'summary': summary,
            'status': 'processed'
        })

        print(f"Éxito: {key} procesado.")
        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        print(f"Error detallado: {str(e)}")
        return {"statusCode": 500, "body": str(e)}