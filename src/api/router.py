from fastapi import APIRouter

from api.healthcheck import router as healthcheck_router
from api.v1.router import router as v1_router

router = APIRouter(prefix="/api")

router.include_router(healthcheck_router)
router.include_router(v1_router)
