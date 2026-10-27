class BaseSignatureException(Exception):
    default_detail: str = "Ошибка обработки подписи."

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(self.default_detail if detail is None else detail)


class InvalidSignatureSampleException(BaseSignatureException):
    default_detail = "Образец подписи непригоден для обработки."


class ReferenceFormationException(BaseSignatureException):
    default_detail = "Не удалось сформировать эталон подписи."


class SignatureVerificationException(BaseSignatureException):
    default_detail = "Не удалось выполнить сравнение подписи с эталоном."
