from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, Project, User
from app.schemas import TaskCreate, TaskOut, TaskUpdate
from app.security import get_current_user

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


def _get_owned_project(db: Session, project_id: int, user_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    return project


@router.post("", response_model=TaskOut, status_code=201)
def create_task(
    project_id: int,
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    _get_owned_project(db, project_id, current_user.id)
    task = Task(
        title=payload.title,
        detail=payload.detail,
        priority=payload.priority,
        project_id=project_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(
    project_id: int,
    status_filter: str | None = Query(default=None, alias="status", pattern="^(todo|in_progress|done)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Task]:
    _get_owned_project(db, project_id, current_user.id)
    query = db.query(Task).filter(Task.project_id == project_id)
    if status_filter:
        query = query.filter(Task.status == status_filter)
    return query.order_by(Task.priority.asc(), Task.id.desc()).all()


@router.patch("/{task_id}", response_model=TaskOut)
def patch_task(
    project_id: int,
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    _get_owned_project(db, project_id, current_user.id)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="task not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task
