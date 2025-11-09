# Add Tariff Management and File Storage

## Why

The platform needs to manage nutrition tariff plans (Fit Start, Balance, Energy) with associated pricing, parameters, and PDF materials. Currently no system exists to create, update, or delete tariff offerings or store/manage their PDF attachments.

## What Changes

- Add tariff management module with full CRUD operations
- Add file storage module for PDF management (CRD operations, no update)
- Store PDFs in `uploads/tariffs/` directory structure
- Configure upload paths and size limits via environment variables
- **BREAKING**: Introduces new database tables `tariffs` and `tariff_files`

## Impact

- Affected specs: `tariff-management` (new), `file-storage` (new)
- Affected code:
  - `src/modules/tariffs/` (new module)
  - `src/modules/files/` (new module)
  - `src/core/settings.py` (add upload configuration)
  - `src/db/all_models.py` (register new models)
  - `.env.example` (add upload settings)
