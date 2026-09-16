import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthcheck_returns_204_with_empty_body(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/api/healthcheck")

    assert response.status_code == status.HTTP_204_NO_CONTENT, (
        "Ожидался статус 204 для работающего приложения"
    )
    assert response.content == b"", "Ожидалось пустое тело ответа проверки состояния"
