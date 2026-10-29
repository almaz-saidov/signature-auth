from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.community.postgres import PostgresContainer

from core.config import Settings
from database.session import get_db_session
from tests.utils import run_migrations, load_mock_data


@pytest.fixture(scope="session")
def test_db_url() -> Iterator[URL]:
    with PostgresContainer(
        Settings.TEST_POSTGRES_IMAGE,
        username="test",
        password=Settings.TEST_POSTGRES_PASSWORD,
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
        load_mock_data(test_database_url)

        yield test_database_url


@pytest.fixture
async def test_db_engine(test_db_url: URL) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(test_db_url, echo=False)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def db_connection(test_db_engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    async with test_db_engine.connect() as connection:
        transaction = await connection.begin()

        try:
            yield connection
        finally:
            await transaction.rollback()


@pytest.fixture
def db_session_factory(
    db_connection: AsyncConnection,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=db_connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )


@pytest.fixture
def test_app() -> FastAPI:
    from main import app

    return app


@pytest.fixture
async def db_session(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with db_session_factory() as session:
        yield session


@pytest.fixture
async def async_client(
    test_app: FastAPI,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        async with db_session_factory() as session:
            yield session

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
