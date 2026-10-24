from fastapi import APIRouter

from api.v1.signature_reference import router as signature_reference_router
from api.v1.user import router as user_router

router = APIRouter(prefix="/v1")

router.include_router(user_router)
router.include_router(signature_reference_router)
