from core.exceptions.http import InactiveUserException, UnauthorizedException
from schemas.user import UserSchema
from services.api_key import ApiKeyService
from services.user import UserService


class AuthenticationService:
    def __init__(
        self, user_service: UserService, api_key_service: ApiKeyService
    ) -> None:
        self._user_service = user_service
        self._api_key_service = api_key_service

    async def authenticate(self, *, api_key: str | None) -> UserSchema:
        if not api_key:
            raise UnauthorizedException()

        api_key_hash = self._api_key_service.get_key_hash(api_key)
        user = await self._user_service.get_by_api_key_hash(api_key_hash=api_key_hash)

        if user is None:
            raise UnauthorizedException()

        if not user.is_active:
            raise InactiveUserException()

        return user
