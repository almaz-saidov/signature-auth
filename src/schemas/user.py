from datetime import datetime
from uuid import UUID

from pydantic import Field

from schemas.base import BaseSchema


class CreateUserPayloadSchema(BaseSchema):
    username: str = Field(min_length=1)


class UserSchema(BaseSchema):
    id: UUID
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    api_key_created_at: datetime


class RegisteredUserSchema(UserSchema):
    api_key: str = Field(
        repr=False, description="Сохраните ключ: он выдаётся только один раз"
    )


class ApiKeySchema(BaseSchema):
    api_key: str = Field(
        repr=False, description="Сохраните новый ключ: прежний больше не действует"
    )
    api_key_created_at: datetime
