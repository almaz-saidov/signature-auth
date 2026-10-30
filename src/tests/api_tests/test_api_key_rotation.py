from datetime import datetime, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient


async def test_rotate_api_key_returns_200_and_new_key_for_active_user(
    async_client: AsyncClient, user_api_keys: dict[str, str]
) -> None:
    api_key = user_api_keys["test_integrator"]
    response = await async_client.post(
        "/api/v1/users/me/api-key", headers={"Authorization": f"Bearer {api_key}"}
    )

    assert response.status_code == status.HTTP_200_OK, (
        "Ожидалось успешное выполнение ротации без тела запроса"
    )
    payload = response.json()

    assert set(payload) == {"api_key", "api_key_created_at"}, (
        "Ожидалось получение только нового API-ключа и времени его выдачи"
    )
    assert isinstance(payload["api_key"], str) and payload["api_key"], (
        "Ожидалось получение непустого строкового API-ключа"
    )
    assert payload["api_key"] != api_key, "Ожидалось получение нового API-ключа"
    timestamp = datetime.fromisoformat(payload["api_key_created_at"])

    assert timestamp.utcoffset() == timedelta(0), (
        "Ожидалось получение времени выдачи ключа в UTC"
    )


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="missing_authorization"),
        pytest.param({"Authorization": ""}, id="empty_authorization"),
        pytest.param({"Authorization": "Bearer"}, id="missing_bearer_key"),
        pytest.param({"Authorization": "Bearer unknown_api_key"}, id="unknown_key"),
    ],
)
async def test_rotate_api_key_returns_401_for_invalid_authorization(
    async_client: AsyncClient, headers: dict[str, str]
) -> None:
    response = await async_client.post("/api/v1/users/me/api-key", headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
        "Ожидалось получение статуса 401 без действующего API-ключа"
    )
    assert response.headers.get("WWW-Authenticate") == "Bearer", (
        "Ожидалось указание схемы Bearer в ответе об отсутствии авторизации"
    )


async def test_rotate_api_key_returns_401_for_non_bearer_scheme(
    async_client: AsyncClient, user_api_keys: dict[str, str]
) -> None:
    api_key = user_api_keys["test_integrator"]
    response = await async_client.post(
        "/api/v1/users/me/api-key", headers={"Authorization": f"Basic {api_key}"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
        "Ожидалось отклонение действующего ключа, переданного без схемы Bearer"
    )


async def test_rotate_api_key_returns_403_for_inactive_user(
    async_client: AsyncClient, user_api_keys: dict[str, str]
) -> None:
    api_key = user_api_keys["test_integrator_inactive"]
    response = await async_client.post(
        "/api/v1/users/me/api-key", headers={"Authorization": f"Bearer {api_key}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN, (
        "Ожидалось получение статуса 403 для test_integrator_inactive"
    )
    assert response.json() == {"detail": "Пользователь сервиса отключён."}, (
        "Ожидалось сообщение об отключённом пользователе без выдачи нового ключа"
    )


async def test_rotate_api_key_revokes_old_key_and_accepts_new_key(
    async_client: AsyncClient, user_api_keys: dict[str, str]
) -> None:
    api_key = user_api_keys["test_integrator"]
    old_headers = {"Authorization": f"Bearer {api_key}"}
    response = await async_client.post("/api/v1/users/me/api-key", headers=old_headers)

    assert response.status_code == status.HTTP_200_OK, (
        "Ожидалось успешное выполнение первой ротации"
    )
    new_api_key = response.json()["api_key"]
    old_key_response = await async_client.post(
        "/api/v1/users/me/api-key", headers=old_headers
    )

    assert old_key_response.status_code == status.HTTP_401_UNAUTHORIZED, (
        "Ожидалось прекращение действия старого API-ключа сразу после ротации"
    )
    new_key_response = await async_client.post(
        "/api/v1/users/me/api-key", headers={"Authorization": f"Bearer {new_api_key}"}
    )

    assert new_key_response.status_code == status.HTTP_200_OK, (
        "Ожидалось успешное выполнение повторной ротации с новым ключом"
    )
    assert new_key_response.json()["api_key"] not in {api_key, new_api_key}, (
        "Ожидалось получение очередного нового ключа при повторной ротации"
    )
