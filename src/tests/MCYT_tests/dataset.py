from pathlib import Path
from struct import Struct

from core.config import signature_settings, test_settings
from schemas.signature_reference import SignaturePointSchema, SignatureSampleSchema


def read_header(*, content: bytes, filename: str) -> tuple[int, int]:
    header = Struct(test_settings.MCYT_FPG_HEADER_FORMAT)
    point = Struct(test_settings.MCYT_FPG_POINT_FORMAT)

    if len(content) < header.size:
        raise ValueError(f"Файл {filename} не содержит полного заголовка FPG.")

    (
        signature,
        header_size,
        file_format,
        _,
        channels,
        _,
        resolution,
        _,
        dimensions,
        point_count,
        _,
        sampling_rate,
    ) = header.unpack_from(content)
    metadata = (signature, file_format, channels, resolution, dimensions)

    if metadata != test_settings.MCYT_FPG_METADATA:
        raise ValueError(f"Файл {filename} имеет неподдерживаемый формат FPG.")

    if (
        header_size < header.size
        or len(content) != header_size + point_count * point.size
        or sampling_rate <= 0
    ):
        raise ValueError(f"Файл {filename} содержит некорректный заголовок или данные.")

    return header_size, sampling_rate


def read_sample(*, path: Path) -> SignatureSampleSchema:
    content = path.read_bytes()
    header_size, sampling_rate = read_header(content=content, filename=path.name)
    point = Struct(test_settings.MCYT_FPG_POINT_FORMAT)
    points = [
        SignaturePointSchema(
            x=x,
            y=y,
            pressure=pressure / test_settings.MCYT_MAX_PRESSURE,
            azimuth=azimuth,
            altitude=altitude,
            time_ms=index * signature_settings.MILLISECONDS_PER_SECOND / sampling_rate,
        )
        for index, (x, y, pressure, azimuth, altitude) in enumerate(
            point.iter_unpack(content[header_size:])
        )
    ]

    return SignatureSampleSchema(points=points)


def get_authors(*, dataset: Path, authors: list[str] | None) -> list[Path]:
    if not dataset.is_dir():
        raise ValueError(f"Каталог датасета не найден: {dataset}")

    available = {
        path.name: path
        for path in sorted(dataset.iterdir())
        if path.is_dir()
        and len(path.name) == test_settings.MCYT_AUTHOR_ID_LENGTH
        and path.name.isascii()
        and path.name.isdigit()
    }

    if not available:
        raise ValueError("В датасете не найдены каталоги авторов MCYT.")

    selected = sorted(set(authors)) if authors is not None else list(available)
    missing = [author for author in selected if author not in available]

    if missing:
        raise ValueError(f"В датасете отсутствуют авторы: {', '.join(missing)}")

    return [available[author] for author in selected]
