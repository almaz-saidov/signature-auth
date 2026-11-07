from datetime import date, datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from core.config import signature_settings
from schemas.base import BaseSchema
from schemas.signature_feature import (
    SignatureFeaturesSchema,
    SignatureFeatureStatisticsSchema,
)

from schemas.pagination import PaginationFiltersSchema


class SignaturePointSchema(BaseSchema):
    model_config = ConfigDict(strict=True)

    x: float = Field(description="Координата X в исходных единицах устройства")
    y: float = Field(description="Координата Y в исходных единицах устройства")
    pressure: float = Field(ge=0, le=1, description="Давление в диапазоне от 0 до 1")
    azimuth: float = Field(description="Азимут пера в градусах")
    altitude: float = Field(description="Угол подъёма пера в градусах")
    time_ms: float = Field(
        ge=0, description="Время от первой точки образца в миллисекундах"
    )


class SignatureSampleSchema(BaseSchema):
    points: list[SignaturePointSchema] = Field(
        min_length=signature_settings.MIN_SIGNATURE_POINT_COUNT
    )

    @model_validator(mode="after")
    def validate_time_order(self) -> Self:
        if self.points[0].time_ms != 0:
            raise ValueError("Время первой точки должно быть равно нулю")

        if any(
            following.time_ms < previous.time_ms
            for previous, following in zip(self.points, self.points[1:])
        ):
            raise ValueError("Время точек должно идти в неубывающем порядке")

        return self


class ListSignatureReferenceFiltersSchema(PaginationFiltersSchema):
    subject_id: str | None = Field(default=None, min_length=1)
    from_: date | None = Field(
        default=None,
        alias="from",
        description="Первая дата создания, включительно, UTC",
    )
    to_: date | None = Field(
        default=None,
        alias="to",
        description="Последняя дата создания, включительно, UTC",
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.from_ is not None and self.to_ is not None and self.from_ > self.to_:
            raise ValueError("Дата from не должна быть позже даты to")

        return self


class CreateSignatureReferencePayloadSchema(BaseSchema):
    subject_id: str = Field(min_length=1)
    samples: list[SignatureSampleSchema] = Field(
        min_length=signature_settings.REFERENCE_SAMPLE_COUNT,
        max_length=signature_settings.REFERENCE_SAMPLE_COUNT,
    )


class VerifySignaturePayloadSchema(BaseSchema):
    sample: SignatureSampleSchema


class SignatureReferenceSchema(BaseSchema):
    id: UUID
    subject_id: str
    created_at: datetime
    updated_at: datetime


class SignatureReferenceSaveResultSchema(BaseSchema):
    reference_id: UUID
    action: Literal["created", "updated"]


class SignatureReferenceDataSchema(BaseSchema):
    version: int = Field(default=signature_settings.SIGNATURE_REFERENCE_VERSION, ge=1)
    sample_count: int = Field(
        ge=signature_settings.REFERENCE_SAMPLE_COUNT,
        le=signature_settings.REFERENCE_SAMPLE_COUNT,
    )
    features: SignatureFeaturesSchema[SignatureFeatureStatisticsSchema]


class SignatureReferenceRecordSchema(SignatureReferenceSchema):
    user_id: UUID
    data: bytes = Field(repr=False)


class SignatureValidationResultSchema(BaseSchema):
    validated: bool = Field(description="Решение сервиса по порогу соответствия")
    score: float = Field(
        ge=0,
        le=signature_settings.VERIFICATION_SCORE_MAX,
        description="Степень соответствия в процентах, не вероятность подлинности",
    )
