from hashlib import sha256
from secrets import token_urlsafe

from core.config import Settings


class ApiKeyService:
    def create_key(self) -> str:
        return token_urlsafe(Settings.API_KEY_LENGTH_BYTES)

    def get_key_hash(self, api_key: str) -> str:
        return sha256(api_key.encode("utf-8")).hexdigest()
