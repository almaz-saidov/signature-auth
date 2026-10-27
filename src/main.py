import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.router import router as api_router
from core.config import settings
from core.exceptions.handlers import request_validation_exception_handler

app = FastAPI()

app.exception_handler(RequestValidationError)(request_validation_exception_handler)

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.SERVER_HOST, port=settings.SERVER_PORT)
