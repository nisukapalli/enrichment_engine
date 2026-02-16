from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings. Load from env or .env file."""

    API_KEY: str
    URL: str = "https://api.sixtyfour.ai"

    @field_validator('API_KEY')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v:
            raise ValueError("API_KEY is required")
        return v

    # CORS for React dev server
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
