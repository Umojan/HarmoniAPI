# Tasks: Add Admin Authentication

## Implementation Order

1. **Add admin configuration to settings**
   - Add `first_admin_email: str` and `first_admin_password: str` to `Settings` class in `src/core/settings.py`
   - Update `.env.example` with `FIRST_ADMIN_EMAIL` and `FIRST_ADMIN_PASSWORD`
   - Validation: Settings load without error

2. **Create Admin model**
   - Define `Admin` model in `src/modules/admin/models.py` (email, hashed_password, first_name, last_name)
   - Register model in `src/db/all_models.py`
   - Validation: Model imports successfully

3. **Create admin schemas**
   - Define `LoginRequest`, `TokenResponse`, `RegisterRequest`, `AdminResponse` in `src/modules/admin/schemas.py`
   - Validation: Schemas import successfully

4. **Create admin exceptions**
   - Define `InvalidCredentialsException`, `AdminNotFoundException`, `AdminAlreadyExistsException` in `src/modules/admin/exceptions.py`
   - Validation: Exceptions inherit from `AppException`

5. **Implement AdminService**
   - Create `AdminService` in `src/modules/admin/service.py`
   - Methods: `authenticate()`, `create_admin()`, `get_admin_by_id()`, `get_admin_by_email()`, `ensure_first_admin()`
   - Use existing `verify_password()`, `get_password_hash()`, `create_access_token()` from `src/core/security.py`
   - Validation: Service methods have full type hints

6. **Create authentication dependency**
   - Add `get_current_admin()` dependency in `src/modules/admin/service.py` or `src/core/dependencies.py`
   - Extract JWT from `Authorization` header, decode, fetch admin
   - Validation: Dependency raises 401 for invalid tokens

7. **Implement auth routes**
   - Create `/auth/login` (POST, public) and `/auth/register` (POST, admin-only) in `src/modules/admin/routes.py`
   - Use `OAuth2PasswordRequestForm` for login compatibility
   - Validation: Routes follow FastAPI conventions

8. **Add first admin seeding to startup**
   - Call `AdminService.ensure_first_admin()` in `src/main.py` lifespan startup hook
   - Validation: First admin created on fresh DB, skipped if admins exist

9. **Register admin router in main.py**
   - Include admin router with prefix `/auth`
   - Validation: Endpoints accessible at `/auth/login` and `/auth/register`

10. **Test authentication flow**
    - WRITE NO TESTS AT ALL!!!

## Dependencies

- Tasks 1-4 can run in parallel
- Task 5 depends on tasks 2-4
- Task 6 depends on task 5
- Task 7 depends on tasks 5-6
- Task 8 depends on task 5
- Task 9 depends on task 7
- Task 10 depends on all previous tasks

## Validation Checkpoints

- [x] Settings include admin env vars
- [x] Admin model registered in `all_models.py`
- [x] Service uses existing security helpers (no code duplication)
- [x] Routes are thin (delegate to service)
- [x] First admin created only if DB empty
- [x] Login returns OAuth2-compliant token response
- [x] Protected endpoints return 401 without valid token
