from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UserModel


async def test_register_user_persists_user_and_key_hash_for_valid_payload(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    count_query = select(func.count()).select_from(UserModel)
    initial_count = (await db_session.execute(count_query)).scalar_one()
    started_at = datetime.now(UTC)
    response = await async_client.post(
        "/api/v1/users", json={"username": "persisted_integrator"}
    )
    finished_at = datetime.now(UTC)

    assert response.status_code == status.HTTP_201_CREATED, (
        "Ожидалось успешное создание пользователя"
    )
    payload = response.json()
    user = await db_session.get(UserModel, UUID(payload["id"]))

    assert user is not None, "Ожидалось сохранение пользователя в базе данных"
    assert user.username == payload["username"] == "persisted_integrator", (
        "Ожидалось совпадение имени в запросе, ответе и базе данных"
    )
    assert user.is_active is True, "Ожидалось сохранение активного пользователя"
    assert (
        user.api_key_hash == sha256(payload["api_key"].encode("utf-8")).hexdigest()
    ), "Ожидалось сохранение SHA-256 выданного API-ключа"
    assert user.api_key_hash != payload["api_key"], (
        "Ожидалось хранение хеша вместо открытого API-ключа"
    )

    for field in ("created_at", "updated_at", "api_key_created_at"):
        timestamp = getattr(user, field)

        assert timestamp == datetime.fromisoformat(payload[field]), (
            f"Ожидалось совпадение даты {field} в ответе и базе данных"
        )
        assert started_at <= timestamp <= finished_at, (
            f"Ожидалось заполнение даты {field} во время регистрации"
        )

    saved_count = (await db_session.execute(count_query)).scalar_one()

    assert saved_count == initial_count + 1, (
        "Ожидалось добавление ровно одного пользователя"
    )


@pytest.mark.parametrize(
    ("username", "is_active"),
    [
        pytest.param("test_integrator", True, id="active"),
        pytest.param("test_integrator_inactive", False, id="inactive"),
    ],
)
async def test_register_user_preserves_existing_data_for_duplicate_username(
    async_client: AsyncClient,
    db_session: AsyncSession,
    username: str,
    is_active: bool,
) -> None:
    users_query = select(UserModel.__table__).order_by(UserModel.id)
    initial_users = (await db_session.execute(users_query)).mappings().all()

    assert any(
        user["username"] == username and user["is_active"] is is_active
        for user in initial_users
    ), "Ожидалось наличие исходного пользователя с заданным статусом активности"

    response = await async_client.post("/api/v1/users", json={"username": username})

    assert response.status_code == status.HTTP_409_CONFLICT, (
        "Ожидалось отклонение занятого имени независимо от активности пользователя"
    )
    saved_users = (await db_session.execute(users_query)).mappings().all()

    assert saved_users == initial_users, (
        "Ожидалось сохранение всех пользователей, их ключей, статусов и дат без изменений"
    )


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"username": ""}, id="empty_username"),
        pytest.param({"username": 123}, id="invalid_username_type"),
        pytest.param(
            {"username": "rejected_integrator", "is_active": False},
            id="unexpected_field",
        ),
    ],
)
async def test_register_user_preserves_database_for_invalid_payload(
    async_client: AsyncClient, db_session: AsyncSession, payload: dict[str, object]
) -> None:
    users_query = select(UserModel.__table__).order_by(UserModel.id)
    initial_users = (await db_session.execute(users_query)).mappings().all()
    response = await async_client.post("/api/v1/users", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, (
        "Ожидалось отклонение некорректных данных регистрации"
    )
    saved_users = (await db_session.execute(users_query)).mappings().all()

    assert saved_users == initial_users, (
        "Ожидалось отсутствие изменений в базе данных после ошибки валидации"
    )
