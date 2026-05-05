# Deploy on Railway (Backend + Frontend)

This repo should be deployed as **two Railway services**:

- `backend` (FastAPI)
- `frontend` (Angular + Nginx)

## 1) Push code to GitHub

Railway deploys from a GitHub repo. Push this project first.

## 2) Create Backend Service

1. In Railway, click **New Project** -> **Deploy from GitHub repo**.
2. Create a service from this repo and set **Root Directory** to:
   - `backend`
3. Railway will detect the `Dockerfile` and build automatically.

### Backend Environment Variables

Set these in Railway service variables:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `SECRET_KEY`
- `ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=1440`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM_NAME`
- `OTP_EXPIRE_MINUTES=10`
- `FRONTEND_URL` (set this after frontend is deployed)

Railway automatically provides `PORT`; no need to set it manually.

## 3) Create Frontend Service

1. Add another service from the same repo.
2. Set **Root Directory** to:
   - `frontend`
3. Railway uses the frontend `Dockerfile`.

### Frontend Environment Variables

- `API_URL=https://<your-backend-domain>/api`

Example:

- `API_URL=https://taskflow-api-production.up.railway.app/api`

## 4) Wire CORS

After frontend deploys, copy its public domain and set backend:

- `FRONTEND_URL=https://<your-frontend-domain>`

Then redeploy backend.

## 5) Validate Production

Check these URLs:

- Backend health: `https://<backend-domain>/health`
- Frontend app: `https://<frontend-domain>`

Login with your seeded users:

- Admin: `admin@taskflow.com` / `Admin@12345`
- Demo: `demo@taskflow.com` / `Demo@12345`

## Notes

- Frontend runtime config is loaded from `env.js`.
- Backend CORS supports one or multiple origins in `FRONTEND_URL` (comma-separated).
