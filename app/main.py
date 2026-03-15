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


@app.get("/todos", response_model=list[Todo])
def list_todos() -> list[Todo]:
    return store.list()


@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(payload: TodoCreate) -> Todo:
    return store.create(payload)


@app.get("/todos/{item_id}", response_model=Todo)
def get_todo(item_id: int) -> Todo:
    return store.get(item_id)


@app.put("/todos/{item_id}", response_model=Todo)
def update_todo(item_id: int, payload: TodoCreate) -> Todo:
    return store.update(item_id, payload)


@app.delete("/todos/{item_id}", status_code=204)
def delete_todo(item_id: int) -> None:
    store.delete(item_id)
