from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimension: int = 384
    top_k: int = 6
    chunk_size: int = 1200
    chunk_overlap: int = 180
    generator_provider: str = "ollama"
    aws_region: str = "us-east-2"
    bedrock_model: str = "us.amazon.nova-lite-v1:0"
    bedrock_max_tokens: int = 800
    ollama_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.2:3b"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    max_pdf_pages: int = 300
    max_total_pages: int = 900
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
