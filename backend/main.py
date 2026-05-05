"""
main.py – FastAPI application entry point.
- Registers all routers
- Initialises DB (code-first table creation) on startup
- Configures CORS for Angular dev server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

from database import init_db
from routers import auth, projects, tasks, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup: create all tables if they don't exist ────────────────────
    print("Initialising database (code-first)...")
    init_db()
    print("Database ready.")
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────
    print("Shutting down Team Task Manager API.")


app = FastAPI(
    title="Team Task Manager API",
    description="REST API for the Team Task Manager full-stack application.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
def _get_allowed_origins() -> list[str]:
    """
    Supports both:
    - FRONTEND_URL=https://your-frontend.up.railway.app
    - FRONTEND_URL=https://a.com,https://b.com
    """
    raw = os.getenv("FRONTEND_URL", "http://localhost:4200")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if "http://localhost:4200" not in origins:
        origins.append("http://localhost:4200")
    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Team Task Manager API is running 🚀"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
