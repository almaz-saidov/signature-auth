from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import URL, MetaData
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.community.postgres import PostgresContainer

from core.config import Settings
from database.session import get_db_session

TEST_POSTGRES_IMAGE = "postgres:18-alpine"
TEST_POSTGRES_PASSWORD = "test@password%with/special:characters"
ALEMBIC_CONFIG_PATH = Path(__file__).resolve().parents[1] / "alembic.ini"


def run_migrations(database_url: URL) -> None:
    alembic_config = Config(str(ALEMBIC_CONFIG_PATH))
    alembic_config.attributes["database_url"] = database_url
    command.upgrade(alembic_config, "head")


@pytest.fixture(scope="session")
def test_db_url() -> Iterator[URL]:
    with PostgresContainer(
        TEST_POSTGRES_IMAGE,
        username="test",
        password=TEST_POSTGRES_PASSWORD,
        dbname="test",
        driver="asyncpg",
    ) as postgres:
        test_settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            POSTGRES_HOST=postgres.get_container_host_ip(),
            POSTGRES_PORT=int(postgres.get_exposed_port(postgres.port)),
            POSTGRES_USER=postgres.username,
            POSTGRES_PASSWORD=postgres.password,
            POSTGRES_DB=postgres.dbname,
        )
        test_database_url = test_settings.postgres_dsn
        run_migrations(test_database_url)

        yield test_database_url


@pytest_asyncio.fixture
async def test_db_engine(test_db_url: URL) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(test_db_url, echo=False)

    try:
        yield engine
    finally:
        try:
            async with engine.begin() as connection:
                metadata = MetaData()
                await connection.run_sync(metadata.reflect)
                for table in reversed(metadata.sorted_tables):
                    if table.name != "alembic_version":
                        await connection.execute(table.delete())
        finally:
            await engine.dispose()


@pytest.fixture
def test_app() -> FastAPI:
    from main import app

    return app


@pytest_asyncio.fixture
async def db_session(test_db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async_session = async_sessionmaker(test_db_engine, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(
    test_app: FastAPI,
    test_db_engine: AsyncEngine,
) -> AsyncIterator[AsyncClient]:
    async_session = async_sessionmaker(test_db_engine, expire_on_commit=False)

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except SQLAlchemyError:
                await session.rollback()
                raise

    original_overrides = dict(test_app.dependency_overrides)
    test_app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        transport = ASGITransport(app=test_app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            yield client
    finally:
        test_app.dependency_overrides.clear()
        test_app.dependency_overrides.update(original_overrides)
