from math import exp
from uuid import UUID

from core.config import signature_settings
from core.exceptions.http import (
    InvalidSignatureException,
    UnsupportedSignatureReferenceVersionException,
)
from core.exceptions.signature import InvalidSignatureSampleException
from schemas.signature_feature import (
    SignatureFeaturesSchema,
    SignatureFeatureStatisticsSchema,
)
from schemas.signature_reference import (
    SignatureReferenceDataSchema,
    SignatureSampleSchema,
    SignatureValidationResultSchema,
)
from services.encryption import EncryptionService
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
        encryption_service: EncryptionService,
    ) -> None:
        self._reference_service = reference_service
        self._normalization_service = normalization_service
        self._feature_service = feature_service
        self._encryption_service = encryption_service
        self._weights = signature_settings.VERIFICATION_WEIGHTS.copy()
        self._threshold = signature_settings.VERIFICATION_THRESHOLD
        self._total_weight = sum(self._weights.values())

    async def verify(
        self, *, user_id: UUID, reference_id: UUID, sample: SignatureSampleSchema
    ) -> SignatureValidationResultSchema:
        record = await self._reference_service.get_record_by_id(
            user_id=user_id, reference_id=reference_id
        )
        decrypted_reference = self._encryption_service.decrypt(data=record.data)

        reference = SignatureReferenceDataSchema.model_validate_json(
            decrypted_reference
        )

        if reference.version != signature_settings.SIGNATURE_REFERENCE_VERSION:
            raise UnsupportedSignatureReferenceVersionException()

        try:
            normalized_sample = await self._normalization_service.normalize(
                sample=sample
            )
            features = self._feature_service.extract(sample=normalized_sample)
        except InvalidSignatureSampleException as error:
            raise InvalidSignatureException(detail=str(error)) from error

        score = self._calculate_score(features=features, reference=reference)

        return SignatureValidationResultSchema(
            validated=score >= self._threshold, score=score
        )

    def _calculate_score(
        self,
        *,
        features: SignatureFeaturesSchema[float],
        reference: SignatureReferenceDataSchema,
    ) -> float:
        weighted_sum = sum(
            weight
            * self._calculate_membership(
                feature_name=name,
                value=getattr(features, name),
                statistics=getattr(reference.features, name),
            )
            for name, weight in self._weights.items()
        )

        return (
            weighted_sum
            / self._total_weight
            * signature_settings.VERIFICATION_SCORE_MAX
        )

    def _calculate_membership(
        self,
        *,
        feature_name: str,
        value: float,
        statistics: SignatureFeatureStatisticsSchema,
    ) -> float:
        difference = abs(value - statistics.mean)

        if feature_name == "mean_azimuth":
            full_turn = signature_settings.FULL_TURN_DEGREES
            half_turn = full_turn / 2
            difference = abs(
                (value % full_turn - statistics.mean % full_turn + half_turn)
                % full_turn
                - half_turn
            )

        if statistics.standard_deviation == 0:
            return 1.0 if difference == 0 else 0.0

        standardized_difference = difference / statistics.standard_deviation

        return exp(-0.5 * standardized_difference * standardized_difference)
