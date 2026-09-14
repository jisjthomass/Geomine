# Authentication Module

## Architecture

This project uses a JWT (JSON Web Token) authentication system backed by PostgreSQL and Argon2 password hashing. The components are as follows:

- **Frontend**: Streamlit dashboard wrapper checks for `st.session_state["authenticated"]`. If not set, it intercepts the dashboard and displays a login screen. On login, it calls the backend `/api/auth/login` endpoint, retrieves a JWT, and stores it in the session state.
- **Backend API**: FastAPI implements standard `OAuth2` bearer token authentication (using `HTTPBearer`). 
- **Database**: PostgreSQL `users` table tracks credentials and role.

## Protected Endpoints

The following routes are secured and require a valid Bearer token in the `Authorization` header:

- `POST /api/analyze_risk`
- `POST /api/generate_ai_summary`
- `POST /api/search_knowledge`
- `POST /api/ingest_report`
- `POST /api/upload_report`
- `PATCH /api/ocr_correction`
- `POST /api/analyze_npt`
- `POST /api/mitigation/queue`
- `GET /api/mitigation/pending`
- `POST /api/mitigation/approve/{queue_id}`
- `POST /api/environmental_risk`

The telemetry WebSocket (`/ws/telemetry/{well_id}`) and health check (`/`) remain public for live operation compatibility in this prototype phase.

## Creating a Local Demo User

You can create an initial admin or demo user via a secure interactive script on the backend (or locally if dependencies are installed):

```bash
docker exec -it geomine_backend python scripts/create_auth_user.py --username demo --role engineer
```
(You will be securely prompted to type a password).

## Database Schema (05_authentication.sql)

The system automatically initializes an idempotent `users` table via Docker `entrypoint-initdb`.
It uses Argon2 hashing via `pwdlib` to prevent plaintext storage of passwords.

## Local Development & Configuration

The system enforces the presence of a strong secret for signing JWTs. You **must** set the environment variable `JWT_SECRET_KEY`.

### Setup Instructions

1. Copy the template to create your local environment file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and generate a strong random string for `JWT_SECRET_KEY`.
3. Do **not** commit `.env` to version control (it is ignored by Git).
4. Docker Compose will automatically use the `JWT_SECRET_KEY` from your local `.env` environment.

If `JWT_SECRET_KEY` is absent, the backend server will refuse to start and fail with a loud runtime error.

## Testing

Comprehensive unit tests are provided in `tests/test_auth.py`. 
To run tests via Docker:
```bash
docker exec geomine_backend pytest tests/test_auth.py
```

## Limitations

> [!WARNING]
> This is a functional prototype authentication layer designed for the SIH project requirements. It does not include enterprise features such as SSO, OAuth integrations (Google/Microsoft), MFA, or email verification flows.
