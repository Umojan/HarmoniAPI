# Project Context

## Purpose

Provide a FastAPI backend for "Harmoni" – a nutrition platform that calculates personalized calorie needs, offers meal plans, handles Stripe payments, and delivers PDF materials to customers while managing client inquiries through Telegram/email notifications.

## Tech Stack

* Python 3.13+
* FastAPI (async-first web framework)
* PostgreSQL
* SQLAlchemy Async ORM + Alembic (async templated migrations)
* uv (package and virtual environment manager)
* Stripe API (payment processing)
* SMTP/SendGrid (email delivery)
* Rich (developer-facing logging and diagnostics)

## Project Conventions

### Code Style

Follow PEP 8, enforce full type hints, and keep every callable focused on a single responsibility.  
Treat asynchronous I/O as the default (endpoints, services, external calls, and database access).  
Prefer descriptive module names, short cohesive files, and separation of concerns between API, services, and persistence code.

### Architecture Patterns

The technical regulations enforce a layered FastAPI application with a predictable filesystem layout. Always rely on the latest stable FastAPI release, keep the application fully asynchronous, and respect separation of concerns—one folder or file should own exactly one responsibility.

#### Root level

* `alembic` — database migrations scaffolded with `alembic init -t async alembic`; contains `env.py`, `script.py.mako`, and the `versions/` directory.
* `src` — all runtime source code for the service.
* `uploads/` — storage for PDF files (meal plans, recipes) attached to tariffs.
* Project root — infrastructure artifacts (Docker/compose files, `.env`, scripts).

#### Core and configuration

* `core` stores application settings, logging setup, security, and base exceptions. Modules inherit from these building blocks rather than redefining them.
* `extensions` holds optional integrations that enhance the app (Redis clients, task queues, notification hubs, pub/sub adapters).

#### Database layer (db) — this package always exposes four fixed files:

* `base.py` defines the declarative base and naming conventions.
* `engine.py` configures the async SQLAlchemy engine, session factory, rich logging, and the `with_session` decorator.
* `mixin.py` collects reusable columns such as UUID primary keys and timestamp fields.
* `all_models.py` imports every SQLAlchemy model so Alembic can autogenerate migrations; import this module only inside migration contexts (`import src.db.all_models`).

The canonical definitions come directly from the regulation.

#### Modules (domain logic)

* `src/modules/<feature>/` — one directory per resource (e.g., tariffs, calculator, orders, inquiries, admin).
* Every module exposes the same fixed file set: `models.py`, `schemas.py`, `exceptions.py`, `service.py`, and `routes.py`.

  * `models.py` contains SQLAlchemy models and stays registered via `all_models.py`.
  * `schemas.py` defines Pydantic request/response contracts.
  * `exceptions.py` inherits from the base `AppException` defined in `exceptions.py`.
  * `service.py` implements business logic and interacts with models and external services.
  * `routes.py` defines FastAPI endpoints, performing validation only before delegating to services.

* Keep each module self-contained; avoid cross-importing between unrelated modules.

#### Services (external integrations). FILE AND FOLDER NAMES ARE JUST EXAMPLE:

* `services` groups adapters for third-party systems. Each integration has its own subpackage:

  * `payment_service/stripe_adapter.py` — Stripe payment processing
  * `email_service/smtp_adapter.py` — email delivery (order confirmations, PDF attachments)

* Implement adapters/facades that hide vendor-specific nuances and offer a consistent API to the rest of the application.

#### API organization

* Endpoint registration lives in each module's `routes.py` file. Routes remain thin—validate input, invoke service methods, and return responses.
* `main.py` serves solely as the FastAPI entrypoint: initialize the app, attach middleware, include routers, and configure CORS for frontend communication. Never embed business logic here.

#### Exceptions and formatting

* `exceptions.py` defines the base hierarchy. Domain modules add their own derived exceptions in `exceptions.py` so HTTP errors remain explicit.
* Follow PEP 8 and full typing. Every function or class should handle one responsibility, files stay short, and asynchronous patterns are used everywhere (database, HTTP clients, external APIs, file I/O).

#### Best practices

* Use dependency injection for sessions, configuration, and services.
* Keep dependencies directional: routes → services → models/schemas/exceptions; avoid reverse imports.
* Provide abstract base classes for adapters with shared behavior, and only allow singletons where global state is required (e.g., Stripe client, Telegram bot instance).
* Document inputs and outputs for any external integration wrapper.
* Alembic `env.py` must import metadata from `src.db.base` and load models via `import src.db.all_models` while running migrations on an async engine.
* Store uploaded PDFs in `uploads/` directory with organized structure: `uploads/tariffs/{tariff_id}/{filename}.pdf`.

## Git Workflow

Commits follow Conventional Commits 1.0.0:

* Format: `<type>[optional scope]: <description>`
* Primary types: `feat` for new functionality, `fix` for bug fixes, plus optional `build`, `chore`, `ci`, `docs`, `style`, `refactor`, `perf`, `test`, and custom scopes.
* Breaking changes must either append `!` to the type/scope or add a `BREAKING CHANGE:` footer.
* Multi-line bodies and additional footers follow git trailer conventions.  
  Feature work lands through topic branches that merge into main via review (assumed default flow).


## Important Constraints

* Maintain strict async-first design across API, database, and integrations.
* Keep `main.py` limited to FastAPI initialization, middleware, and router inclusion; no business logic inside entrypoints.
* Import models only through `import src.db.all_models` inside Alembic `env.py`.
* Reuse shared SQLAlchemy artifacts (Base, BaseMixin, engine/session helpers) to ensure consistent metadata and naming conventions.
* When adding external adapters, hide vendor-specific behavior behind facades within services.
* Use uv as the canonical package manager and environment tool.
* Store Stripe webhook secret and API keys in environment variables, never in code.


# ⚠️ CRITICAL DEVELOPMENT RULES

These rules are mandatory and must be followed strictly:

## Rule 1: Database Migrations

**DO NOT CREATE OR RUN MIGRATIONS MANUALLY. MIGRATIONS HAPPEN AUTOMATICALLY!**

* The system handles all database migrations automatically via Alembic
* Never run `alembic revision` or `alembic upgrade` commands manually
* Database schema changes are managed by the infrastructure, not by developers during feature implementation
