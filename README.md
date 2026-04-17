# 🚀 Local AI Cloud: GitOps + Serverless + LLM (Ollama)

Este proyecto implementa una arquitectura de **Nube Privada Local** que emula servicios de AWS mediante **LocalStack**, gestiona la infraestructura como código con **Terraform** y procesa datos mediante Inteligencia Artificial local con **Ollama (Llama 3)**. Todo el ciclo de vida está automatizado con un flujo **GitOps** utilizando un GitHub Runner local.

---

## 🏗️ Arquitectura del Sistema

El flujo de datos sigue un modelo orientado a eventos (Event-Driven):

1. **Despliegue (GitOps):** Un `git push` activa el **GitHub Runner** local, que ejecuta `terraform apply` sobre **LocalStack**.
2. **Ingesta:** El usuario sube un archivo `.txt` a un bucket de **Amazon S3**.
3. **Procesamiento:** El evento de S3 dispara una función **AWS Lambda**.
4. **Inferencia de IA:** La Lambda se comunica con la API de **Ollama** (ejecutándose en el host) para resumir el texto.
5. **Persistencia:** El resumen generado se almacena en una tabla de **Amazon DynamoDB**.



---

## 📋 Pre-requisitos

Para ejecutar este proyecto en Windows, necesitas:

* **Docker Desktop**: Para ejecutar el contenedor de LocalStack.
* **Ollama**: Instalado y con el modelo Llama 3 descargado (`ollama pull llama3:8b`).
* **Terraform**: Binario instalado en el PATH.
* **AWS CLI**: Configurado con credenciales dummy (ej. `access_key=test`, `secret_key=test`).
* **GitHub Self-Hosted Runner**: Configurado y en estado `Idle` en tu PC.

---

## 🛠️ Configuración e Instalación

### 1. Preparar Ollama (IA Local)
Es crucial permitir que Docker se comunique con Ollama configurando las variables de entorno:

```powershell
# Configurar para que escuche en todas las interfaces
$env:OLLAMA_HOST="0.0.0.0"
# Iniciar el servidor
ollama serve