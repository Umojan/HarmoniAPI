# Spec: Admin Management

## ADDED Requirements

### Requirement: First admin created from environment variables

The system SHALL create the first admin from `FIRST_ADMIN_EMAIL` and `FIRST_ADMIN_PASSWORD` on startup if no admins exist.

#### Scenario: Empty database creates first admin

**Given** database has zero admins
**And** env vars set: `FIRST_ADMIN_EMAIL=root@harmoni.com`, `FIRST_ADMIN_PASSWORD=initialpass`
**When** application starts (lifespan startup hook runs)
**Then** admin created with email `root@harmoni.com` and hashed password
**And** `first_name` and `last_name` are NULL

#### Scenario: Existing admin skips seeding

**Given** database has one or more admins
**When** application starts
**Then** no new admin is created (first admin seeding skipped)

#### Scenario: Missing env vars raises error

**Given** `FIRST_ADMIN_EMAIL` or `FIRST_ADMIN_PASSWORD` not set
**When** application starts
**Then** startup fails with configuration error

---

### Requirement: Admins can register new admins

Only authenticated admins SHALL be able to create additional admin accounts.

#### Scenario: Admin creates new admin with names

**Given** logged-in admin with valid token
**When** POST `/auth/register` with `{"email": "new@harmoni.com", "password": "pass456", "first_name": "John", "last_name": "Doe"}`
**And** header `Authorization: Bearer <valid_token>`
**Then** response is 201 with created admin object (email, first_name, last_name, id, created_at)
**And** password hash NOT included in response

#### Scenario: Admin creates new admin without names

**Given** logged-in admin
**When** POST `/auth/register` with `{"email": "minimal@harmoni.com", "password": "pass789"}`
**Then** response is 201 with admin object (first_name and last_name are null)

#### Scenario: Duplicate email returns 400

**Given** admin exists with email `existing@harmoni.com`
**When** POST `/auth/register` with same email
**Then** response is 400 with error "Email already registered"

#### Scenario: Unauthenticated request returns 401

**Given** no Authorization header
**When** POST `/auth/register`
**Then** response is 401 with error "Not authenticated"

---

### Requirement: Admin model includes optional name fields

Admin records SHALL store email (unique, required), hashed password (required), and optional first/last names.

#### Scenario: Admin stored with all fields

**Given** admin registered with first_name="Alice" and last_name="Smith"
**Then** database record has all fields populated
**And** `created_at` and `updated_at` timestamps auto-set

#### Scenario: Admin stored without names

**Given** admin registered without first_name or last_name
**Then** database record has `first_name=NULL` and `last_name=NULL`

#### Scenario: Email uniqueness enforced

**Given** admin exists with email `unique@test.com`
**When** attempting to create second admin with same email
**Then** database raises unique constraint violation (handled as 400 by service)
