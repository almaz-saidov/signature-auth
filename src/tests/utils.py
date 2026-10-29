from alembic import command
from alembic.config import Config
from sqlalchemy import URL, create_engine

from core.config import Settings


def run_migrations(database_url: URL) -> None:
    alembic_config = Config(str(Settings.ALEMBIC_CONFIG_PATH))
    alembic_config.attributes["database_url"] = database_url
    command.upgrade(alembic_config, "head")


def load_mock_data(database_url: URL) -> None:
    script = Settings.TEST_MOCK_DATA_PATH.read_text(encoding="utf-8")

    engine = create_engine(database_url.set(drivername="postgresql+psycopg2"))

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(script)
    finally:
        engine.dispose()
