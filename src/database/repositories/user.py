# mypy: disable-error-code=empty-body
# Заглушки сохраняют возвращаемые типы будущей реализации.
from datetime import datetime
from uuid import UUID

from database.repositories.base import BaseDatabaseRepository
from schemas.user import UserSchema


class UserRepository(BaseDatabaseRepository):
    async def create(self, *, username: str, api_key_hash: str) -> UserSchema:
        pass

    async def get_by_username(self, *, username: str) -> UserSchema | None:
        pass

    async def get_by_api_key_hash(self, *, api_key_hash: str) -> UserSchema | None:
        pass

    async def update_api_key(
        self, *, user_id: UUID, api_key_hash: str, api_key_created_at: datetime
    ) -> UserSchema:
        pass
