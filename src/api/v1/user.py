from fastapi import APIRouter, Body, HTTPException, status

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
    response_model=None,
    summary="Зарегистрировать пользователя сервиса",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Пользователь создан; возвращаются его метаданные и API-ключ",
        },
        status.HTTP_409_CONFLICT: {"description": "Имя пользователя уже занято"},
    },
)
async def register_user(
    username: str = Body(..., embed=True, min_length=1),
) -> None:
    """Регистрация интегратора без API-ключа.

    Выданный API-ключ возвращается один раз. В БД будет храниться только хеш.
    Статус is_active может менять только владелец сервиса, вне этого API.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Регистрация пользователя пока не реализована",
    )


@router.post(
    "/me/api-key",
    status_code=status.HTTP_200_OK,
    response_model=None,
    summary="Перевыпустить API-ключ",
    responses={
        status.HTTP_200_OK: {
            "description": "Возвращаются новый API-ключ и время выдачи"
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "API-ключ отсутствует или неверен"
        },
        status.HTTP_403_FORBIDDEN: {"description": "Пользователь сервиса отключён"},
    },
)
async def rotate_api_key() -> None:
    """Перевыпуск ключа текущего пользователя сервиса.

    Требуется Authorization: Bearer <api_key> с действующим ключом.
    После успешной замены старый ключ перестаёт действовать.
    Новый ключ возвращается один раз. Тело запроса не требуется.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Перевыпуск API-ключа пока не реализован",
    )
