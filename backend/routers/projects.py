"""
routers/projects.py – Project management REST API endpoints.

GET    /api/projects                    – List user's projects
POST   /api/projects                    – Create project
GET    /api/projects/{id}               – Get project details + members
PUT    /api/projects/{id}               – Update project (project admin)
DELETE /api/projects/{id}               – Delete project (project admin)
GET    /api/projects/{id}/members       – List members (cached)
POST   /api/projects/{id}/members       – Add member by email
DELETE /api/projects/{id}/members/{uid} – Remove member
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import cache
from auth import get_current_user
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/projects", tags=["Projects"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_project_or_404(project_id: int, db: Session) -> models.Project:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_membership(project_id: int, user_id: int, db: Session):
    return (
        db.query(models.ProjectMember)
        .filter(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == user_id,
        )
        .first()
    )


def _require_project_access(project: models.Project, current_user: models.User, db: Session):
    """Ensure user is owner or member of the project."""
    if current_user.role == models.UserRole.admin:
        return
    if project.owner_id == current_user.id:
        return
    membership = _get_membership(project.id, current_user.id, db)
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied to this project")


def _require_project_admin(project: models.Project, current_user: models.User, db: Session):
    """Ensure user is global admin."""
    if current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Global admin access required")


def _build_project_out(project: models.Project) -> schemas.ProjectOut:
    return schemas.ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        owner_name=project.owner.name if project.owner else "",
        created_at=project.created_at,
        member_count=len(project.members),
        task_count=len(project.tasks),
    )


def _build_member_out(m: models.ProjectMember) -> schemas.MemberOut:
    return schemas.MemberOut(
        id=m.id,
        user_id=m.user_id,
        user_name=m.user.name if m.user else "",
        user_email=m.user.email if m.user else "",
        role=m.role.value,
        joined_at=m.joined_at,
    )


# ── GET /api/projects ─────────────────────────────────────────────────────────

@router.get("", response_model=List[schemas.ProjectOut])
def list_projects(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Try cache
    cached = cache.get_projects_cache(current_user.id)
    if cached is not None:
        return cached

    if current_user.role == models.UserRole.admin:
        all_projects = db.query(models.Project).order_by(models.Project.created_at.desc()).all()
        result = [_build_project_out(p) for p in all_projects]
        cache.set_projects_cache(current_user.id, result)
        return result

    # Projects where user is owner
    owned = db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()
    # Projects where user is a member
    memberships = (
        db.query(models.ProjectMember)
        .filter(models.ProjectMember.user_id == current_user.id)
        .all()
    )
    member_project_ids = {m.project_id for m in memberships}
    member_projects = (
        db.query(models.Project)
        .filter(
            models.Project.id.in_(member_project_ids),
            models.Project.owner_id != current_user.id,
        )
        .all()
    )

    all_projects = owned + member_projects
    result = [_build_project_out(p) for p in all_projects]
    cache.set_projects_cache(current_user.id, result)
    return result


# ── POST /api/projects ────────────────────────────────────────────────────────

@router.post("", response_model=schemas.ProjectOut, status_code=201)
def create_project(
    body: schemas.ProjectCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Only global admins can create projects")

    project = models.Project(
        name=body.name,
        description=body.description,
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Auto-add owner as admin member
    membership = models.ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role=models.ProjectMemberRole.admin,
    )
    db.add(membership)
    db.commit()
    db.refresh(project)

    cache.invalidate_projects_cache(current_user.id)
    cache.invalidate_all_dashboard_cache()
    return _build_project_out(project)


# ── GET /api/projects/{id} ────────────────────────────────────────────────────

@router.get("/{project_id}", response_model=schemas.ProjectDetailOut)
def get_project(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(project_id, db)
    _require_project_access(project, current_user, db)

    members = _get_cached_members(project_id, db)
    return schemas.ProjectDetailOut(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        owner_name=project.owner.name if project.owner else "",
        created_at=project.created_at,
        members=members,
    )


# ── PUT /api/projects/{id} ────────────────────────────────────────────────────

@router.put("/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: int,
    body: schemas.ProjectUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(project_id, db)
    _require_project_admin(project, current_user, db)

    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description

    db.commit()
    db.refresh(project)
    cache.invalidate_all_projects_cache()
    return _build_project_out(project)


# ── DELETE /api/projects/{id} ─────────────────────────────────────────────────

@router.delete("/{project_id}", response_model=schemas.MessageResponse)
def delete_project(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(project_id, db)
    _require_project_admin(project, current_user, db)

    db.delete(project)
    db.commit()
    cache.invalidate_all_projects_cache()
    cache.invalidate_members_cache(project_id)
    cache.invalidate_all_dashboard_cache()
    return {"message": "Project deleted successfully"}


# ── GET /api/projects/{id}/members ───────────────────────────────────────────

@router.get("/{project_id}/members", response_model=List[schemas.MemberOut])
def list_members(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(project_id, db)
    _require_project_access(project, current_user, db)
    return _get_cached_members(project_id, db)


# ── POST /api/projects/{id}/members ──────────────────────────────────────────

@router.post("/{project_id}/members", response_model=schemas.MemberOut, status_code=201)
def add_member(
    project_id: int,
    body: schemas.AddMemberRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(project_id, db)
    _require_project_admin(project, current_user, db)

    # Find user by email
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found with that email")
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="User has not verified their email")

    # Check if already a member
    existing = _get_membership(project_id, user.id, db)
    if existing:
        raise HTTPException(status_code=409, detail="User is already a project member")

    role = models.ProjectMemberRole(body.role)
    membership = models.ProjectMember(
        project_id=project_id,
        user_id=user.id,
        role=role,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)

    cache.invalidate_members_cache(project_id)
    cache.invalidate_projects_cache(user.id)
    return _build_member_out(membership)


# ── DELETE /api/projects/{id}/members/{uid} ───────────────────────────────────

@router.delete("/{project_id}/members/{user_id}", response_model=schemas.MessageResponse)
def remove_member(
    project_id: int,
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(project_id, db)
    _require_project_admin(project, current_user, db)

    if user_id == project.owner_id:
        raise HTTPException(status_code=400, detail="Cannot remove the project owner")

    membership = _get_membership(project_id, user_id, db)
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found in this project")

    db.delete(membership)
    db.commit()

    cache.invalidate_members_cache(project_id)
    cache.invalidate_projects_cache(user_id)
    return {"message": "Member removed successfully"}


# ── Internal ──────────────────────────────────────────────────────────────────

def _get_cached_members(project_id: int, db: Session) -> List[schemas.MemberOut]:
    cached = cache.get_members_cache(project_id)
    if cached is not None:
        return cached

    memberships = (
        db.query(models.ProjectMember)
        .filter(models.ProjectMember.project_id == project_id)
        .all()
    )
    result = [_build_member_out(m) for m in memberships]
    cache.set_members_cache(project_id, result)
    return result
