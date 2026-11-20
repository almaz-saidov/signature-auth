from math import exp

from core.config import signature_settings
from schemas.signature_feature import (
    SignatureFeaturesSchema,
    SignatureFeatureStatisticsSchema,
)


class SignatureComparisonService:
    def __init__(self) -> None:
        self._weights = signature_settings.VERIFICATION_WEIGHTS.copy()
        self._total_weight = sum(self._weights.values())

    def calculate_score(
        self,
        *,
        features: SignatureFeaturesSchema[float],
        statistics: SignatureFeaturesSchema[SignatureFeatureStatisticsSchema],
    ) -> float:
        weighted_sum = sum(
            weight
            * self._calculate_membership(
                feature_name=name,
                value=getattr(features, name),
                statistics=getattr(statistics, name),
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

        if feature_name in signature_settings.CIRCULAR_FEATURE_NAMES:
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
