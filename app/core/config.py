from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    groq_api_key: str
    gemini_api_key: Optional[str] = None
    model_name: str = "llama-3.3-70b-versatile"
    database_url: str = "postgresql://hr_user:admin123@localhost:5432/hr_agent_db"
    chroma_db_path: str = "./chroma_db"
    max_tokens: int = 2048
    max_iterations: int = 10
    top_k_results: int = 3

settings = Settings()