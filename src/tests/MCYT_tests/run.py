import argparse
import asyncio
import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from math import isfinite
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx

from core.config import signature_settings, test_settings
from schemas.signature_reference import SignatureValidationResultSchema
from tests.MCYT_tests.dataset import get_authors, read_sample
from tests.MCYT_tests.results import (
    AuthorResult,
    SampleResult,
    print_summary,
    summarize,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Проверка сервиса на подлинных подписях и подделках MCYT."
    )
    parser.add_argument("--base-url", required=True, help="Адрес сервиса без /api/v1")
    parser.add_argument(
        "--api-key",
        default=os.getenv("MCYT_API_KEY"),
        help="API-ключ; по умолчанию MCYT_API_KEY из окружения",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=test_settings.MCYT_DATASET_PATH,
        help="Каталог MCYT_Signature_100",
    )
    parser.add_argument(
        "--authors",
        nargs="+",
        help="Идентификаторы авторов, например 0000 0001; по умолчанию все",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Путь к JSON-отчёту; по умолчанию отдельный файл в data/mcyt_results",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=test_settings.MCYT_HTTP_TIMEOUT_SECONDS,
        help="Тайм-аут HTTP-запроса в секундах",
    )
    arguments = parser.parse_args()
    validate_arguments(parser=parser, arguments=arguments)

    return arguments


def validate_arguments(
    *, parser: argparse.ArgumentParser, arguments: argparse.Namespace
) -> None:
    if not arguments.api_key:
        parser.error("Передайте --api-key или задайте MCYT_API_KEY в окружении.")

    if not isfinite(arguments.timeout) or arguments.timeout <= 0:
        parser.error("Тайм-аут должен быть положительным конечным числом.")


async def request_json(
    *, client: httpx.AsyncClient, path: str, payload: dict[str, Any]
) -> Any:
    try:
        response = await client.post(path, json=payload)
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise ValueError(
            f"Запрос {path} завершился с HTTP {error.response.status_code}."
        ) from error
    except httpx.RequestError as error:
        raise ValueError(f"Не удалось выполнить запрос {path}.") from error

    try:
        return response.json()
    except ValueError as error:
        raise ValueError(f"Ответ на запрос {path} не является JSON.") from error


async def enroll(
    *, client: httpx.AsyncClient, author: Path, result: AuthorResult
) -> None:
    if len(result.enrollment_files) != signature_settings.REFERENCE_SAMPLE_COUNT:
        raise ValueError("Недостаточно подлинных образцов для создания эталона.")

    if not any(sample.kind == "genuine" for sample in result.samples):
        raise ValueError(
            "Не осталось подлинных образцов для проверки после создания эталона."
        )

    if not any(sample.kind == "forgery" for sample in result.samples):
        raise ValueError("Не найдены подделки для проверки.")

    samples = [
        read_sample(path=author / name).model_dump() for name in result.enrollment_files
    ]
    response = await request_json(
        client=client,
        path="/api/v1/signature-references",
        payload={"subject_id": result.subject_id, "samples": samples},
    )

    if not isinstance(response, str):
        raise ValueError("Сервис не вернул UUID созданного эталона.")

    result.reference_id = str(UUID(response))


async def verify_samples(
    *, client: httpx.AsyncClient, author: Path, result: AuthorResult
) -> None:
    for sample in result.samples:
        try:
            payload = read_sample(path=author / sample.file).model_dump()
            response = await request_json(
                client=client,
                path=f"/api/v1/signature-references/{result.reference_id}/verifications",
                payload={"sample": payload},
            )
            verification = SignatureValidationResultSchema.model_validate(response)
            sample.score = verification.score
            sample.validated = verification.validated
        except (OSError, ValueError) as error:
            sample.error = str(error)


def prepare_author(*, author: Path, run_id: str) -> AuthorResult:
    genuine = sorted(author.glob(f"{author.name}v*.fpg"))
    forgeries = sorted(author.glob(f"{author.name}f*.fpg"))
    count = signature_settings.REFERENCE_SAMPLE_COUNT

    return AuthorResult(
        author_id=author.name,
        subject_id=f"mcyt:{run_id}:{author.name}",
        enrollment_files=[path.name for path in genuine[:count]],
        samples=[
            SampleResult(kind="genuine", file=path.name) for path in genuine[count:]
        ]
        + [SampleResult(kind="forgery", file=path.name) for path in forgeries],
    )


def write_report(*, path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def create_report(
    *, client: httpx.AsyncClient, dataset: Path, authors: list[Path], run_id: str
) -> dict[str, Any]:
    sample_count = signature_settings.REFERENCE_SAMPLE_COUNT

    return {
        "run_id": run_id,
        "started_at": datetime.now(UTC).isoformat(),
        "finished_at": None,
        "base_url": str(client.base_url),
        "dataset": str(dataset.resolve()),
        "enrollment_sample_count": sample_count,
        "selection": (
            f"Первые {sample_count} подлинных файлов по имени — для эталона; "
            "остальные подлинные и все подделки — для проверки."
        ),
        "selected_authors": [author.name for author in authors],
        "authors": [],
    }


async def run_author(
    *, client: httpx.AsyncClient, author: Path, run_id: str
) -> AuthorResult:
    result = prepare_author(author=author, run_id=run_id)

    try:
        await enroll(client=client, author=author, result=result)
    except (OSError, ValueError) as error:
        result.enrollment_error = str(error)
    else:
        await verify_samples(client=client, author=author, result=result)

    return result


async def run_experiment(
    *,
    client: httpx.AsyncClient,
    dataset: Path,
    authors: list[Path],
    output: Path,
    run_id: str,
) -> dict[str, Any]:
    results: list[AuthorResult] = []
    report = create_report(
        client=client, dataset=dataset, authors=authors, run_id=run_id
    )

    for index, author in enumerate(authors, start=1):
        result = await run_author(client=client, author=author, run_id=run_id)
        results.append(result)
        report["authors"] = [asdict(item) for item in results]
        report["summary"] = summarize(authors=results)
        report["summary"]["complete"] = (
            len(results) == len(authors) and report["summary"]["complete"]
        )
        write_report(path=output, report=report)
        status = "ошибка создания эталона" if result.enrollment_error else "проверен"
        print(f"[{index}/{len(authors)}] Автор {author.name}: {status}", flush=True)

    report["finished_at"] = datetime.now(UTC).isoformat()
    write_report(path=output, report=report)
    print_summary(summary=report["summary"])
    print(f"Отчёт: {output.resolve()}")

    return report


async def main() -> int:
    arguments = parse_arguments()
    run_id = f"{datetime.now(UTC):%Y%m%dT%H%M%S}-{uuid4().hex[:8]}"
    output = arguments.output or test_settings.MCYT_REPORT_DIRECTORY / f"{run_id}.json"

    try:
        authors = get_authors(dataset=arguments.dataset, authors=arguments.authors)

        async with httpx.AsyncClient(
            base_url=arguments.base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {arguments.api_key}"},
            timeout=arguments.timeout,
        ) as client:
            report = await run_experiment(
                client=client,
                dataset=arguments.dataset,
                authors=authors,
                output=output,
                run_id=run_id,
            )
    except (OSError, ValueError) as error:
        print(f"Не удалось завершить проверку MCYT: {error}")

        return 1

    return 0 if report["summary"]["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
