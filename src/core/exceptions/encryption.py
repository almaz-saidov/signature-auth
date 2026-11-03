class EncryptionException(Exception):
    def __init__(self) -> None:
        super().__init__("Ошибка работы с криптографией.")
