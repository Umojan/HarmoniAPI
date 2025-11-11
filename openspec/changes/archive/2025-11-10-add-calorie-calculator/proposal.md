## Why

Users need to calculate their personalized daily calorie requirements based on scientific formulas (Mifflin-St Jeor) and receive tariff recommendations that align with their calculated needs. Currently, the platform lacks a calculator endpoint that bridges user biometric data with available tariff plans.

## What Changes

- Add new `calculator` module under `src/modules/calculator/` with complete CRUD structure (models, schemas, exceptions, service, routes)
- Implement POST `/api/calculator/calculate` endpoint accepting user biometric data (gender, age, weight, height, activity level, goal)
- Calculate BMR using Mifflin-St Jeor formula (1990) with activity multipliers and goal adjustments
- Match calculated calorie needs to nearest tariff by comparing absolute calorie difference
- Return both calculated daily calorie requirement and recommended tariff
- Add configurable calorie deficit/surplus values to settings.py for weight loss/gain goals
- No database persistence required—pure calculation endpoint

## Impact

- Affected specs: `calorie-calculator` (new capability)
- Affected code:
  - `src/modules/calculator/` (new module with 5 files)
  - `src/core/settings.py` (add calculator config parameters)
  - `src/main.py` (register calculator router)
  - Integrates with existing `tariffs` module for recommendation logic
