from uuid import UUID

from core.exceptions.http import NotImplementedHTTPException
from schemas.pagination import PaginatedSchema
from schemas.signature_reference import (
    CreateSignatureReferencePayloadSchema,
    ListSignatureReferenceFiltersSchema,
    SignatureReferenceSchema,
    SignatureSampleSchema,
    SignatureValidationResultSchema,
)
from services.database import DatabaseService


class SignatureReferenceService(DatabaseService):
    async def create(
        self, *, user_id: UUID, payload: CreateSignatureReferencePayloadSchema
    ) -> tuple[UUID, bool]:
        raise NotImplementedHTTPException(
            detail="Создание и замена эталона пока не реализованы."
        )

    async def list(
        self, *, user_id: UUID, filters: ListSignatureReferenceFiltersSchema
    ) -> PaginatedSchema[SignatureReferenceSchema]:
        raise NotImplementedHTTPException(
            detail="Получение списка эталонов пока не реализовано."
        )

    async def get(
        self, *, user_id: UUID, reference_id: UUID
    ) -> SignatureReferenceSchema:
        raise NotImplementedHTTPException(
            detail="Получение метаданных эталона пока не реализовано."
        )

    async def delete(self, *, user_id: UUID, reference_id: UUID) -> None:
        raise NotImplementedHTTPException(
            detail="Удаление эталона пока не реализовано."
        )

    async def verify(
        self, *, user_id: UUID, reference_id: UUID, sample: SignatureSampleSchema
    ) -> SignatureValidationResultSchema:
        raise NotImplementedHTTPException(
            detail="Сравнение подписи с эталоном пока не реализовано."
        )
