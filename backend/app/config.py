from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings. Load from env or .env file."""

    API_KEY: str = ""
    URL: str = "https://api.sixtyfour.ai"

    # CORS for React dev server
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
