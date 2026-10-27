from pydantic import Field

from core.config import settings
from schemas.base import BaseSchema


class PaginationFiltersSchema(BaseSchema):
    page: int = Field(default=1, ge=1)
    size: int = Field(
        default=settings.PAGINATION_DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.PAGINATION_MAX_PAGE_SIZE,
    )


class PaginatedSchema[T](BaseSchema):
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1, le=settings.PAGINATION_MAX_PAGE_SIZE)
    data: list[T]
