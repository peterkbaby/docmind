from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    algorithm: str
    
    database_url: str
    
    aws_access_key_id: str
    aws_secret_access_key: str
    s3_bucket_name: str
    s3_region: str

    qdrant_url: str
    qdrant_api_key: str  
    qdrant_collection: str = "docmind_chunks"       
    llm_api_key: str

    llm_model: str = "gemini-3.6-flash"

    max_documents_per_user: int = 6



    cors_origins: str = "http://localhost:3000"
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int = 5

    max_pdf_size_mb: int = 50

    debug: bool = False

    
    class Config:
        env_file = ".env"

settings = Settings()