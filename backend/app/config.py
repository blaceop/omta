from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    llm_api_key: str = Field(default="")
    llm_base_url: str | None = Field(default=None)
    llm_model: str = Field(default="gpt-4.1-mini")
    llm_provider: str = Field(default="openai")
    database_url: str = Field(default="sqlite:///./app.db")
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://127.0.0.1:5173"])
    execution_step_transition_delay_ms: int = Field(default=600, ge=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
