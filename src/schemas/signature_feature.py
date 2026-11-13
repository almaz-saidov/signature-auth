from pydantic import Field

from schemas.base import BaseSchema


class SignatureFeaturesSchema[T](BaseSchema):
    duration_ms: T
    trajectory_length: T
    maximum_speed: T
    rms_acceleration: T
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
    mean_azimuth_start: T
    mean_azimuth_middle: T
    mean_azimuth_end: T
    mean_altitude_start: T
    mean_altitude_middle: T
    mean_altitude_end: T
    maximum_speed_time_ratio: T
    maximum_pause_duration_ms: T
    direction_length_ratio_0: T
    direction_length_ratio_45: T
    direction_length_ratio_90: T
    direction_length_ratio_135: T
    direction_length_ratio_180: T
    direction_length_ratio_225: T
    direction_length_ratio_270: T
    direction_length_ratio_315: T
    total_turning_angle_degrees: T
    pressure_speed_correlation: T


class SignatureFeatureStatisticsSchema(BaseSchema):
    mean: float
    standard_deviation: float = Field(ge=0)
