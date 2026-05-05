# Team Task Manager - Project README

## 1) Project Overview

This is a full-stack Team Task Manager application with:
- Backend: FastAPI + SQLAlchemy + MySQL
- Frontend: Angular (standalone components)
- Authentication: JWT + OTP verification flow
- Roles: Admin and Member

Purpose:
- Admins can create and assign tasks.
- Members can view/update assigned tasks and project progress.

## 2) Tech Stack

Backend:
- Python 3.11
- FastAPI
- SQLAlchemy ORM
- PyMySQL
- JWT (python-jose)

Frontend:
- Angular 21
- TypeScript
- CSS (custom dark theme)

Deployment:
- Railway (separate backend and frontend services)
- Frontend runtime config via env.js

## 3) Folder Structure

- `backend/`
  - `main.py` -> FastAPI app entry
  - `database.py` -> DB connection and session
  - `models.py` -> SQLAlchemy models
  - `routers/` -> auth, projects, tasks, dashboard routes
  - `seed_demo_users.py` -> creates admin/demo users
  - `Dockerfile` -> backend Railway container

- `frontend/`
  - `src/` -> Angular source code
  - `public/env.js` -> local API config
  - `Dockerfile` -> frontend Railway container
  - `env.js.template` -> runtime API_URL injection

- `DEPLOY_RAILWAY.md` -> deployment instructions
- `readme.txt` -> text-format README
- `deploy_readme.md` -> markdown README

## 4) Core Workflow (Application)

### A) Authentication Workflow
1. User signs up with name, email, password.
2. Backend creates unverified user and sends OTP email.
3. User verifies OTP.
4. Backend marks user verified and returns JWT token.
5. Frontend stores token and user info.
6. Protected routes are unlocked based on auth guard.

### B) Login Workflow
1. User logs in with email/password.
2. Backend validates credentials and verification status.
3. JWT token is returned.
4. Frontend attaches token via auth interceptor for API calls.

### C) Role Workflow
1. Admin users can create tasks and assign them.
2. Member users have limited non-admin access.
3. Backend enforces permissions for protected actions.

### D) Dashboard Workflow
1. Frontend requests `/api/dashboard`.
2. Backend returns summary stats + recent tasks.
3. Frontend renders progress cards, task list, and state badges.

## 5) Local Development Workflow

Backend:
1. `cd backend`
2. `pip install -r requirements.txt`
3. Set environment variables in `backend/.env`
4. `uvicorn main:app --reload --port 8000`

Frontend:
1. `cd frontend`
2. `npm install`
3. `npm start`
4. Open `http://localhost:4200`

## 6) Railway Deployment Workflow

This project is deployed as 2 services:

### Service 1: Backend
- Root directory: `backend`
- Uses `backend/Dockerfile`
- Expose public domain
- Required variables:
  - `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
  - `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_NAME`
  - `OTP_EXPIRE_MINUTES`, `FRONTEND_URL`

### Service 2: Frontend
- Root directory: `frontend`
- Uses `frontend/Dockerfile`
- Expose public domain
- Required variable:
  - `API_URL=https://<backend-domain>/api`

Important:
- Keep `FRONTEND_URL` on backend set to deployed frontend domain.
- Keep `API_URL` on frontend set to deployed backend `/api` URL.

## 7) Test Users (for demo/testing)

Use backend script:
- `python seed_demo_users.py`

Generated users:
- Admin:
  - email: `admin@taskflow.com`
  - password: `Admin@12345`
- Demo Member:
  - email: `demo@taskflow.com`
  - password: `Demo@12345`

## 8) Submission Notes

- Frontend and backend are containerized for Railway.
- Runtime API configuration is handled using `env.js`.
- CORS is configurable through `FRONTEND_URL`.
- App supports end-to-end testing with seeded users.
