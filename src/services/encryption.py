from secrets import token_bytes

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.config import application_settings
from core.exceptions.encryption import EncryptionException


class EncryptionService:
    def __init__(self, *, key: bytes) -> None:
        try:
            self._cipher = AESGCM(key)
        except Exception as error:
            raise EncryptionException() from error

    def encrypt(self, *, data: bytes) -> bytes:
        try:
            nonce = token_bytes(application_settings.ENCRYPTION_NONCE_LENGTH_BYTES)
            encrypted_data = self._cipher.encrypt(
                nonce=nonce, data=data, associated_data=None
            )
        except Exception as error:
            raise EncryptionException() from error

        return nonce + encrypted_data

    def decrypt(self, *, data: bytes) -> bytes:
        if len(data) < (
            application_settings.ENCRYPTION_NONCE_LENGTH_BYTES
            + application_settings.ENCRYPTION_TAG_LENGTH_BYTES
        ):
            raise EncryptionException()

        nonce = data[: application_settings.ENCRYPTION_NONCE_LENGTH_BYTES]
        encrypted_data = data[application_settings.ENCRYPTION_NONCE_LENGTH_BYTES :]

        try:
            return self._cipher.decrypt(
                nonce=nonce, data=encrypted_data, associated_data=None
            )
        except Exception as error:
            raise EncryptionException() from error
