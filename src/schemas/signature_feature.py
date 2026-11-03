from pydantic import Field

from schemas.base import BaseSchema


class SignatureFeaturesSchema[T](BaseSchema):
    duration_ms: T
    trajectory_length: T
    mean_speed: T
    maximum_speed: T
    rms_acceleration: T
    mean_altitude: T
    mean_azimuth: T
    mean_pressure: T
    normalized_area: T


class SignatureFeatureStatisticsSchema(BaseSchema):
    mean: float
    standard_deviation: float = Field(ge=0)
