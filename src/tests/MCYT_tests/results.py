from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(kw_only=True)
class SampleResult:
    kind: Literal["genuine", "forgery"]
    file: str
    score: float | None = None
    validated: bool | None = None
    error: str | None = None


@dataclass(kw_only=True)
class AuthorResult:
    author_id: str
    subject_id: str
    enrollment_files: list[str]
    reference_id: str | None = None
    enrollment_error: str | None = None
    samples: list[SampleResult] = field(default_factory=list)


def summarize_samples(
    *, samples: list[SampleResult], kind: Literal["genuine", "forgery"]
) -> dict[str, int | float | None]:
    evaluated = [sample for sample in samples if sample.validated is not None]
    accepted = sum(sample.validated is True for sample in evaluated)
    rejected = len(evaluated) - accepted
    errors = sum(sample.error is not None for sample in samples)
    mistakes = rejected if kind == "genuine" else accepted
    metric = (
        "false_rejection_rate_percent"
        if kind == "genuine"
        else "false_acceptance_rate_percent"
    )

    return {
        "planned": len(samples),
        "evaluated": len(evaluated),
        "accepted": accepted,
        "rejected": rejected,
        "errors": errors,
        "skipped": len(samples) - len(evaluated) - errors,
        metric: mistakes / len(evaluated) * 100 if evaluated else None,
    }


def summarize(*, authors: list[AuthorResult]) -> dict[str, Any]:
    samples = [sample for author in authors for sample in author.samples]

    return {
        "authors": len(authors),
        "references_created": sum(
            author.reference_id is not None for author in authors
        ),
        "enrollment_errors": sum(
            author.enrollment_error is not None for author in authors
        ),
        "genuine": summarize_samples(
            samples=[sample for sample in samples if sample.kind == "genuine"],
            kind="genuine",
        ),
        "forgery": summarize_samples(
            samples=[sample for sample in samples if sample.kind == "forgery"],
            kind="forgery",
        ),
        "complete": all(
            author.enrollment_error is None
            and all(sample.validated is not None for sample in author.samples)
            for author in authors
        ),
    }


def print_summary(*, summary: dict[str, Any]) -> None:
    print(
        f"Авторов: {summary['authors']}; создано эталонов: {summary['references_created']}"
    )
    print(f"Ошибок создания эталона: {summary['enrollment_errors']}")

    for kind, label, metric in (
        ("genuine", "Ложные отказы (FRR)", "false_rejection_rate_percent"),
        ("forgery", "Ложные допуски (FAR)", "false_acceptance_rate_percent"),
    ):
        statistics = summary[kind]
        rate = statistics[metric]
        value = f"{rate:.2f}%" if rate is not None else "нет успешных проверок"
        mistakes = (
            statistics["rejected"] if kind == "genuine" else statistics["accepted"]
        )
        print(f"{label}: {value} ({mistakes}/{statistics['evaluated']})")
        print(
            f"  Ошибок обработки: {statistics['errors']}; пропущено: {statistics['skipped']}"
        )

    if not summary["complete"]:
        print(
            "Прогон неполный: FRR и FAR рассчитаны только по полученным решениям сервиса."
        )
