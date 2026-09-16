import os
from pathlib import Path
from typing import Final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = os.path.join(BASE_DIR, "core", "envs", ".env")
MAX_PORT_NUMBER: Final = 65535


class Settings(BaseSettings):
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = Field(default=8000, gt=0, le=MAX_PORT_NUMBER)

    POSTGRES_HOST: str = "signature-auth-db"
    POSTGRES_PORT: int = Field(default=5432, gt=0, le=MAX_PORT_NUMBER)
    POSTGRES_USER: str = "db_user"
    POSTGRES_PASSWORD: str = "db_pass"
    POSTGRES_DB: str = "db_name"

    @property
    def postgres_dsn(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    model_config = SettingsConfigDict(env_file=ENV_PATH, env_file_encoding="utf-8")


settings: Final = Settings()
