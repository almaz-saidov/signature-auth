from database.repositories.base import BaseDatabaseRepository


class DatabaseService:
    def __init__(self, repository: BaseDatabaseRepository):
        self._repository = repository
