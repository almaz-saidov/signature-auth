from datetime import datetime, timedelta
from uuid import UUID

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.parametrize("username", ["new_integrator", "a", "интегратор"])
async def test_register_user_returns_201_and_api_key_for_valid_username(
    async_client: AsyncClient, username: str
) -> None:
    response = await async_client.post("/api/v1/users", json={"username": username})

    assert response.status_code == status.HTTP_201_CREATED, (
        "Ожидалось создание пользователя без предварительной авторизации"
    )
    payload = response.json()

    assert set(payload) == {
        "id",
        "username",
        "is_active",
        "created_at",
        "updated_at",
        "api_key_created_at",
        "api_key",
    }, "Ожидалось получение метаданных и API-ключа без хеша и лишних полей"
    assert payload["username"] == username, "Ожидалось сохранение переданного имени"
    assert payload["is_active"] is True, "Ожидалось создание активного пользователя"
    assert UUID(payload["id"]).version == 7, "Ожидалось получение UUID версии 7"
    assert isinstance(payload["api_key"], str) and payload["api_key"], (
        "Ожидалось получение непустого строкового API-ключа"
    )

    for field in ("created_at", "updated_at", "api_key_created_at"):
        timestamp = datetime.fromisoformat(payload[field])

        assert timestamp.utcoffset() == timedelta(0), (
            f"Ожидалось получение даты {field} в UTC"
        )


@pytest.mark.parametrize(
    "username",
    [
        pytest.param("test_integrator", id="active"),
        pytest.param("test_integrator_inactive", id="inactive"),
    ],
)
async def test_register_user_returns_409_for_existing_username(
    async_client: AsyncClient, username: str
) -> None:
    response = await async_client.post("/api/v1/users", json={"username": username})

    assert response.status_code == status.HTTP_409_CONFLICT, (
        "Ожидалось получение статуса 409 для занятого имени"
    )
    assert response.json() == {"detail": "Имя пользователя уже занято."}, (
        "Ожидалось сообщение о занятом имени без выдачи API-ключа"
    )


async def test_register_user_returns_409_for_repeated_registration(
    async_client: AsyncClient,
) -> None:
    payload = {"username": "repeated_integrator"}
    first_response = await async_client.post("/api/v1/users", json=payload)

    assert first_response.status_code == status.HTTP_201_CREATED, (
        "Ожидалось успешное выполнение первой регистрации"
    )
    repeated_response = await async_client.post("/api/v1/users", json=payload)

    assert repeated_response.status_code == status.HTTP_409_CONFLICT, (
        "Ожидалось получение статуса 409 при повторной регистрации"
    )
    assert repeated_response.json() == {"detail": "Имя пользователя уже занято."}, (
        "Ожидалось сообщение о занятом имени без повторной выдачи ключа"
    )


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="missing_username"),
        pytest.param({"username": ""}, id="empty_username"),
        pytest.param({"username": None}, id="null_username"),
        pytest.param({"username": 123}, id="integer_username"),
        pytest.param({"username": 1.5}, id="float_username"),
        pytest.param({"username": True}, id="boolean_username"),
        pytest.param({"username": []}, id="list_username"),
        pytest.param({"username": {}}, id="object_username"),
    ],
)
async def test_register_user_returns_422_for_invalid_username(
    async_client: AsyncClient, payload: dict[str, object]
) -> None:
    response = await async_client.post("/api/v1/users", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, (
        "Ожидалось получение статуса 422 для некорректного имени"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [("is_active", False), ("api_key", "client_supplied_key"), ("extra", "value")],
)
async def test_register_user_returns_422_for_unexpected_field(
    async_client: AsyncClient, field: str, value: object
) -> None:
    response = await async_client.post(
        "/api/v1/users", json={"username": "unexpected_field_integrator", field: value}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, (
        "Ожидалось отклонение не предусмотренного схемой поля"
    )


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(b"", id="missing_body"),
        pytest.param(b'{"username":', id="malformed_json"),
        pytest.param(b"[]", id="non_object_body"),
    ],
)
async def test_register_user_returns_422_for_invalid_request_body(
    async_client: AsyncClient, content: bytes
) -> None:
    response = await async_client.post(
        "/api/v1/users", content=content, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, (
        "Ожидалось получение статуса 422 для некорректного тела запроса"
    )


async def test_register_users_returns_distinct_credentials_for_different_usernames(
    async_client: AsyncClient,
) -> None:
    first_response = await async_client.post(
        "/api/v1/users", json={"username": "first_integrator"}
    )
    second_response = await async_client.post(
        "/api/v1/users", json={"username": "second_integrator"}
    )

    assert first_response.status_code == status.HTTP_201_CREATED, (
        "Ожидалось успешное создание первого пользователя"
    )
    assert second_response.status_code == status.HTTP_201_CREATED, (
        "Ожидалось успешное создание второго пользователя"
    )
    first_user = first_response.json()
    second_user = second_response.json()

    assert first_user["id"] != second_user["id"], (
        "Ожидалось получение разных идентификаторов пользователей"
    )
    assert first_user["api_key"] != second_user["api_key"], (
        "Ожидалось получение отдельного API-ключа для каждого пользователя"
    )
