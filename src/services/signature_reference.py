from statistics import mean, stdev
from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions.database import DatabaseException
from core.exceptions.http import (
    InvalidSignatureException,
    SignatureReferenceNotFoundException,
)
from core.exceptions.signature import (
    InvalidSignatureSampleException,
    ReferenceFormationException,
)
from database.repositories.signature_reference import SignatureReferenceRepository
from schemas.pagination import PaginatedSchema
from schemas.signature_feature import (
    SignatureFeaturesSchema,
    SignatureFeatureStatisticsSchema,
)
from schemas.signature_reference import (
    CreateSignatureReferencePayloadSchema,
    ListSignatureReferenceFiltersSchema,
    SignatureReferenceDataSchema,
    SignatureReferenceRecordSchema,
    SignatureReferenceSaveResultSchema,
    SignatureReferenceSchema,
    SignatureSampleSchema,
)
from services.database import DatabaseService
from services.encryption import EncryptionService
from services.signature_feature import SignatureFeatureService
from services.signature_normalization import SignatureNormalizationService


class SignatureReferenceService(DatabaseService[SignatureReferenceRepository]):
    def __init__(
        self,
        *,
        repository: SignatureReferenceRepository,
        session: AsyncSession,
        normalization_service: SignatureNormalizationService,
        feature_service: SignatureFeatureService,
        encryption_service: EncryptionService,
    ) -> None:
        super().__init__(repository=repository, session=session)
        self._normalization_service = normalization_service
        self._feature_service = feature_service
        self._encryption_service = encryption_service

    async def create_or_update(
        self, *, user_id: UUID, payload: CreateSignatureReferencePayloadSchema
    ) -> SignatureReferenceSaveResultSchema:
        try:
            existing_reference = await self._repository.get_by_subject_id(
                user_id=user_id, subject_id=payload.subject_id
            )

            normalized_samples = [
                await self._normalization_service.normalize(sample=sample)
                for sample in payload.samples
            ]

            reference = self._create_reference_from_samples(
                normalized_samples=normalized_samples
            )
            serialized_reference = reference.model_dump_json().encode("utf-8")

            encrypted_reference = self._encryption_service.encrypt(
                data=serialized_reference
            )

            action: Literal["created", "updated"] = "created"

            if existing_reference is not None:
                reference_id = await self._repository.update(
                    user_id=user_id,
                    reference_id=existing_reference.id,
                    data=encrypted_reference,
                )

                if reference_id is None:
                    raise SignatureReferenceNotFoundException()

                action = "updated"
            else:
                reference_id = await self._repository.create(
                    user_id=user_id,
                    subject_id=payload.subject_id,
                    data=encrypted_reference,
                )

            result = SignatureReferenceSaveResultSchema(
                reference_id=reference_id, action=action
            )
            await self._commit()

            return result
        except (InvalidSignatureSampleException, ReferenceFormationException) as error:
            raise InvalidSignatureException(detail=str(error)) from error
        except DatabaseException:
            await self._rollback()
            raise

    async def get_list(
        self, *, user_id: UUID, filters: ListSignatureReferenceFiltersSchema
    ) -> PaginatedSchema[SignatureReferenceSchema]:
        return await self._repository.get_list(user_id=user_id, filters=filters)

    async def get_by_id(
        self, *, user_id: UUID, reference_id: UUID
    ) -> SignatureReferenceSchema:
        reference = await self._repository.get_by_id(
            user_id=user_id, reference_id=reference_id
        )

        if reference is None:
            raise SignatureReferenceNotFoundException()

        return reference

    async def get_record_by_id(
        self, *, user_id: UUID, reference_id: UUID
    ) -> SignatureReferenceRecordSchema:
        reference = await self._repository.get_record_by_id(
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

    def _create_reference_from_samples(
        self, *, normalized_samples: list[SignatureSampleSchema]
    ) -> SignatureReferenceDataSchema:
        features = [
            self._feature_service.extract(sample=sample)
            for sample in normalized_samples
        ]
        statistics: dict[str, SignatureFeatureStatisticsSchema] = {}

        try:
            for name in SignatureFeaturesSchema.model_fields:
                values = [
                    getattr(sample_features, name) for sample_features in features
                ]

                if name == "mean_azimuth":
                    statistics[name] = self._feature_service.get_circular_statistics(
                        values=values
                    )
                else:
                    statistics[name] = SignatureFeatureStatisticsSchema(
                        mean=mean(values), standard_deviation=stdev(values)
                    )

            return SignatureReferenceDataSchema(
                sample_count=len(normalized_samples),
                features=SignatureFeaturesSchema[SignatureFeatureStatisticsSchema](
                    **statistics
                ),
            )
        except (ArithmeticError, ValueError) as error:
            raise ReferenceFormationException() from error
