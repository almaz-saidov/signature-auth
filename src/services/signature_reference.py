from uuid import UUID

from core.exceptions.database import DatabaseException
from core.exceptions.http import (
    NotImplementedHTTPException,
    SignatureReferenceNotFoundException,
)
from database.repositories.signature_reference import SignatureReferenceRepository
from schemas.pagination import PaginatedSchema
from schemas.signature_reference import (
    CreateSignatureReferencePayloadSchema,
    ListSignatureReferenceFiltersSchema,
    SignatureReferenceSchema,
    SignatureSampleSchema,
    SignatureValidationResultSchema,
)
from services.database import DatabaseService


class SignatureReferenceService(DatabaseService[SignatureReferenceRepository]):
    async def create(
        self, *, user_id: UUID, payload: CreateSignatureReferencePayloadSchema
    ) -> tuple[UUID, bool]:
        raise NotImplementedHTTPException(
            detail="Создание и замена эталона пока не реализованы."
        )

    async def get_list(
        self, *, user_id: UUID, filters: ListSignatureReferenceFiltersSchema
    ) -> PaginatedSchema[SignatureReferenceSchema]:
        return await self._repository.get_list(user_id=user_id, filters=filters)

    async def get(
        self, *, user_id: UUID, reference_id: UUID
    ) -> SignatureReferenceSchema:
        reference = await self._repository.get(
            user_id=user_id, reference_id=reference_id
        )

        if reference is None:
            raise SignatureReferenceNotFoundException()

        return reference

    async def delete(self, *, user_id: UUID, reference_id: UUID) -> None:
        try:
            deleted = await self._repository.delete(
                user_id=user_id, reference_id=reference_id
            )

            if not deleted:
                raise SignatureReferenceNotFoundException()

            await self._commit()
        except DatabaseException:
            await self._rollback()
            raise

    async def verify(
        self, *, user_id: UUID, reference_id: UUID, sample: SignatureSampleSchema
    ) -> SignatureValidationResultSchema:
        raise NotImplementedHTTPException(
            detail="Сравнение подписи с эталоном пока не реализовано."
        )
