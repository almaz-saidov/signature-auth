from math import isfinite

from core.exceptions.signature import InvalidSignatureSampleException
from schemas.signature_reference import SignatureSampleSchema


class SignatureNormalizationService:
    async def normalize(
        self, *, sample: SignatureSampleSchema
    ) -> SignatureSampleSchema:
        contact_points = [point for point in sample.points if point.pressure > 0]

        if not contact_points:
            raise InvalidSignatureSampleException(
                detail="Образец должен содержать точки контакта пера."
            )

        minimum_x = min(point.x for point in contact_points)
        minimum_y = min(point.y for point in contact_points)
        width = max(point.x for point in contact_points) - minimum_x
        height = max(point.y for point in contact_points) - minimum_y
        scale = max(width, height)

        if scale <= 0 or not isfinite(scale):
            raise InvalidSignatureSampleException(
                detail="Размер подписи должен быть положительным конечным числом."
            )

        normalized_sample = sample.model_copy(deep=True)

        for point in normalized_sample.points:
            point.x = (point.x - minimum_x) / scale
            point.y = (point.y - minimum_y) / scale

            if not isfinite(point.x) or not isfinite(point.y):
                raise InvalidSignatureSampleException(
                    detail="Не удалось нормализовать координаты подписи."
                )

        return normalized_sample
