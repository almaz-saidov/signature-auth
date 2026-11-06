from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from core.config import signature_settings
from core.dependencies import (
    get_current_user,
    get_signature_reference_service,
    get_signature_verification_service,
)
from schemas.pagination import PaginatedSchema
from schemas.signature_reference import (
    CreateSignatureReferencePayloadSchema,
    ListSignatureReferenceFiltersSchema,
    SignatureReferenceSchema,
    SignatureValidationResultSchema,
    VerifySignaturePayloadSchema,
)
from schemas.user import UserSchema
from services.signature_reference import SignatureReferenceService
from services.signature_verification import SignatureVerificationService

router = APIRouter(
    prefix="/signature-references",
    tags=["Signature References"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "API-ключ отсутствует или неверен"
        },
        status.HTTP_403_FORBIDDEN: {"description": "Доступ запрещён"},
    },
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UUID,
    summary="Создать или заменить эталон",
    responses={
        status.HTTP_200_OK: {
            "model": UUID,
            "description": "Эталон заменён; возвращается его UUID",
        },
        status.HTTP_201_CREATED: {
            "description": "Эталон создан; возвращается его UUID"
        },
    },
    description=(
        "Создание эталона по subject_id и десяти образцам из тела запроса.\n"
        "\n"
        "Владелец определяется по ключу. Если эталон уже существует, он заменяется.\n"
        "При ошибке обработки образцов существующий эталон сохраняется.\n"
        "Ответ содержит UUID эталона."
    ),
)
async def create_or_update_signature_reference(
    payload: CreateSignatureReferencePayloadSchema,
    response: Response,
    current_user: UserSchema = Depends(get_current_user),
    service: SignatureReferenceService = Depends(get_signature_reference_service),
) -> UUID:
    result = await service.create_or_update(user_id=current_user.id, payload=payload)
    response.status_code = (
        status.HTTP_201_CREATED if result.action == "created" else status.HTTP_200_OK
    )

    return result.reference_id


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedSchema[SignatureReferenceSchema],
    summary="Получить список своих эталонов",
    responses={
        status.HTTP_200_OK: {
            "description": "Страница метаданных эталонов: total, page, size, data"
        },
    },
    description=(
        "Список эталонов владельца ключа.\n"
        "\n"
        "subject_id фильтруется по точному совпадению; from и to — по дате created_at в UTC.\n"
        "Границы включительны. from не должен быть позже to (ошибка 422).\n"
        "Сортировка по created_at и id по убыванию.\n"
        "data — список метаданных эталонов.\n"
        "total — количество эталонов после фильтрации, до пагинации."
    ),
)
async def get_signature_references(
    filters: ListSignatureReferenceFiltersSchema = Query(),
    current_user: UserSchema = Depends(get_current_user),
    service: SignatureReferenceService = Depends(get_signature_reference_service),
) -> PaginatedSchema[SignatureReferenceSchema]:
    return await service.get_list(user_id=current_user.id, filters=filters)


@router.get(
    "/{reference_id}",
    status_code=status.HTTP_200_OK,
    response_model=SignatureReferenceSchema,
    summary="Получить метаданные эталона",
    responses={
        status.HTTP_200_OK: {
            "description": "Метаданные эталона: id, subject_id, created_at, updated_at"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Эталон не найден у текущего владельца"
        },
    },
    description=(
        "Метаданные собственного эталона.\n"
        "\n"
        "Для чужого и отсутствующего эталона возвращается одинаковый ответ 404."
    ),
)
async def get_signature_reference(
    reference_id: UUID,
    current_user: UserSchema = Depends(get_current_user),
    service: SignatureReferenceService = Depends(get_signature_reference_service),
) -> SignatureReferenceSchema:
    return await service.get_by_id(user_id=current_user.id, reference_id=reference_id)


@router.delete(
    "/{reference_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить эталон",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Эталон удалён; тело ответа отсутствует"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Эталон не найден у текущего владельца"
        },
    },
    description=(
        "Удаление собственного эталона. Чужой или отсутствующий эталон даёт 404.\n"
        "Повторное удаление того же эталона также возвращает 404."
    ),
)
async def delete_signature_reference(
    reference_id: UUID,
    current_user: UserSchema = Depends(get_current_user),
    service: SignatureReferenceService = Depends(get_signature_reference_service),
) -> None:
    await service.delete(user_id=current_user.id, reference_id=reference_id)


@router.post(
    "/{reference_id}/verifications",
    status_code=status.HTTP_200_OK,
    response_model=SignatureValidationResultSchema,
    summary="Сравнить образец с эталоном",
    responses={
        status.HTTP_200_OK: {
            "description": "Результат validated и score в процентах; несовпадение также даёт 200"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Эталон не найден у текущего владельца"
        },
    },
    description=(
        "Сравнение одного образца из тела запроса с собственным эталоном.\n"
        "\n"
        "Для чужого и отсутствующего эталона возвращается одинаковый ответ 404.\n"
        "Неподдерживаемая версия эталона даёт 422 с просьбой обновить эталон.\n"
        "score — степень соответствия от 0 до 100, не вероятность подлинности.\n"
        f"validated=true при score >= {signature_settings.VERIFICATION_THRESHOLD:g}.\n"
        "Интегратор может применить собственный порог к score.\n"
        "Ответ содержит только validated и score."
    ),
)
async def verify_signature(
    reference_id: UUID,
    payload: VerifySignaturePayloadSchema,
    current_user: UserSchema = Depends(get_current_user),
    service: SignatureVerificationService = Depends(get_signature_verification_service),
) -> SignatureValidationResultSchema:
    return await service.verify(
        user_id=current_user.id, reference_id=reference_id, sample=payload.sample
    )
