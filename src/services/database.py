from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions.database import DatabaseException
from database.repositories.base import BaseDatabaseRepository


class DatabaseService[RepositoryT: BaseDatabaseRepository]:
    def __init__(self, repository: RepositoryT, session: AsyncSession) -> None:
        self._repository = repository
        self._session = session

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except SQLAlchemyError as error:
            raise DatabaseException() from error

    async def _rollback(self) -> None:
        try:
            await self._session.rollback()
        except SQLAlchemyError as error:
            raise DatabaseException() from error
