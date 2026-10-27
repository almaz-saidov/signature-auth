from uuid import UUID

from core.exceptions.http import NotImplementedHTTPException, UnauthorizedException
from schemas.user import (
    ApiKeySchema,
    CreateUserPayloadSchema,
    RegisteredUserSchema,
    UserSchema,
)
from services.database import DatabaseService


class UserService(DatabaseService):
    async def register(
        self, *, payload: CreateUserPayloadSchema
    ) -> RegisteredUserSchema:
        raise NotImplementedHTTPException(
            detail="Регистрация пользователя пока не реализована."
        )

    async def rotate_api_key(self, *, user_id: UUID) -> ApiKeySchema:
        raise NotImplementedHTTPException(
            detail="Перевыпуск API-ключа пока не реализован."
        )

    async def authenticate(self, *, api_key: str | None) -> UserSchema:
        if not api_key:
            raise UnauthorizedException()

        raise NotImplementedHTTPException(
            detail="Проверка API-ключа пока не реализована."
        )
