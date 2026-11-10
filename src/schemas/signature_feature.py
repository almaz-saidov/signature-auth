from pydantic import Field

from schemas.base import BaseSchema


class SignatureFeaturesSchema[T](BaseSchema):
    duration_ms: T
    trajectory_length: T
    maximum_speed: T
    rms_acceleration: T
    mean_altitude: T
    mean_azimuth: T
    shape_factor: T
    pen_lift_count: T
    contact_duration_ms: T
    pen_up_duration_ms: T
    start_x: T
    start_y: T
    end_x: T
    end_y: T
    mean_speed_start: T
    mean_speed_middle: T
    mean_speed_end: T
    mean_pressure_start: T
    mean_pressure_middle: T
    mean_pressure_end: T


class SignatureFeatureStatisticsSchema(BaseSchema):
    mean: float
    standard_deviation: float = Field(ge=0)
