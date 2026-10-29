from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import insert, select, update

from database.models import UserModel
from database.repositories.base import BaseDatabaseRepository
from schemas.user import CreateUserPayloadSchema, UserSchema


class UserRepository(BaseDatabaseRepository):
    async def create(
        self, *, data: CreateUserPayloadSchema, api_key_hash: str
    ) -> UserSchema:
        query = (
            insert(UserModel)
            .values(**data.model_dump(), api_key_hash=api_key_hash)
            .returning(UserModel)
        )
        result = await self._execute(query)
        user = result.scalar_one()

        return UserSchema.model_validate(user)

    async def get_by_username(self, *, username: str) -> UserSchema | None:
        query = select(UserModel).where(UserModel.username == username)
        result = await self._execute(query)
        user = result.scalar_one_or_none()

        return UserSchema.model_validate(user) if user else None

    async def get_by_api_key_hash(self, *, api_key_hash: str) -> UserSchema | None:
        query = select(UserModel).where(UserModel.api_key_hash == api_key_hash)
        result = await self._execute(query)
        user = result.scalar_one_or_none()

        return UserSchema.model_validate(user) if user else None

    async def update_api_key(
        self, *, user_id: UUID, api_key_hash: str
    ) -> UserSchema | None:
        query = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(api_key_hash=api_key_hash, api_key_created_at=datetime.now(UTC))
            .returning(UserModel)
        )
        result = await self._execute(query)
        user = result.scalar_one_or_none()

        return UserSchema.model_validate(user) if user else None
