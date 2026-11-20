import json
from uuid import UUID

from core.config import signature_settings
from core.exceptions.http import (
    InvalidSignatureException,
    UnsupportedSignatureReferenceVersionException,
)
from core.exceptions.signature import InvalidSignatureSampleException
from schemas.signature_reference import (
    SignatureReferenceDataSchema,
    SignatureSampleSchema,
    SignatureValidationResultSchema,
)
from services.encryption import EncryptionService
from services.signature_comparison import SignatureComparisonService
from services.signature_feature import SignatureFeatureService
from services.signature_normalization import SignatureNormalizationService
from services.signature_reference import SignatureReferenceService


class SignatureVerificationService:
    def __init__(
        self,
        *,
        reference_service: SignatureReferenceService,
        normalization_service: SignatureNormalizationService,
        feature_service: SignatureFeatureService,
        comparison_service: SignatureComparisonService,
        encryption_service: EncryptionService,
    ) -> None:
        self._reference_service = reference_service
        self._normalization_service = normalization_service
        self._feature_service = feature_service
        self._comparison_service = comparison_service
        self._encryption_service = encryption_service
        self._threshold = signature_settings.VERIFICATION_THRESHOLD

    async def verify(
        self, *, user_id: UUID, reference_id: UUID, sample: SignatureSampleSchema
    ) -> SignatureValidationResultSchema:
        record = await self._reference_service.get_record_by_id(
            user_id=user_id, reference_id=reference_id
        )
        decrypted_reference = self._encryption_service.decrypt(data=record.data)

        reference_data = json.loads(decrypted_reference)

        if reference_data["version"] != signature_settings.SIGNATURE_REFERENCE_VERSION:
            raise UnsupportedSignatureReferenceVersionException()

        reference = SignatureReferenceDataSchema.model_validate(reference_data)

        try:
            normalized_sample = await self._normalization_service.normalize(
                sample=sample
            )
            features = self._feature_service.extract(sample=normalized_sample)
        except InvalidSignatureSampleException as error:
            raise InvalidSignatureException(detail=str(error)) from error

        score = self._comparison_service.calculate_score(
            features=features, statistics=reference.features
        )

        return SignatureValidationResultSchema(
            validated=score >= self._threshold, score=score
        )
