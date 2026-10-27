from typing import Any

from fastapi import HTTPException, status


class BaseHTTPException(HTTPException):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail: str = "Внутренняя ошибка сервера."

    def __init__(
        self,
        detail: str | dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            status_code=self.status_code,
            detail=self.default_detail if detail is None else detail,
            headers=headers,
        )


class UnauthorizedException(BaseHTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = (
        "Требуется действующий API-ключ в заголовке Authorization: Bearer <api_key>."
    )

    def __init__(
        self,
        detail: str | dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"} if headers is None else headers,
        )


class ForbiddenException(BaseHTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Доступ запрещён."


class NotFoundException(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Объект не найден."


class ConflictException(BaseHTTPException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Операция конфликтует с текущим состоянием данных."


class UnprocessableContentException(BaseHTTPException):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    default_detail = "Некорректные данные запроса."


class ServiceUnavailableException(BaseHTTPException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Сервис временно недоступен."


class NotImplementedHTTPException(BaseHTTPException):
    status_code = status.HTTP_501_NOT_IMPLEMENTED
    default_detail = "Операция пока не реализована."


class InactiveUserException(ForbiddenException):
    default_detail = "Пользователь сервиса отключён."


class UsernameAlreadyExistsException(ConflictException):
    default_detail = "Имя пользователя уже занято."


class SignatureReferenceNotFoundException(NotFoundException):
    default_detail = "Эталон не найден."


class InvalidSignatureException(UnprocessableContentException):
    default_detail = "Образцы подписи непригодны для обработки."
