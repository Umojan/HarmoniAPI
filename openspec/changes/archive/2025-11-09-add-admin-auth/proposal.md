# Proposal: Add Admin Authentication

## Overview

Add OAuth2-based admin authentication with JWT tokens. First admin auto-created from env vars, subsequent admins registered by existing admins.

## Motivation

Platform requires admin access control for managing tariffs, orders, and customer inquiries. Simple email/password auth with role-based endpoint protection.

## Scope

**In scope:**
- Admin model (email, hashed password, optional first/last name)
- OAuth2 password flow with JWT
- Admin registration endpoint (protected, requires existing admin)
- Login endpoint (public)
- Dependency for protecting admin-only endpoints
- First admin seeded from `FIRST_ADMIN_EMAIL` and `FIRST_ADMIN_PASSWORD` env vars

**Out of scope:**
- Password reset flows
- Multi-factor authentication
- Role hierarchies beyond single "admin" role
- Session management (stateless JWT only)
- Admin deactivation/soft-delete

## Capabilities

1. **admin-authentication** — Login, token issuance, endpoint protection
2. **admin-management** — Admin creation, first admin seeding

## Dependencies

- Existing `src/core/security.py` (JWT + bcrypt helpers)
- SQLAlchemy async setup in `src/db/`
- Pydantic settings in `src/core/settings.py`

## Risks

- **First admin security**: Env vars must be strong; no validation beyond non-empty check
- **No password complexity enforcement**: Accept any password (simplicity over policy)

## Success Criteria

- First admin created on app startup if not exists
- Admins can log in and receive JWT
- Protected endpoints reject non-admin requests with 401
- New admins registered only by authenticated admins
