from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int = 60
    admin_email: str = "admin@example.com"
    admin_password: str = "CambieEstaClave123!"
    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    s3_public_base_url: str = ""
    max_upload_mb: int = 5
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
