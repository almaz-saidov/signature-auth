# mypy: disable-error-code=empty-body
# Заглушки сохраняют возвращаемые типы будущей реализации.
from datetime import UTC, datetime, time
from uuid import UUID

from sqlalchemy import delete, func, select

from database.models import SignatureReferenceModel
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
    ) -> SignatureReferenceSchema | None:
        query = select(
            SignatureReferenceModel.id,
            SignatureReferenceModel.subject_id,
            SignatureReferenceModel.created_at,
            SignatureReferenceModel.updated_at,
        ).where(
            SignatureReferenceModel.user_id == user_id,
            SignatureReferenceModel.id == reference_id,
        )
        result = await self._execute(query)
        reference = result.mappings().one_or_none()

        return (
            SignatureReferenceSchema.model_validate(reference)
            if reference is not None
            else None
        )

    async def get_by_subject_id(
        self, *, user_id: UUID, subject_id: str
    ) -> SignatureReferenceRecordSchema | None:
        pass

    async def get_list(
        self, *, user_id: UUID, filters: ListSignatureReferenceFiltersSchema
    ) -> PaginatedSchema[SignatureReferenceSchema]:
        query = select(
            SignatureReferenceModel.id,
            SignatureReferenceModel.subject_id,
            SignatureReferenceModel.created_at,
            SignatureReferenceModel.updated_at,
        ).where(SignatureReferenceModel.user_id == user_id)

        if filters.subject_id is not None:
            query = query.where(
                SignatureReferenceModel.subject_id == filters.subject_id
            )

        if filters.from_ is not None:
            query = query.where(
                SignatureReferenceModel.created_at
                >= datetime.combine(filters.from_, time.min, tzinfo=UTC)
            )

        if filters.to_ is not None:
            query = query.where(
                SignatureReferenceModel.created_at
                <= datetime.combine(filters.to_, time.max, tzinfo=UTC)
            )

        count_result = await self._execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()
        query = (
            query.order_by(
                SignatureReferenceModel.created_at.desc(),
                SignatureReferenceModel.id.desc(),
            )
            .limit(filters.size)
            .offset((filters.page - 1) * filters.size)
        )
        result = await self._execute(query)

        return PaginatedSchema[SignatureReferenceSchema](
            total=total,
            page=filters.page,
            size=filters.size,
            data=[
                SignatureReferenceSchema.model_validate(reference)
                for reference in result.mappings()
            ],
        )

    async def update(self, *, user_id: UUID, reference_id: UUID, data: bytes) -> UUID:
        pass

    async def delete(self, *, user_id: UUID, reference_id: UUID) -> bool:
        query = (
            delete(SignatureReferenceModel)
            .where(
                SignatureReferenceModel.user_id == user_id,
                SignatureReferenceModel.id == reference_id,
            )
            .returning(SignatureReferenceModel.id)
        )
        result = await self._execute(query)

        return result.scalar_one_or_none() is not None
