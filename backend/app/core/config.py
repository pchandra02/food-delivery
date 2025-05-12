from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings."""
    OPENAI_API_KEY: Optional[str] = None
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Food Delivery AI Support Chatbot"
    
    # Security
    SECRET_KEY: str = "development-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # AI Model Settings
    MODEL_PATH: str = "models/"
    CONFIDENCE_THRESHOLD: float = 0.7
    
    # Storage Settings
    STORAGE_DIR: str = "storage"
    
    # Language Settings
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: list = ["en", "ar"]
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png"}
    
    # Azure Storage Settings
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    AZURE_STORAGE_CONTAINER_NAME: str = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "food-delivery-images")
    
    # Google Cloud Vision Settings
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 