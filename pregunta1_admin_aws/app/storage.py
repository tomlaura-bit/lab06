import uuid
import boto3
from botocore.config import Config
from fastapi import HTTPException, UploadFile
from .config import settings

ALLOWED = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def client():
    return boto3.client("s3", region_name=settings.aws_region, config=Config(signature_version="s3v4"))


def upload_profile(file: UploadFile, user_id: int) -> str:
    if not settings.s3_bucket:
        raise HTTPException(503, "S3_BUCKET no está configurado")
    if file.content_type not in ALLOWED:
        raise HTTPException(415, "Solo se permiten JPEG, PNG o WebP")
    data = file.file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "La imagen excede el tamaño permitido")
    key = f"profiles/{user_id}/{uuid.uuid4().hex}{ALLOWED[file.content_type]}"
    client().put_object(Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=file.content_type, ServerSideEncryption="AES256")
    return key


def delete_object(key: str | None) -> None:
    if key and settings.s3_bucket:
        client().delete_object(Bucket=settings.s3_bucket, Key=key)


def image_url(key: str | None) -> str | None:
    if not key:
        return None
    if settings.s3_public_base_url:
        return f"{settings.s3_public_base_url.rstrip('/')}/{key}"
    return client().generate_presigned_url("get_object", Params={"Bucket": settings.s3_bucket, "Key": key}, ExpiresIn=900)
