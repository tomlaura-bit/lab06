# Infraestructura AWS

`lab6-stack.yaml` crea la infraestructura usada para el laboratorio: EC2, RDS PostgreSQL, grupos de seguridad, Secrets Manager y un rol IAM. Recibe como parámetros el bucket S3 privado, la clave del ZIP, VPC y tres subredes.

La instancia instala Docker, descarga el proyecto desde S3 y levanta ambas aplicaciones. La administración usa RDS; el RAG usa pgvector en un volumen Docker y Amazon Bedrock como generador.

Para eliminar los recursos creados por la plantilla:

```bash
aws cloudformation delete-stack --stack-name lab6-aplicacion --region us-east-2
aws cloudformation wait stack-delete-complete --stack-name lab6-aplicacion --region us-east-2
```

El bucket de artefactos se administra aparte y debe vaciarse antes de eliminarlo.
