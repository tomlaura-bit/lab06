# Laboratorio 6 - Solución

## URLs públicas verificadas

- Administración: http://ec2-18-118-253-138.us-east-2.compute.amazonaws.com:8000
- RAG con Amazon Bedrock: http://ec2-18-118-253-138.us-east-2.compute.amazonaws.com:8001
- Repositorio: https://github.com/tomlaura-bit/lab06

La contraseña inicial del administrador se mantiene en AWS Secrets Manager (`lab6/admin-credentials`) y no se publica en el repositorio.

Este repositorio contiene las dos aplicaciones solicitadas:

- `pregunta1_admin_aws`: panel web de administración de usuarios con FastAPI, PostgreSQL, Amazon S3, Docker y guía de despliegue en EC2.
- `pregunta2_rag`: aplicación RAG en español con ingesta idempotente de tres PDF, PostgreSQL con pgvector, búsqueda semántica, citas por documento y página, visualización de pasajes y generación mediante Amazon Bedrock, Ollama u OpenAI.

Cada carpeta incluye su propio `README.md`, variables de entorno de ejemplo, `Dockerfile` y `docker-compose.yml`.

## Requisitos

- Docker y Docker Compose.
- Para la pregunta 1: una cuenta AWS con un bucket S3 y, para producción, RDS PostgreSQL y EC2.
- Para la pregunta 2: los tres PDF entregados por el docente.

## Ejecución rápida

```bash
cd pregunta1_admin_aws
cp .env.example .env
docker compose up --build
```

Abra `http://localhost:8000`.

```bash
cd pregunta2_rag
cp .env.example .env
docker compose up --build
```

Abra `http://localhost:8001`.

## Despliegue AWS incluido

El archivo `infra/lab6-stack.yaml` reproduce la arquitectura usada: EC2 con Docker y acceso por Systems Manager, RDS PostgreSQL privado, S3 privado, Secrets Manager y rol IAM de instancia. El RAG usa Amazon Bedrock mediante credenciales temporales del rol, sin keys en archivos.
