from pathlib import Path
from typing import ClassVar, Final

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class ApplicationSettings(BaseSettings):
    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent
    ENV_PATH: ClassVar[Path] = BASE_DIR / "core" / "envs" / ".env"
    MAX_PORT_NUMBER: ClassVar[int] = 65535
    API_KEY_LENGTH_BYTES: ClassVar[int] = 32
    ENCRYPTION_NONCE_LENGTH_BYTES: ClassVar[int] = 12
    ENCRYPTION_TAG_LENGTH_BYTES: ClassVar[int] = 16
    PAGINATION_DEFAULT_PAGE_SIZE: ClassVar[int] = 20
    PAGINATION_MAX_PAGE_SIZE: ClassVar[int] = 100

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = Field(default=8000, gt=0, le=MAX_PORT_NUMBER)
    SECRET_KEY: SecretStr = Field(..., min_length=64, max_length=64)

    model_config = SettingsConfigDict(
        env_file=ENV_PATH, env_file_encoding="utf-8", extra="ignore"
    )


class DatabaseSettings(BaseSettings):
    ALEMBIC_CONFIG_PATH: ClassVar[Path] = ApplicationSettings.BASE_DIR / "alembic.ini"

    POSTGRES_HOST: str = "signature-auth-db"
    POSTGRES_PORT: int = Field(
        default=5432, gt=0, le=ApplicationSettings.MAX_PORT_NUMBER
    )
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

    model_config = SettingsConfigDict(
        env_file=ApplicationSettings.ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


class SignatureSettings:
    REFERENCE_SAMPLE_COUNT: ClassVar[int] = 10
    SIGNATURE_REFERENCE_VERSION: ClassVar[int] = 1
    MILLISECONDS_PER_SECOND: ClassVar[float] = 1000.0
    FULL_TURN_DEGREES: ClassVar[float] = 360.0
    CIRCULAR_MEAN_EPSILON: ClassVar[float] = 1e-12
    MIN_SIGNATURE_POINT_COUNT: ClassVar[int] = 2


class TestSettings:
    MOCK_DATA_PATH: ClassVar[Path] = (
        ApplicationSettings.BASE_DIR / "tests" / "mock_data.sql"
    )
    POSTGRES_IMAGE: ClassVar[str] = "postgres:18-alpine"
    POSTGRES_PASSWORD: ClassVar[str] = "test@password%with/special:characters"


# Обязательные настройки загружаются из окружения.
application_settings: Final = ApplicationSettings()  # type: ignore[call-arg]
database_settings: Final = DatabaseSettings()
signature_settings: Final = SignatureSettings()
test_settings: Final = TestSettings()
