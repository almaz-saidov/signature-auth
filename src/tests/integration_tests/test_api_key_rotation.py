from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UserModel


async def test_rotate_api_key_persists_new_key_for_registered_user(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    registration_response = await async_client.post(
        "/api/v1/users", json={"username": "new_key_rotation_integrator"}
    )

    assert registration_response.status_code == status.HTTP_201_CREATED, (
        "Ожидалось успешное создание пользователя с выдачей API-ключа"
    )
    registered_user = registration_response.json()
    initial_api_key = registered_user["api_key"]
    rotation_response = await async_client.post(
        "/api/v1/users/me/api-key",
        headers={"Authorization": f"Bearer {initial_api_key}"},
    )

    assert rotation_response.status_code == status.HTTP_200_OK, (
        "Ожидалось успешное выполнение ротации с ключом, выданным при регистрации"
    )
    rotated_key = rotation_response.json()

    assert rotated_key["api_key"] != initial_api_key, (
        "Ожидалось получение нового ключа вместо выданного при регистрации"
    )
    user = await db_session.get(UserModel, UUID(registered_user["id"]))

    assert user is not None, "Ожидалось сохранение зарегистрированного пользователя"
    assert (
        user.api_key_hash == sha256(rotated_key["api_key"].encode("utf-8")).hexdigest()
    ), "Ожидалось сохранение хеша нового ключа у зарегистрированного пользователя"
    assert user.api_key_created_at == datetime.fromisoformat(
        rotated_key["api_key_created_at"]
    ), "Ожидалось совпадение даты выдачи нового ключа в ответе и базе данных"


@pytest.mark.parametrize(
    "username", ["test_integrator", "test_integrator_other", "test_integrator_many"]
)
async def test_rotate_api_key_updates_only_current_users_key_and_dates(
    async_client: AsyncClient,
    db_session: AsyncSession,
    user_api_keys: dict[str, str],
    username: str,
) -> None:
    users_query = select(UserModel.__table__).order_by(UserModel.id)
    initial_users = {
        user["username"]: dict(user)
        for user in (await db_session.execute(users_query)).mappings()
    }
    api_key = user_api_keys[username]
    started_at = datetime.now(UTC)
    response = await async_client.post(
        "/api/v1/users/me/api-key", headers={"Authorization": f"Bearer {api_key}"}
    )
    finished_at = datetime.now(UTC)

    assert response.status_code == status.HTTP_200_OK, (
        "Ожидалось успешное выполнение ротации текущего пользователя"
    )
    payload = response.json()
    saved_users = {
        user["username"]: dict(user)
        for user in (await db_session.execute(users_query)).mappings()
    }
    expected_user = {
        **initial_users[username],
        "api_key_hash": sha256(payload["api_key"].encode("utf-8")).hexdigest(),
        "api_key_created_at": datetime.fromisoformat(payload["api_key_created_at"]),
        "updated_at": saved_users[username]["updated_at"],
    }

    assert saved_users == {**initial_users, username: expected_user}, (
        "Ожидалось изменение только хеша ключа и дат текущего пользователя"
    )
    assert (
        saved_users[username]["api_key_hash"] != initial_users[username]["api_key_hash"]
    ), "Ожидалось обновление хеша прежнего API-ключа"

    for field in ("api_key_created_at", "updated_at"):
        assert started_at <= saved_users[username][field] <= finished_at, (
            f"Ожидалось обновление даты {field} во время ротации"
        )


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="missing_authorization"),
        pytest.param({"Authorization": "Bearer unknown_api_key"}, id="unknown_key"),
    ],
)
async def test_rotate_api_key_preserves_database_for_invalid_authorization(
    async_client: AsyncClient, db_session: AsyncSession, headers: dict[str, str]
) -> None:
    users_query = select(UserModel.__table__).order_by(UserModel.id)
    initial_users = (await db_session.execute(users_query)).mappings().all()
    response = await async_client.post("/api/v1/users/me/api-key", headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
        "Ожидалось отклонение ротации без действующего API-ключа"
    )
    saved_users = (await db_session.execute(users_query)).mappings().all()

    assert saved_users == initial_users, (
        "Ожидалось отсутствие изменений в базе данных после отказа в авторизации"
    )


async def test_rotate_api_key_preserves_database_for_inactive_user(
    async_client: AsyncClient,
    db_session: AsyncSession,
    user_api_keys: dict[str, str],
) -> None:
    users_query = select(UserModel.__table__).order_by(UserModel.id)
    initial_users = (await db_session.execute(users_query)).mappings().all()

    assert any(
        user["username"] == "test_integrator_inactive" and user["is_active"] is False
        for user in initial_users
    ), "Ожидалось наличие отключённого пользователя в исходных данных"

    api_key = user_api_keys["test_integrator_inactive"]
    response = await async_client.post(
        "/api/v1/users/me/api-key", headers={"Authorization": f"Bearer {api_key}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN, (
        "Ожидалось получение статуса 403 для test_integrator_inactive"
    )
    saved_users = (await db_session.execute(users_query)).mappings().all()

    assert saved_users == initial_users, (
        "Ожидалось сохранение прежнего ключа, статуса и дат отключённого пользователя"
    )


async def test_rotate_api_key_preserves_new_key_for_revoked_credentials(
    async_client: AsyncClient,
    db_session: AsyncSession,
    user_api_keys: dict[str, str],
) -> None:
    api_key = user_api_keys["test_integrator"]
    old_headers = {"Authorization": f"Bearer {api_key}"}
    response = await async_client.post("/api/v1/users/me/api-key", headers=old_headers)

    assert response.status_code == status.HTTP_200_OK, (
        "Ожидалось успешное выполнение ротации для отзыва прежнего ключа"
    )
    users_query = select(UserModel.__table__).order_by(UserModel.id)
    rotated_users = (await db_session.execute(users_query)).mappings().all()
    rejected_response = await async_client.post(
        "/api/v1/users/me/api-key", headers=old_headers
    )

    assert rejected_response.status_code == status.HTTP_401_UNAUTHORIZED, (
        "Ожидалось отклонение повторной ротации с отозванным ключом"
    )
    saved_users = (await db_session.execute(users_query)).mappings().all()

    assert saved_users == rotated_users, (
        "Ожидалось сохранение нового ключа и остальных данных после отказа"
    )
