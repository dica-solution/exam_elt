from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    database_url: Optional[str]
    db_id_mapping: Optional[str]
    db_destination: Optional[str]
    api_authentication_token: Optional[str]
    api_get_by_exam_id: Optional[str]
    api_get_by_page: Optional[str]
    access_key: Optional[str]
    api_course_list: Optional[str]
    api_course_detail: Optional[str]
    api_lecture_detail: Optional[str]
    api_type_of_maths_detail: Optional[str]
    import_course_log_dir: Optional[str]

    # model_config = SettingsConfigDict(env_file=".env.dev", env_file_encoding='utf=8', extra='ignore')
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'


def get_settings(env_file: str='./.env.dev') -> Settings:
    return Settings(_env_file=env_file)