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
    SIGNATURE_REFERENCE_VERSION: ClassVar[int] = 3
    SIGNATURE_PHASE_NAMES: ClassVar[tuple[str, ...]] = ("start", "middle", "end")
    MILLISECONDS_PER_SECOND: ClassVar[float] = 1000.0
    FULL_TURN_DEGREES: ClassVar[float] = 360.0
    CIRCULAR_MEAN_EPSILON: ClassVar[float] = 1e-12
    MIN_SIGNATURE_POINT_COUNT: ClassVar[int] = 2
    VERIFICATION_SCORE_MAX: ClassVar[float] = 100.0
    VERIFICATION_THRESHOLD: ClassVar[float] = 44.887893393784765
    VERIFICATION_WEIGHTS: ClassVar[dict[str, float]] = {
        "duration_ms": 0.06695575560380373,
        "trajectory_length": 0.007568917045878567,
        "maximum_speed": 0.07592229700775364,
        "rms_acceleration": 0.03131696198535675,
        "mean_altitude": 0.060107213412768076,
        "mean_azimuth": 0.0739785584463694,
        "shape_factor": 0.05034562384476233,
        "pen_lift_count": 0.025005825433159358,
        "contact_duration_ms": 0.046612966682284214,
        "pen_up_duration_ms": 0.047213121894756,
        "start_x": 0.054154605120882084,
        "start_y": 0.045277794766003236,
        "end_x": 0.04509507683944964,
        "end_y": 0.05595191105424617,
        "mean_speed_start": 0.05209846089511083,
        "mean_speed_middle": 0.06908957894731531,
        "mean_speed_end": 0.054646346968722004,
        "mean_pressure_start": 0.04808417585733531,
        "mean_pressure_middle": 0.02901276600437474,
        "mean_pressure_end": 0.06156157611896182,
    }


class TestSettings:
    MCYT_DATASET_PATH: ClassVar[Path] = (
        ApplicationSettings.BASE_DIR.parent / "data" / "MCYT_Signature_100"
    )
    MCYT_REPORT_DIRECTORY: ClassVar[Path] = (
        ApplicationSettings.BASE_DIR.parent / "data" / "mcyt_results"
    )
    MCYT_FPG_HEADER_FORMAT: ClassVar[str] = "<4sHHHHIH4xIIIHI"
    MCYT_FPG_POINT_FORMAT: ClassVar[str] = "<5f"
    MCYT_FPG_METADATA: ClassVar[tuple[bytes, int, int, int, int]] = (
        b"FPG ",
        4,
        1,
        32,
        5,
    )
    MCYT_AUTHOR_ID_LENGTH: ClassVar[int] = 4
    MCYT_MAX_PRESSURE: ClassVar[float] = 1023.0
    MCYT_HTTP_TIMEOUT_SECONDS: ClassVar[float] = 30.0
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
