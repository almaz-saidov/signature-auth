# mypy: disable-error-code=empty-body
# Заглушки сохраняют возвращаемые типы будущей реализации.
from uuid import UUID

from database.repositories.base import BaseDatabaseRepository
from schemas.pagination import PaginatedSchema
from schemas.signature_reference import (
    ListSignatureReferenceFiltersSchema,
    SignatureReferenceSchema,
    SignatureReferenceRecordSchema,
)


class SignatureReferenceRepository(BaseDatabaseRepository):
    async def create(self, *, user_id: UUID, subject_id: str, data: bytes) -> UUID:
        pass

    async def get(
        self, *, user_id: UUID, reference_id: UUID
    ) -> SignatureReferenceRecordSchema | None:
        pass

    async def get_by_subject_id(
        self, *, user_id: UUID, subject_id: str
    ) -> SignatureReferenceRecordSchema | None:
        pass

    async def list(
        self, *, user_id: UUID, filters: ListSignatureReferenceFiltersSchema
    ) -> PaginatedSchema[SignatureReferenceSchema]:
        pass

    async def update(self, *, user_id: UUID, reference_id: UUID, data: bytes) -> UUID:
        pass

    async def delete(self, *, user_id: UUID, reference_id: UUID) -> bool:
        pass
