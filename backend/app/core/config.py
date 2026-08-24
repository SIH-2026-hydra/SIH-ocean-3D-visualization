from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env files."""

    app_name: str = 'Ocean Intelligence API'
    app_env: str = 'development'
    api_v1_prefix: str = '/api/v1'
    host: str = '127.0.0.1'
    port: int = 8000
    frontend_origin: str = 'http://localhost:5173'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )


settings = Settings()
