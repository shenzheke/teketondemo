from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=500)


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    detail: str = Field(default="", max_length=1000)
    priority: int = Field(default=3, ge=1, le=5)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    detail: str | None = Field(default=None, max_length=1000)
    priority: int | None = Field(default=None, ge=1, le=5)
    status: str | None = Field(default=None, pattern="^(todo|in_progress|done)$")


class TaskOut(BaseModel):
    id: int
    title: str
    detail: str
    status: str
    priority: int
    project_id: int
    assignee_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
