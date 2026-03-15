from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.tasks import router as tasks_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(tasks_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
