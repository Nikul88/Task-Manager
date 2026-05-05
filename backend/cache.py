"""
cache.py – In-memory TTL cache using cachetools.
Provides fast retrieval for dashboard stats, project members, and user profiles.
Cache is invalidated on write operations (tasks create/update, member changes).
"""
from cachetools import TTLCache
from threading import Lock

# ── Cache instances ───────────────────────────────────────────────────────────
# Each cache key is prefixed with the user/project ID

# Dashboard stats: TTL 30 seconds (refreshed quickly after task changes)
_dashboard_cache: TTLCache = TTLCache(maxsize=512, ttl=30)
_dashboard_lock = Lock()

# Project members list: TTL 60 seconds
_members_cache: TTLCache = TTLCache(maxsize=512, ttl=60)
_members_lock = Lock()

# User profile by ID: TTL 5 minutes
_user_cache: TTLCache = TTLCache(maxsize=1024, ttl=300)
_user_lock = Lock()

# Projects list per user: TTL 30 seconds
_projects_cache: TTLCache = TTLCache(maxsize=512, ttl=30)
_projects_lock = Lock()


# ── Dashboard cache ───────────────────────────────────────────────────────────

def get_dashboard_cache(user_id: int):
    with _dashboard_lock:
        return _dashboard_cache.get(f"dashboard:{user_id}")


def set_dashboard_cache(user_id: int, data: dict):
    with _dashboard_lock:
        _dashboard_cache[f"dashboard:{user_id}"] = data


def invalidate_dashboard_cache(user_id: int):
    with _dashboard_lock:
        _dashboard_cache.pop(f"dashboard:{user_id}", None)


def invalidate_all_dashboard_cache():
    """Called when task or project changes affect multiple users."""
    with _dashboard_lock:
        _dashboard_cache.clear()


# ── Members cache ─────────────────────────────────────────────────────────────

def get_members_cache(project_id: int):
    with _members_lock:
        return _members_cache.get(f"members:{project_id}")


def set_members_cache(project_id: int, data: list):
    with _members_lock:
        _members_cache[f"members:{project_id}"] = data


def invalidate_members_cache(project_id: int):
    with _members_lock:
        _members_cache.pop(f"members:{project_id}", None)


# ── User cache ────────────────────────────────────────────────────────────────

def get_user_cache(user_id: int):
    with _user_lock:
        return _user_cache.get(f"user:{user_id}")


def set_user_cache(user_id: int, data: dict):
    with _user_lock:
        _user_cache[f"user:{user_id}"] = data


def invalidate_user_cache(user_id: int):
    with _user_lock:
        _user_cache.pop(f"user:{user_id}", None)


# ── Projects cache ────────────────────────────────────────────────────────────

def get_projects_cache(user_id: int):
    with _projects_lock:
        return _projects_cache.get(f"projects:{user_id}")


def set_projects_cache(user_id: int, data: list):
    with _projects_lock:
        _projects_cache[f"projects:{user_id}"] = data


def invalidate_projects_cache(user_id: int):
    with _projects_lock:
        _projects_cache.pop(f"projects:{user_id}", None)


def invalidate_all_projects_cache():
    with _projects_lock:
        _projects_cache.clear()
