from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.signature_reference import SignatureReferenceRepository
from database.repositories.user import UserRepository
from database.session import get_db_session
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


async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository=repository)


async def get_signature_reference_service(
    repository: SignatureReferenceRepository = Depends(
        get_signature_reference_repository
    ),
) -> SignatureReferenceService:
    return SignatureReferenceService(repository=repository)
