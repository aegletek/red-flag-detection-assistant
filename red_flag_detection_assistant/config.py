from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class UseCaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Red Flag Detection Assistant"
    environment: str = "local"

    database_url: str = ""
    langfuse_base_url: str = "https://us.cloud.langfuse.com"
    ui_display_name: str = "Local administrator"
