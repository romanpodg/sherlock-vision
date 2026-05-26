import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # VK Settings
    vk_token: str
    vk_group_id: int
    
    # Yandex Settings
    yandex_api_key: str
    yandex_folder_id: str
    
    # Database Settings
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str
    
    # App Settings
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
