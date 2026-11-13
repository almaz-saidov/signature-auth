from collections.abc import Iterator
from math import atan2, cos, degrees, floor, fsum, hypot, log, radians, sin, sqrt
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
                maximum_pause_duration_ms=self._get_maximum_pause_duration(
                    strokes=strokes
                ),
                **self._get_direction_features(strokes=strokes),
                total_turning_angle_degrees=self._get_total_turning_angle(
                    strokes=strokes
                ),
                pressure_speed_correlation=self._get_pressure_speed_correlation(
                    strokes=strokes
                ),
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

    def _get_total_turning_angle(
        self, *, strokes: list[list[SignaturePointSchema]]
    ) -> float:
        turns: list[float] = []

        for stroke in strokes:
            previous_direction: tuple[float, float] | None = None

            for previous, current in zip(stroke, stroke[1:]):
                direction = current.x - previous.x, current.y - previous.y

                if direction == (0, 0):
                    continue

                if previous_direction is not None:
                    cross = (
                        previous_direction[0] * direction[1]
                        - previous_direction[1] * direction[0]
                    )
                    dot = (
                        previous_direction[0] * direction[0]
                        + previous_direction[1] * direction[1]
                    )
                    turns.append(abs(degrees(atan2(cross, dot))))

                previous_direction = direction

        return fsum(turns)

    def _get_pressure_speed_correlation(
        self, *, strokes: list[list[SignaturePointSchema]]
    ) -> float:
        speeds: list[float] = []
        pressures: list[float] = []
        durations: list[float] = []

        for stroke in strokes:
            for previous, current in zip(stroke, stroke[1:]):
                duration = (
                    current.time_ms - previous.time_ms
                ) / signature_settings.MILLISECONDS_PER_SECOND
                speeds.append(
                    hypot(current.x - previous.x, current.y - previous.y) / duration
                )
                pressures.append((previous.pressure + current.pressure) / 2)
                durations.append(duration)

        return self._get_weighted_correlation(
            speeds=speeds, pressures=pressures, durations=durations
        )

    def _get_weighted_correlation(
        self, *, speeds: list[float], pressures: list[float], durations: list[float]
    ) -> float:
        if not durations or len(set(speeds)) == 1 or len(set(pressures)) == 1:
            return 0.0

        mean_speed = fmean(speeds, weights=durations)
        mean_pressure = fmean(pressures, weights=durations)
        speed_deviations = [speed - mean_speed for speed in speeds]
        pressure_deviations = [pressure - mean_pressure for pressure in pressures]
        speed_variance = fsum(
            deviation**2 * duration
            for deviation, duration in zip(speed_deviations, durations)
        )
        pressure_variance = fsum(
            deviation**2 * duration
            for deviation, duration in zip(pressure_deviations, durations)
        )

        if speed_variance == 0 or pressure_variance == 0:
            return 0.0

        covariance = fsum(
            speed * pressure * duration
            for speed, pressure, duration in zip(
                speed_deviations, pressure_deviations, durations
            )
        )
        correlation = covariance / (sqrt(speed_variance) * sqrt(pressure_variance))

        return max(-1.0, min(1.0, correlation))

    def _get_maximum_pause_duration(
        self, *, strokes: list[list[SignaturePointSchema]]
    ) -> float:
        return max(
            (
                following[0].time_ms - previous[-1].time_ms
                for previous, following in zip(strokes, strokes[1:])
            ),
            default=0.0,
        )

    def _get_direction_features(
        self, *, strokes: list[list[SignaturePointSchema]]
    ) -> dict[str, float]:
        sector_count = signature_settings.DIRECTION_SECTOR_COUNT
        sector_width = signature_settings.FULL_TURN_DEGREES / sector_count
        lengths = [0.0] * sector_count

        for stroke in strokes:
            for previous, current in zip(stroke, stroke[1:]):
                delta_x = current.x - previous.x
                delta_y = current.y - previous.y
                length = hypot(delta_x, delta_y)

                if length == 0:
                    continue

                angle = degrees(atan2(delta_y, delta_x))
                sector = floor((angle + sector_width / 2) / sector_width) % sector_count
                lengths[sector] += length

        total_length = fsum(lengths)

        return {
            f"direction_length_ratio_{int(index * sector_width)}": length / total_length
            for index, length in enumerate(lengths)
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

        for index, phase in enumerate(signature_settings.SIGNATURE_PHASE_NAMES):
            values = self._get_phase_means(
                strokes=strokes,
                start_ms=index * phase_duration,
                end_ms=(index + 1) * phase_duration,
            )
            features.update(
                {f"{name}_{phase}": value for name, value in values.items()}
            )

        return features

    def _get_phase_intervals(
        self,
        *,
        strokes: list[list[SignaturePointSchema]],
        start_ms: float,
        end_ms: float,
    ) -> Iterator[
        tuple[SignaturePointSchema, SignaturePointSchema, float, float, float]
    ]:
        # Время накапливается только внутри штрихов, без пауз между ними.
        elapsed = 0.0

        for stroke in strokes:
            for previous, current in zip(stroke, stroke[1:]):
                duration = current.time_ms - previous.time_ms
                overlap_start = max(start_ms, elapsed)
                overlap_end = min(end_ms, elapsed + duration)
                interval_start = elapsed
                elapsed += duration

                if overlap_end <= overlap_start:
                    continue

                yield (
                    previous,
                    current,
                    (overlap_start - interval_start) / duration,
                    (overlap_end - interval_start) / duration,
                    overlap_end - overlap_start,
                )

    def _get_phase_means(
        self,
        *,
        strokes: list[list[SignaturePointSchema]],
        start_ms: float,
        end_ms: float,
    ) -> dict[str, float]:
        contact_duration = 0.0
        trajectory_length = 0.0
        pressure_integral = 0.0
        altitudes: list[float] = []
        azimuths: list[float] = []
        weights: list[float] = []
        full_turn = signature_settings.FULL_TURN_DEGREES

        for (
            previous,
            current,
            start_fraction,
            end_fraction,
            duration,
        ) in self._get_phase_intervals(
            strokes=strokes, start_ms=start_ms, end_ms=end_ms
        ):
            pressure_change = current.pressure - previous.pressure
            start_pressure = previous.pressure + pressure_change * start_fraction
            end_pressure = previous.pressure + pressure_change * end_fraction
            pressure_integral += (start_pressure + end_pressure) / 2 * duration
            trajectory_length += (
                hypot(current.x - previous.x, current.y - previous.y)
                * duration
                / (current.time_ms - previous.time_ms)
            )
            contact_duration += duration
            altitude_change = current.altitude - previous.altitude
            azimuth_change = (
                current.azimuth - previous.azimuth + full_turn / 2
            ) % full_turn - full_turn / 2
            altitudes.extend(
                previous.altitude + altitude_change * fraction
                for fraction in (start_fraction, end_fraction)
            )
            azimuths.extend(
                previous.azimuth + azimuth_change * fraction
                for fraction in (start_fraction, end_fraction)
            )
            weights.extend((duration / 2, duration / 2))

        return {
            "mean_speed": trajectory_length
            / contact_duration
            * signature_settings.MILLISECONDS_PER_SECOND,
            "mean_pressure": pressure_integral / contact_duration,
            "mean_altitude": fmean(altitudes, weights=weights),
            "mean_azimuth": self.get_circular_statistics(
                values=azimuths, weights=weights
            ).mean,
        }

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
        maximum_speed = 0.0
        acceleration_energy = 0.0
        acceleration_duration = 0.0
        elapsed_contact_ms = 0.0
        maximum_speed_time_ms = 0.0

        for stroke in strokes:
            previous_velocity: tuple[float, float] | None = None
            previous_duration = 0.0

            for previous, current in zip(stroke, stroke[1:]):
                duration_ms = current.time_ms - previous.time_ms
                duration = duration_ms / signature_settings.MILLISECONDS_PER_SECOND

                if duration <= 0:
                    raise InvalidSignatureSampleException(
                        detail="Интервал между различными точками штриха должен быть положительным."
                    )

                delta_x = current.x - previous.x
                delta_y = current.y - previous.y
                velocity_x = delta_x / duration
                velocity_y = delta_y / duration
                trajectory_length += hypot(delta_x, delta_y)
                speed = hypot(velocity_x, velocity_y)

                if speed > maximum_speed:
                    maximum_speed = speed
                    maximum_speed_time_ms = elapsed_contact_ms + duration_ms / 2

                elapsed_contact_ms += duration_ms

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
            "maximum_speed": maximum_speed,
            "maximum_speed_time_ratio": maximum_speed_time_ms / elapsed_contact_ms,
            "rms_acceleration": sqrt(acceleration_energy / acceleration_duration),
        }
