# Pregunta 1 - Administración de usuarios en AWS

## Funcionalidad implementada

- Inicio de sesión exclusivo para administradores con JWT.
- CRUD de usuarios, validación de correo único y bloqueo de autoeliminación.
- Carga de JPEG, PNG o WebP a S3, límite configurable y cifrado SSE-S3.
- Base de datos PostgreSQL compatible con Amazon RDS.
- Panel web adaptable, API documentada en `/docs` y comprobación `/health`.
- Contenedor Docker y composición local con PostgreSQL.

## Prueba local

```bash
cp .env.example .env
docker compose up --build
```

Abra `http://localhost:8000`. Para probar S3 localmente, configure credenciales AWS mediante el mecanismo estándar del SDK y complete `S3_BUCKET`.

## Despliegue en AWS

1. Cree un bucket S3 privado. Active bloqueo de acceso público, cifrado y CORS solo para el dominio de la aplicación.
2. Cree RDS PostgreSQL en subredes privadas. Permita el puerto 5432 únicamente desde el grupo de seguridad de EC2.
3. Cree un rol IAM para EC2 limitado a `s3:GetObject`, `s3:PutObject` y `s3:DeleteObject` sobre `arn:aws:s3:::BUCKET/profiles/*`.
4. Lance EC2 con Amazon Linux 2023, permita SSH solo desde la IP administrativa y HTTP/HTTPS desde Internet.
5. Instale Docker, copie el proyecto y cambie `DATABASE_URL` por el endpoint de RDS. No coloque claves AWS en `.env`; el SDK usará el rol de instancia.
6. Para usar RDS en vez del contenedor PostgreSQL local, ejecute `docker compose -f docker-compose.aws.yml up -d --build`. En producción use un proxy TLS y no exponga directamente PostgreSQL.

El despliegue entregado usa Systems Manager en lugar de abrir SSH, exige IMDSv2, cifra EBS/RDS/S3, obtiene las credenciales desde Secrets Manager y deja RDS sin acceso público.

## Evidencias sugeridas

- Pantalla de inicio y CRUD funcionando.
- Tabla `users` en RDS.
- objetos bajo `profiles/` en S3.
- instancia EC2 y grupos de seguridad.
- `docker compose ps`, `/health` y URL HTTPS.
- política IAM del rol sin permisos globales.
