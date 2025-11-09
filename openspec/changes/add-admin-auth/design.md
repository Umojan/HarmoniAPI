# Design: Admin Authentication System

## Architecture

### Module Structure
```
src/modules/admin/
├── models.py       # Admin SQLAlchemy model
├── schemas.py      # Login/register request/response schemas
├── exceptions.py   # AdminAuthException, AdminNotFoundException
├── service.py      # Authentication logic, admin CRUD
└── routes.py       # /auth/login, /auth/register endpoints
```

### Authentication Flow

**Login:**
1. POST `/auth/login` with email + password
2. Verify credentials via `AdminService.authenticate()`
3. Issue JWT with `sub: admin.id` claim
4. Return access token

**Endpoint Protection:**
1. Endpoint uses `Depends(get_current_admin)` dependency
2. Dependency extracts JWT from `Authorization: Bearer <token>` header
3. Decode token, fetch admin from DB by ID
4. Raise 401 if invalid/missing token or admin not found

**Admin Registration:**
1. POST `/auth/register` requires `Depends(get_current_admin)` (only admins can create admins)
2. Create new admin with hashed password
3. Return created admin (exclude password hash)

### First Admin Seeding

**Startup hook** (in `src/main.py` lifespan):
```python
async with get_session() as session:
    admin_service = AdminService(session)
    await admin_service.ensure_first_admin(
        email=settings.first_admin_email,
        password=settings.first_admin_password
    )
```

Checks if any admin exists; creates first admin if DB empty.

## Data Model

```python
class Admin(Base, BaseMixin):
    __tablename__ = "admins"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    # Inherits: id (UUID), created_at, updated_at
```

## Configuration

New settings in `Settings` class:
```python
first_admin_email: str
first_admin_password: str
```

New env vars in `.env.example`:
```env
FIRST_ADMIN_EMAIL=admin@harmoni.com
FIRST_ADMIN_PASSWORD=change-me-in-production
```

## Security Considerations

- Passwords hashed with bcrypt (existing `get_password_hash()`)
- JWT signed with `SECRET_KEY` from settings (HS256)
- Token expiration: `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30min)
- No refresh tokens (keep simple; re-login on expiry)
- First admin password stored in env (must use secure values in production)

## Trade-offs

**Simplicity choices:**
- Single admin role (no superadmin/moderator hierarchy)
- No password reset (admin can create new account if locked out)
- Stateless JWT (no session revocation; token valid until expiry)
- No email verification (trust admin who creates account)

