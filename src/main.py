import uvicorn
from fastapi import FastAPI

from api.router import router as api_router
from core.config import settings

app = FastAPI()

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.SERVER_HOST, port=settings.SERVER_PORT)
