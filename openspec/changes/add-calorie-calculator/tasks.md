## 1. Core Configuration
- [x] 1.1 Add calculator settings to `src/core/settings.py` (calorie deficit/surplus values + validation constraints)
- [x] 1.2 Update `.env.example` with new calculator config parameters

## 2. Calculator Module Implementation
- [x] 2.1 Create `src/modules/calculator/__init__.py`
- [x] 2.2 Create `src/modules/calculator/exceptions.py` with domain exceptions
- [x] 2.3 Create `src/modules/calculator/schemas.py` with request/response Pydantic models
- [x] 2.4 Create `src/modules/calculator/service.py` with BMR/TDEE calculation logic and tariff matching
- [x] 2.5 Create `src/modules/calculator/routes.py` with POST `/calculate` endpoint

## 3. Integration
- [x] 3.1 Register calculator router in `src/main.py`

## 4. Validation
- [ ] 4.1 Verify endpoint responds correctly with valid input
- [ ] 4.2 Verify validation errors for invalid biometric data
- [ ] 4.3 Verify tariff recommendation logic with multiple tariff scenarios
- [ ] 4.4 Confirm no database models created (stateless calculation)
