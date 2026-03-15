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
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict

app = FastAPI(title="tekton-demo-api", version="1.0.0")


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    done: bool = False


class Todo(TodoCreate):
    id: int


class TodoStore:
    def __init__(self) -> None:
        self._items: Dict[int, Todo] = {}
        self._next_id: int = 1

    def list(self) -> list[Todo]:
        return list(self._items.values())

    def create(self, payload: TodoCreate) -> Todo:
        item = Todo(id=self._next_id, **payload.model_dump())
        self._items[item.id] = item
        self._next_id += 1
        return item

    def get(self, item_id: int) -> Todo:
        if item_id not in self._items:
            raise HTTPException(status_code=404, detail="todo not found")
        return self._items[item_id]

    def update(self, item_id: int, payload: TodoCreate) -> Todo:
        if item_id not in self._items:
            raise HTTPException(status_code=404, detail="todo not found")
        updated = Todo(id=item_id, **payload.model_dump())
        self._items[item_id] = updated
        return updated

    def delete(self, item_id: int) -> None:
        if item_id not in self._items:
            raise HTTPException(status_code=404, detail="todo not found")
        del self._items[item_id]


store = TodoStore()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
