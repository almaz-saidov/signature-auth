from typing import Any

from sqlalchemy import Executable, Result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions.database import DatabaseException


class BaseDatabaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _execute(self, statement: Executable) -> Result[Any]:
        try:
            return await self._session.execute(statement)
        except SQLAlchemyError as error:
            raise DatabaseException() from error

    async def _flush(self) -> None:
        try:
            await self._session.flush()
        except SQLAlchemyError as error:
            raise DatabaseException() from error
