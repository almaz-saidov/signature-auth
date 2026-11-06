from datetime import UTC, datetime, time
from uuid import UUID

from sqlalchemy import ColumnElement, delete, func, insert, select, update

from database.models import SignatureReferenceModel
from database.repositories.base import BaseDatabaseRepository
from schemas.pagination import PaginatedSchema
from schemas.signature_reference import (
    ListSignatureReferenceFiltersSchema,
    SignatureReferenceRecordSchema,
    SignatureReferenceSchema,
)


class SignatureReferenceRepository(BaseDatabaseRepository):
    async def create(self, *, user_id: UUID, subject_id: str, data: bytes) -> UUID:
        query = (
            insert(SignatureReferenceModel)
            .values(user_id=user_id, subject_id=subject_id, data=data)
            .returning(SignatureReferenceModel.id)
        )
        result = await self._execute(statement=query)

        return result.scalar_one()

    async def update(
        self, *, user_id: UUID, reference_id: UUID, data: bytes
    ) -> UUID | None:
        query = (
            update(SignatureReferenceModel)
            .where(
                SignatureReferenceModel.user_id == user_id,
                SignatureReferenceModel.id == reference_id,
            )
            .values(data=data)
            .returning(SignatureReferenceModel.id)
        )
        result = await self._execute(statement=query)

        return result.scalar_one_or_none()

    async def get_by_id(
        self, *, user_id: UUID, reference_id: UUID
    ) -> SignatureReferenceSchema | None:
        return await self._get_one(
            user_id=user_id,
            condition=SignatureReferenceModel.id == reference_id,
        )

    async def get_record_by_id(
        self, *, user_id: UUID, reference_id: UUID
    ) -> SignatureReferenceRecordSchema | None:
        query = select(SignatureReferenceModel).where(
            SignatureReferenceModel.user_id == user_id,
            SignatureReferenceModel.id == reference_id,
        )
        result = await self._execute(statement=query)
        reference = result.scalar_one_or_none()

        return (
            SignatureReferenceRecordSchema.model_validate(reference)
            if reference is not None
            else None
        )

    async def get_by_subject_id(
        self, *, user_id: UUID, subject_id: str
    ) -> SignatureReferenceSchema | None:
        return await self._get_one(
            user_id=user_id,
            condition=SignatureReferenceModel.subject_id == subject_id,
        )

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
            statement=select(func.count()).select_from(query.subquery())
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
        result = await self._execute(statement=query)

        return PaginatedSchema[SignatureReferenceSchema](
            total=total,
            page=filters.page,
            size=filters.size,
            data=[
                SignatureReferenceSchema.model_validate(reference)
                for reference in result.mappings()
            ],
        )

    async def delete(self, *, user_id: UUID, reference_id: UUID) -> bool:
        query = (
            delete(SignatureReferenceModel)
            .where(
                SignatureReferenceModel.user_id == user_id,
                SignatureReferenceModel.id == reference_id,
            )
            .returning(SignatureReferenceModel.id)
        )
        result = await self._execute(statement=query)

        return result.scalar_one_or_none() is not None

    async def _get_one(
        self, *, user_id: UUID, condition: ColumnElement[bool]
    ) -> SignatureReferenceSchema | None:
        query = select(
            SignatureReferenceModel.id,
            SignatureReferenceModel.subject_id,
            SignatureReferenceModel.created_at,
            SignatureReferenceModel.updated_at,
        ).where(SignatureReferenceModel.user_id == user_id, condition)
        result = await self._execute(statement=query)
        reference = result.mappings().one_or_none()

        return (
            SignatureReferenceSchema.model_validate(reference)
            if reference is not None
            else None
        )
