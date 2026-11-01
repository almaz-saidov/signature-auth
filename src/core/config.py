from pathlib import Path
from typing import ClassVar, Final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent
    ENV_PATH: ClassVar[Path] = BASE_DIR / "core" / "envs" / ".env"
    ALEMBIC_CONFIG_PATH: ClassVar[Path] = BASE_DIR / "alembic.ini"

    MAX_PORT_NUMBER: ClassVar[int] = 65535
    API_KEY_LENGTH_BYTES: ClassVar[int] = 32
    REFERENCE_SAMPLE_COUNT: ClassVar[int] = 10
    MIN_SIGNATURE_POINT_COUNT: ClassVar[int] = 2
    PAGINATION_DEFAULT_PAGE_SIZE: ClassVar[int] = 20
    PAGINATION_MAX_PAGE_SIZE: ClassVar[int] = 100

    TEST_MOCK_DATA_PATH: ClassVar[Path] = BASE_DIR / "tests" / "mock_data.sql"
    TEST_POSTGRES_IMAGE: ClassVar[str] = "postgres:18-alpine"
    TEST_POSTGRES_PASSWORD: ClassVar[str] = "test@password%with/special:characters"

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
