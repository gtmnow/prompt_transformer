from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./prompt_transformer.db"
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8000
    enable_request_logging: bool = False
    railway_auto_migrate: bool = True
    railway_seed_on_start: bool = False
    host: str = "0.0.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
