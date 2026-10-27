from fastapi import APIRouter, Depends, status

from core.dependencies import get_current_user, get_user_service
from schemas.user import (
    ApiKeySchema,
    CreateUserPayloadSchema,
    RegisteredUserSchema,
    UserSchema,
)
from services.user import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        status.HTTP_501_NOT_IMPLEMENTED: {"description": "Эндпоинт пока не реализован"},
    },
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisteredUserSchema,
    summary="Зарегистрировать пользователя сервиса",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Пользователь создан; возвращаются его метаданные и API-ключ",
        },
        status.HTTP_409_CONFLICT: {"description": "Имя пользователя уже занято"},
    },
    description=(
        "Регистрация интегратора без API-ключа.\n"
        "\n"
        "Выданный API-ключ возвращается один раз. Сохраните его для последующих запросов."
    ),
)
async def register_user(
    payload: CreateUserPayloadSchema,
    service: UserService = Depends(get_user_service),
) -> RegisteredUserSchema:
    return await service.register(payload=payload)


@router.post(
    "/me/api-key",
    status_code=status.HTTP_200_OK,
    response_model=ApiKeySchema,
    summary="Перевыпустить API-ключ",
    responses={
        status.HTTP_200_OK: {
            "description": "Возвращаются новый API-ключ и время выдачи"
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "API-ключ отсутствует или неверен"
        },
        status.HTTP_403_FORBIDDEN: {"description": "Доступ запрещён"},
    },
    description=(
        "Перевыпуск ключа текущего пользователя сервиса.\n"
        "\n"
        "Требуется Authorization: Bearer <api_key> с действующим ключом.\n"
        "После успешной замены старый ключ перестаёт действовать.\n"
        "Новый ключ возвращается один раз. Тело запроса не требуется."
    ),
)
async def rotate_api_key(
    current_user: UserSchema = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> ApiKeySchema:
    return await service.rotate_api_key(user_id=current_user.id)
