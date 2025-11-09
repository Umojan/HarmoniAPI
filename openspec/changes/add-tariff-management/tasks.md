# Implementation Tasks

## 1. Configuration

- [x] 1.1 Add upload settings to `src/core/settings.py`
- [x] 1.2 Add upload environment variables to `.env.example`

## 2. File Storage Module

- [x] 2.1 Create `src/modules/files/models.py` with TariffFile model
- [x] 2.2 Create `src/modules/files/schemas.py` with request/response schemas
- [x] 2.3 Create `src/modules/files/exceptions.py` with custom exceptions
- [x] 2.4 Create `src/modules/files/service.py` with PDF upload/read/delete logic
- [x] 2.5 Create `src/modules/files/routes.py` with CRD endpoints
- [x] 2.6 Register models in `src/db/all_models.py`

## 3. Tariff Management Module

- [x] 3.1 Create `src/modules/tariffs/models.py` with Tariff model
- [x] 3.2 Create `src/modules/tariffs/schemas.py` with request/response schemas
- [x] 3.3 Create `src/modules/tariffs/exceptions.py` with custom exceptions
- [x] 3.4 Create `src/modules/tariffs/service.py` with CRUD logic
- [x] 3.5 Create `src/modules/tariffs/routes.py` with CRUD endpoints
- [x] 3.6 Register models in `src/db/all_models.py`

## 4. API Integration

- [x] 4.1 Register file routes in `src/main.py`
- [x] 4.2 Register tariff routes in `src/main.py`
- [x] 4.3 Create `uploads/tariffs/` directory structure
