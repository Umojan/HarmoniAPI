# Spec: Admin Authentication

## ADDED Requirements

### Requirement: Admin login with email and password

The system SHALL authenticate admins via OAuth2 password flow and issue JWT access tokens.

#### Scenario: Valid credentials return access token

**Given** an admin exists with email `admin@test.com` and password `secret123`
**When** POST `/auth/login` with `{"email": "admin@test.com", "password": "secret123"}`
**Then** response is 200 with `{"access_token": "<jwt>", "token_type": "bearer"}`
**And** token decodes to `{"sub": "<admin_id>"}`

#### Scenario: Invalid credentials return 401

**Given** no admin exists with email `wrong@test.com`
**When** POST `/auth/login` with `{"email": "wrong@test.com", "password": "any"}`
**Then** response is 401 with error message "Invalid credentials"

#### Scenario: Wrong password returns 401

**Given** admin exists with email `admin@test.com`
**When** POST `/auth/login` with correct email but wrong password
**Then** response is 401 with error message "Invalid credentials"

---

### Requirement: Protected endpoints require valid admin token

Endpoints decorated with `get_current_admin` dependency SHALL reject unauthenticated requests.

#### Scenario: Valid token grants access

**Given** admin logged in with token `<valid_jwt>`
**When** GET `/auth/register` with header `Authorization: Bearer <valid_jwt>`
**Then** request proceeds (dependency returns admin object)

#### Scenario: Missing token returns 401

**Given** no Authorization header
**When** accessing protected endpoint
**Then** response is 401 with error "Not authenticated"

#### Scenario: Invalid token returns 401

**Given** malformed or expired JWT
**When** accessing protected endpoint with `Authorization: Bearer <bad_token>`
**Then** response is 401 with error "Invalid token"

#### Scenario: Token for non-existent admin returns 401

**Given** valid JWT with `sub: <deleted_admin_id>`
**When** accessing protected endpoint
**Then** response is 401 with error "Admin not found"

---

### Requirement: OAuth2 password flow compatibility

The login endpoint SHALL follow OAuth2 password grant conventions for client compatibility.

#### Scenario: Accept form-encoded credentials

**Given** client sends `Content-Type: application/x-www-form-urlencoded`
**When** POST `/auth/login` with `username=admin@test.com&password=secret`
**Then** response is 200 with access token (same as JSON request)

#### Scenario: Token type is bearer

**Given** successful login
**Then** response includes `"token_type": "bearer"`
