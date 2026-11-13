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
    SIGNATURE_REFERENCE_VERSION: ClassVar[int] = 5
    SIGNATURE_PHASE_NAMES: ClassVar[tuple[str, ...]] = ("start", "middle", "end")
    CIRCULAR_FEATURE_NAMES: ClassVar[tuple[str, ...]] = (
        "mean_azimuth_start",
        "mean_azimuth_middle",
        "mean_azimuth_end",
    )
    DIRECTION_SECTOR_COUNT: ClassVar[int] = 8
    MILLISECONDS_PER_SECOND: ClassVar[float] = 1000.0
    FULL_TURN_DEGREES: ClassVar[float] = 360.0
    CIRCULAR_MEAN_EPSILON: ClassVar[float] = 1e-12
    MIN_SIGNATURE_POINT_COUNT: ClassVar[int] = 2
    VERIFICATION_SCORE_MAX: ClassVar[float] = 100.0
    VERIFICATION_THRESHOLD: ClassVar[float] = 47.03550793052496
    VERIFICATION_WEIGHTS: ClassVar[dict[str, float]] = {
        "duration_ms": 0.0493652085071491,
        "trajectory_length": 0.0002899811115012122,
        "maximum_speed": 0.044553680230785556,
        "rms_acceleration": 0.03378800617590821,
        "shape_factor": 0.0440368011300406,
        "pen_lift_count": 0.004868247366028559,
        "contact_duration_ms": 0.03963381244599419,
        "pen_up_duration_ms": 0.0006779351455091557,
        "start_x": 0.03821694388134867,
        "start_y": 0.01765275392126188,
        "end_x": 0.03689980936092488,
        "end_y": 0.013770118474329188,
        "mean_speed_start": 0.02095956243904895,
        "mean_speed_middle": 0.047129509995783324,
        "mean_speed_end": 0.04384192288509061,
        "mean_pressure_start": 0.03182909473510577,
        "mean_pressure_middle": 0.0252787425370073,
        "mean_pressure_end": 0.055373407001261345,
        "mean_azimuth_start": 0.04115570261983042,
        "mean_azimuth_middle": 0.03078776627421228,
        "mean_azimuth_end": 0.0010286827371067174,
        "mean_altitude_start": 0.012130876957245063,
        "mean_altitude_middle": 0.005463603085060648,
        "mean_altitude_end": 0.013674894735902015,
        "maximum_speed_time_ratio": 0.03476670939183648,
        "maximum_pause_duration_ms": 0.04753299475836279,
        "direction_length_ratio_0": 0.029690890554525253,
        "direction_length_ratio_45": 0.02257569875793534,
        "direction_length_ratio_90": 0.019811347035064132,
        "direction_length_ratio_135": 0.03788827719314217,
        "direction_length_ratio_180": 0.0038915049227251585,
        "direction_length_ratio_225": 0.010408610618086728,
        "direction_length_ratio_270": 0.02485546593420622,
        "direction_length_ratio_315": 0.030878250419025408,
        "total_turning_angle_degrees": 0.027809904853466325,
        "pressure_speed_correlation": 0.057483281808188465,
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
