from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    database_url: Optional[str]
    db_id_mapping: Optional[str]
    db_destination: Optional[str]
    api_authentication_token: Optional[str]
    api_get_by_exam_id: Optional[str]
    api_get_by_page: Optional[str]

    model_config = SettingsConfigDict(env_file=".env.dev", env_file_encoding='utf=8', extra='ignore')


def get_settings() -> Settings:
    return Settings()


settings = get_settings()