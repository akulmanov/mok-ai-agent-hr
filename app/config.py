from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./data/hr_screening.db"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"  # or "gpt-4-turbo" or "gpt-3.5-turbo"
    
    # Scoring
    scoring_threshold: float = 0.65
    scoring_hold_band: float = 0.10
    
    # Logging
    log_level: str = "INFO"
    
    # File storage
    upload_dir: str = "./uploads"
    data_dir: str = "./data"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
