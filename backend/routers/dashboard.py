"""
routers/dashboard.py – Dashboard statistics endpoint (in-memory cached).

GET /api/dashboard – Returns task stats for the current user.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import cache
from auth import get_current_user
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("", response_model=schemas.DashboardStats)
def get_dashboard(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ── Try cache first ────────────────────────────────────────────────────
    cached = cache.get_dashboard_cache(current_user.id)
    if cached is not None:
        return cached

    # ── Query tasks assigned to current user ───────────────────────────────
    tasks = (
        db.query(models.Task)
        .filter(models.Task.assignee_id == current_user.id)
        .all()
    )

    now = datetime.now(timezone.utc)
    total = len(tasks)
    todo_count = 0
    in_progress_count = 0
    done_count = 0
    overdue_count = 0
    task_outs = []

    for t in tasks:
        status_val = t.status.value if t.status else "todo"
        if status_val == "todo":
            todo_count += 1
        elif status_val == "in_progress":
            in_progress_count += 1
        elif status_val == "done":
            done_count += 1

        due = t.due_date
        if due:
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if now > due and status_val != "done":
                overdue_count += 1

        is_overdue = bool(
            t.due_date
            and now > (t.due_date.replace(tzinfo=timezone.utc) if t.due_date.tzinfo is None else t.due_date)
            and status_val != "done"
        )
        task_outs.append(
            schemas.TaskOut(
                id=t.id,
                title=t.title,
                description=t.description,
                status=status_val,
                priority=t.priority.value if t.priority else "medium",
                due_date=t.due_date,
                project_id=t.project_id,
                project_name=t.project.name if t.project else None,
                assignee_id=t.assignee_id,
                assignee_name=t.assignee.name if t.assignee else None,
                created_by=t.created_by,
                creator_name=t.creator.name if t.creator else None,
                created_at=t.created_at,
                updated_at=t.updated_at,
                is_overdue=is_overdue,
            )
        )

    # Return 5 most recent tasks on dashboard
    recent = sorted(task_outs, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]

    result = schemas.DashboardStats(
        total_tasks=total,
        todo=todo_count,
        in_progress=in_progress_count,
        done=done_count,
        overdue=overdue_count,
        recent_tasks=recent,
    )

    # ── Store in cache ────────────────────────────────────────────────────
    cache.set_dashboard_cache(current_user.id, result)
    return result
