"""
routers/tasks.py – Task management REST API endpoints.

GET    /api/tasks           – List tasks (filtered by project/assignee/status)
POST   /api/tasks           – Create task (project admin)
GET    /api/tasks/{id}      – Get single task
PUT    /api/tasks/{id}      – Full update (project admin)
PATCH  /api/tasks/{id}/status – Update status only (any member)
DELETE /api/tasks/{id}      – Delete task (project admin)
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import cache
from auth import get_current_user
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_task_or_404(task_id: int, db: Session) -> models.Task:
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _user_in_project(project_id: int, user_id: int, db: Session) -> Optional[models.ProjectMember]:
    return (
        db.query(models.ProjectMember)
        .filter(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == user_id,
        )
        .first()
    )


def _require_task_access(task: models.Task, current_user: models.User, db: Session):
    if current_user.role == models.UserRole.admin:
        return
    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id == current_user.id:
        return
    membership = _user_in_project(task.project_id, current_user.id, db)
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")


def _require_task_admin(task: models.Task, current_user: models.User, db: Session):
    if current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Global admin access required")


def _build_task_out(task: models.Task) -> schemas.TaskOut:
    now = datetime.now(timezone.utc)
    due = task.due_date
    if due and due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    is_overdue = bool(due and now > due and task.status != models.TaskStatus.done)

    return schemas.TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value if task.status else "todo",
        priority=task.priority.value if task.priority else "medium",
        due_date=task.due_date,
        project_id=task.project_id,
        project_name=task.project.name if task.project else None,
        assignee_id=task.assignee_id,
        assignee_name=task.assignee.name if task.assignee else None,
        created_by=task.created_by,
        creator_name=task.creator.name if task.creator else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
        is_overdue=is_overdue,
    )


# ── GET /api/tasks ────────────────────────────────────────────────────────────

@router.get("", response_model=List[schemas.TaskOut])
def list_tasks(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    assignee_id: Optional[int] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == models.UserRole.admin:
        query = db.query(models.Task)
        if project_id:
            query = query.filter(models.Task.project_id == project_id)
        if status:
            query = query.filter(models.Task.status == status)
        if assignee_id:
            query = query.filter(models.Task.assignee_id == assignee_id)
        tasks = query.order_by(models.Task.created_at.desc()).all()
        return [_build_task_out(t) for t in tasks]

    # Get all projects user has access to
    owned_ids = {
        p.id
        for p in db.query(models.Project)
        .filter(models.Project.owner_id == current_user.id)
        .all()
    }
    member_ids = {
        m.project_id
        for m in db.query(models.ProjectMember)
        .filter(models.ProjectMember.user_id == current_user.id)
        .all()
    }
    accessible_ids = owned_ids | member_ids

    query = db.query(models.Task).filter(models.Task.project_id.in_(accessible_ids))

    if project_id:
        if project_id not in accessible_ids:
            raise HTTPException(status_code=403, detail="Access denied to this project")
        query = query.filter(models.Task.project_id == project_id)

    if status:
        query = query.filter(models.Task.status == status)

    if assignee_id:
        query = query.filter(models.Task.assignee_id == assignee_id)

    tasks = query.order_by(models.Task.created_at.desc()).all()
    return [_build_task_out(t) for t in tasks]


# ── POST /api/tasks ───────────────────────────────────────────────────────────

@router.post("", response_model=schemas.TaskOut, status_code=201)
def create_task(
    body: schemas.TaskCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(models.Project).filter(models.Project.id == body.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Only global admins can create tasks
    if current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins can create tasks")

    # Validate assignee is in project if provided
    if body.assignee_id:
        assignee_member = _user_in_project(body.project_id, body.assignee_id, db)
        assignee_owner = project.owner_id == body.assignee_id
        if not assignee_member and not assignee_owner:
            raise HTTPException(status_code=400, detail="Assignee is not a member of this project")

    task = models.Task(
        title=body.title,
        description=body.description,
        status=models.TaskStatus(body.status),
        priority=models.TaskPriority(body.priority),
        due_date=body.due_date,
        project_id=body.project_id,
        assignee_id=body.assignee_id,
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    cache.invalidate_all_dashboard_cache()
    return _build_task_out(task)


# ── GET /api/tasks/{id} ───────────────────────────────────────────────────────

@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = _get_task_or_404(task_id, db)
    _require_task_access(task, current_user, db)
    return _build_task_out(task)


# ── PUT /api/tasks/{id} ───────────────────────────────────────────────────────

@router.put("/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    body: schemas.TaskUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = _get_task_or_404(task_id, db)
    _require_task_admin(task, current_user, db)

    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    if body.status is not None:
        task.status = models.TaskStatus(body.status)
    if body.priority is not None:
        task.priority = models.TaskPriority(body.priority)
    if body.due_date is not None:
        task.due_date = body.due_date
    if body.assignee_id is not None:
        task.assignee_id = body.assignee_id

    db.commit()
    db.refresh(task)
    cache.invalidate_all_dashboard_cache()
    return _build_task_out(task)


# ── PATCH /api/tasks/{id}/status ─────────────────────────────────────────────

@router.patch("/{task_id}/status", response_model=schemas.TaskOut)
def update_task_status(
    task_id: int,
    body: schemas.TaskStatusUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = _get_task_or_404(task_id, db)
    _require_task_access(task, current_user, db)  # Any member can update status

    task.status = models.TaskStatus(body.status)
    db.commit()
    db.refresh(task)

    cache.invalidate_dashboard_cache(current_user.id)
    if task.assignee_id and task.assignee_id != current_user.id:
        cache.invalidate_dashboard_cache(task.assignee_id)

    return _build_task_out(task)


# ── DELETE /api/tasks/{id} ────────────────────────────────────────────────────

@router.delete("/{task_id}", response_model=schemas.MessageResponse)
def delete_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = _get_task_or_404(task_id, db)
    _require_task_admin(task, current_user, db)

    db.delete(task)
    db.commit()
    cache.invalidate_all_dashboard_cache()
    return {"message": "Task deleted successfully"}
