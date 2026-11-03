from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database.repositories.signature_reference import SignatureReferenceRepository
from database.repositories.user import UserRepository
from database.session import get_db_session
from schemas.user import UserSchema
from services.api_key import ApiKeyService
from services.authentication import AuthenticationService
from services.encryption import EncryptionService
from services.signature_feature import SignatureFeatureService
from services.signature_normalization import SignatureNormalizationService
from services.signature_reference import SignatureReferenceService
from services.user import UserService


async def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session=session)


async def get_signature_reference_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SignatureReferenceRepository:
    return SignatureReferenceRepository(session=session)


async def get_api_key_service() -> ApiKeyService:
    return ApiKeyService()


async def get_signature_normalization_service() -> SignatureNormalizationService:
    return SignatureNormalizationService()


async def get_signature_feature_service() -> SignatureFeatureService:
    return SignatureFeatureService()


async def get_encryption_service() -> EncryptionService:
    return EncryptionService(key=bytes.fromhex(settings.SECRET_KEY.get_secret_value()))


async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
    session: AsyncSession = Depends(get_db_session),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> UserService:
    return UserService(
        repository=repository, session=session, api_key_service=api_key_service
    )


async def get_signature_reference_service(
    repository: SignatureReferenceRepository = Depends(
        get_signature_reference_repository
    ),
    session: AsyncSession = Depends(get_db_session),
    normalization_service: SignatureNormalizationService = Depends(
        get_signature_normalization_service
    ),
    feature_service: SignatureFeatureService = Depends(get_signature_feature_service),
    encryption_service: EncryptionService = Depends(get_encryption_service),
) -> SignatureReferenceService:
    return SignatureReferenceService(
        repository=repository,
        session=session,
        normalization_service=normalization_service,
        feature_service=feature_service,
        encryption_service=encryption_service,
    )


async def get_authentication_service(
    user_service: UserService = Depends(get_user_service),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> AuthenticationService:
    return AuthenticationService(
        user_service=user_service, api_key_service=api_key_service
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(
            auto_error=False,
            scheme_name="ApiKey",
            description="API-ключ пользователя сервиса",
        )
    ),
    service: AuthenticationService = Depends(get_authentication_service),
) -> UserSchema:
    api_key = credentials.credentials if credentials is not None else None

    return await service.authenticate(api_key=api_key)
