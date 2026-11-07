from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions.database import DatabaseException
from core.exceptions.http import UsernameAlreadyExistsException
from database.repositories.user import UserRepository
from schemas.user import (
    APIKeySchema,
    CreateUserPayloadSchema,
    RegisteredUserSchema,
    UserSchema,
)
from services.api_key import APIKeyService
from services.database import DatabaseService


class UserService(DatabaseService[UserRepository]):
    def __init__(
        self,
        *,
        repository: UserRepository,
        session: AsyncSession,
        api_key_service: APIKeyService,
    ) -> None:
        super().__init__(repository=repository, session=session)
        self._api_key_service = api_key_service

    async def register(
        self, *, payload: CreateUserPayloadSchema
    ) -> RegisteredUserSchema:
        try:
            existing_user = await self._repository.get_by_username(
                username=payload.username
            )

            if existing_user:
                raise UsernameAlreadyExistsException()

            api_key = self._api_key_service.create_key()
            api_key_hash = self._api_key_service.get_key_hash(api_key=api_key)
            registered_user = await self._repository.create(
                data=payload, api_key_hash=api_key_hash
            )
            await self._commit()

            return RegisteredUserSchema(**registered_user.model_dump(), api_key=api_key)
        except DatabaseException:
            await self._rollback()
            raise

    async def get_by_api_key_hash(self, *, api_key_hash: str) -> UserSchema | None:
        return await self._repository.get_by_api_key_hash(api_key_hash=api_key_hash)

    async def rotate_api_key(self, *, user_id: UUID) -> APIKeySchema:
        try:
            api_key = self._api_key_service.create_key()
            api_key_hash = self._api_key_service.get_key_hash(api_key=api_key)
            updated_user = await self._repository.update_api_key(
                user_id=user_id,
                api_key_hash=api_key_hash,
            )

            await self._commit()

            return APIKeySchema(
                api_key=api_key, api_key_created_at=updated_user.api_key_created_at
            )
        except DatabaseException:
            await self._rollback()
            raise
