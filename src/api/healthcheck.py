from fastapi import APIRouter, status

router = APIRouter(prefix="/healthcheck")


@router.get("", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def healthcheck() -> None: ...
