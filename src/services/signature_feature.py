from math import atan2, cos, degrees, hypot, log, radians, sin, sqrt
from statistics import fmean

from core.config import signature_settings
from core.exceptions.signature import InvalidSignatureSampleException
from schemas.signature_feature import (
    SignatureFeaturesSchema,
    SignatureFeatureStatisticsSchema,
)
from schemas.signature_reference import SignaturePointSchema, SignatureSampleSchema


class SignatureFeatureService:
    def extract(
        self, *, sample: SignatureSampleSchema
    ) -> SignatureFeaturesSchema[float]:
        strokes = self._get_strokes(sample=sample)

        try:
            dynamics = self._get_dynamics(strokes=strokes)
            duration_ms = sample.points[-1].time_ms - sample.points[0].time_ms
            contact_duration_ms = dynamics["contact_duration_ms"]

            return SignatureFeaturesSchema[float](
                duration_ms=duration_ms,
                pen_lift_count=len(strokes) - 1,
                pen_up_duration_ms=max(0.0, duration_ms - contact_duration_ms),
                **dynamics,
                **self._get_contact_means(strokes=strokes),
                **self._get_geometry(
                    strokes=strokes, trajectory_length=dynamics["trajectory_length"]
                ),
                **self._get_phase_features(
                    strokes=strokes, contact_duration_ms=contact_duration_ms
                ),
            )
        except (ArithmeticError, ValueError) as error:
            raise InvalidSignatureSampleException(
                detail="Не удалось вычислить конечные значения признаков подписи."
            ) from error

    def _get_contact_means(
        self, *, strokes: list[list[SignaturePointSchema]]
    ) -> dict[str, float]:
        weighted_points: list[SignaturePointSchema] = []
        weights: list[float] = []

        for stroke in strokes:
            for previous, current in zip(stroke, stroke[1:]):
                weight = (current.time_ms - previous.time_ms) / 2
                weighted_points.extend((previous, current))
                weights.extend((weight, weight))

        azimuth = self.get_circular_statistics(
            values=[point.azimuth for point in weighted_points], weights=weights
        )

        return {
            "mean_altitude": fmean(
                [point.altitude for point in weighted_points], weights=weights
            ),
            "mean_azimuth": azimuth.mean,
            "mean_pressure": fmean(
                [point.pressure for point in weighted_points], weights=weights
            ),
        }

    def _get_geometry(
        self, *, strokes: list[list[SignaturePointSchema]], trajectory_length: float
    ) -> dict[str, float]:
        contact_points = [point for stroke in strokes for point in stroke]
        width = max(point.x for point in contact_points) - min(
            point.x for point in contact_points
        )
        height = max(point.y for point in contact_points) - min(
            point.y for point in contact_points
        )

        return {
            "shape_factor": width * height / trajectory_length**2,
            "start_x": contact_points[0].x,
            "start_y": contact_points[0].y,
            "end_x": contact_points[-1].x,
            "end_y": contact_points[-1].y,
        }

    def _get_phase_features(
        self,
        *,
        strokes: list[list[SignaturePointSchema]],
        contact_duration_ms: float,
    ) -> dict[str, float]:
        features: dict[str, float] = {}
        phase_duration = contact_duration_ms / len(
            signature_settings.SIGNATURE_PHASE_NAMES
        )

        for index, name in enumerate(signature_settings.SIGNATURE_PHASE_NAMES):
            speed, pressure = self._get_phase_means(
                strokes=strokes,
                start_ms=index * phase_duration,
                end_ms=(index + 1) * phase_duration,
            )
            features[f"mean_speed_{name}"] = speed
            features[f"mean_pressure_{name}"] = pressure

        return features

    def _get_phase_means(
        self,
        *,
        strokes: list[list[SignaturePointSchema]],
        start_ms: float,
        end_ms: float,
    ) -> tuple[float, float]:
        # Время накапливается только внутри штрихов, без пауз между ними.
        elapsed = 0.0
        contact_duration = 0.0
        trajectory_length = 0.0
        pressure_integral = 0.0

        for stroke in strokes:
            for previous, current in zip(stroke, stroke[1:]):
                duration = current.time_ms - previous.time_ms
                overlap_start = max(start_ms, elapsed)
                overlap_end = min(end_ms, elapsed + duration)
                interval_start = elapsed
                elapsed += duration

                if overlap_end <= overlap_start:
                    continue

                overlap_duration = overlap_end - overlap_start
                start_fraction = (overlap_start - interval_start) / duration
                end_fraction = (overlap_end - interval_start) / duration
                pressure_change = current.pressure - previous.pressure
                start_pressure = previous.pressure + pressure_change * start_fraction
                end_pressure = previous.pressure + pressure_change * end_fraction
                pressure_integral += (
                    (start_pressure + end_pressure) / 2 * overlap_duration
                )
                trajectory_length += (
                    hypot(current.x - previous.x, current.y - previous.y)
                    * overlap_duration
                    / duration
                )
                contact_duration += overlap_duration

        return (
            trajectory_length
            / contact_duration
            * signature_settings.MILLISECONDS_PER_SECOND,
            pressure_integral / contact_duration,
        )

    def get_circular_statistics(
        self, *, values: list[float], weights: list[float] | None = None
    ) -> SignatureFeatureStatisticsSchema:
        angles = [value % signature_settings.FULL_TURN_DEGREES for value in values]
        mean_sine = fmean([sin(radians(angle)) for angle in angles], weights=weights)
        mean_cosine = fmean([cos(radians(angle)) for angle in angles], weights=weights)
        resultant_length = min(1.0, hypot(mean_sine, mean_cosine))

        if resultant_length <= signature_settings.CIRCULAR_MEAN_EPSILON:
            raise InvalidSignatureSampleException(
                detail="Невозможно определить средний азимут пера."
            )

        mean_angle = (
            degrees(atan2(mean_sine, mean_cosine))
            % signature_settings.FULL_TURN_DEGREES
        )

        if mean_angle == signature_settings.FULL_TURN_DEGREES:
            mean_angle = 0.0

        standard_deviation = degrees(sqrt(-2 * log(resultant_length)))

        if all(angle == angles[0] for angle in angles):
            mean_angle = angles[0]
            standard_deviation = 0.0

        return SignatureFeatureStatisticsSchema(
            mean=mean_angle, standard_deviation=standard_deviation
        )

    def _get_strokes(
        self, *, sample: SignatureSampleSchema
    ) -> list[list[SignaturePointSchema]]:
        strokes: list[list[SignaturePointSchema]] = []
        current_stroke: list[SignaturePointSchema] = []

        for point in sample.points:
            if point.pressure == 0:
                if current_stroke:
                    strokes.append(current_stroke)
                    current_stroke = []

                continue

            if current_stroke and point.time_ms == current_stroke[-1].time_ms:
                previous = current_stroke[-1]

                if point.x != previous.x or point.y != previous.y:
                    raise InvalidSignatureSampleException(
                        detail="Точки одного штриха с одинаковым временем должны иметь одинаковые координаты."
                    )

                current_stroke[-1] = point
            else:
                current_stroke.append(point)

        if current_stroke:
            strokes.append(current_stroke)

        return strokes

    def _get_dynamics(
        self, *, strokes: list[list[SignaturePointSchema]]
    ) -> dict[str, float]:
        trajectory_length = 0.0
        contact_duration = 0.0
        maximum_speed = 0.0
        acceleration_energy = 0.0
        acceleration_duration = 0.0

        for stroke in strokes:
            previous_velocity: tuple[float, float] | None = None
            previous_duration = 0.0

            for previous, current in zip(stroke, stroke[1:]):
                duration = (
                    current.time_ms - previous.time_ms
                ) / signature_settings.MILLISECONDS_PER_SECOND

                if duration <= 0:
                    raise InvalidSignatureSampleException(
                        detail="Интервал между различными точками штриха должен быть положительным."
                    )

                delta_x = current.x - previous.x
                delta_y = current.y - previous.y
                velocity_x = delta_x / duration
                velocity_y = delta_y / duration
                trajectory_length += hypot(delta_x, delta_y)
                contact_duration += duration
                maximum_speed = max(maximum_speed, hypot(velocity_x, velocity_y))

                if previous_velocity is not None:
                    # Скорости относятся к серединам соседних временных интервалов.
                    interval = (previous_duration + duration) / 2
                    acceleration = (
                        hypot(
                            velocity_x - previous_velocity[0],
                            velocity_y - previous_velocity[1],
                        )
                        / interval
                    )
                    acceleration_energy += acceleration**2 * interval
                    acceleration_duration += interval

                previous_velocity = (velocity_x, velocity_y)
                previous_duration = duration

        if trajectory_length <= 0:
            raise InvalidSignatureSampleException(
                detail="Подпись должна содержать движение пера во время контакта."
            )

        if acceleration_duration <= 0:
            raise InvalidSignatureSampleException(
                detail="Образец содержит недостаточно точек для расчёта ускорения."
            )

        return {
            "contact_duration_ms": sum(
                stroke[-1].time_ms - stroke[0].time_ms for stroke in strokes
            ),
            "trajectory_length": trajectory_length,
            "mean_speed": trajectory_length / contact_duration,
            "maximum_speed": maximum_speed,
            "rms_acceleration": sqrt(acceleration_energy / acceleration_duration),
        }
