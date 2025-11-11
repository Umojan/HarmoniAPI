## ADDED Requirements

### Requirement: Calorie Calculation Endpoint

The system SHALL provide a POST endpoint `/api/calculator/calculate` that accepts user biometric data and returns personalized daily calorie requirements using the Mifflin-St Jeor formula (1990).

#### Scenario: Male user calculation with weight loss goal

- **WHEN** POST `/api/calculator/calculate` with `{"gender": "male", "age": 30, "weight_kg": 80, "height_cm": 180, "activity_level": "moderate", "goal": "weight_loss"}`
- **THEN** calculate BMR = (10 × 80) + (6.25 × 180) - (5 × 30) + 5 = 1775 kcal
- **AND** calculate TDEE = 1775 × 1.55 = 2751 kcal
- **AND** apply deficit = 2751 - 500 = 2251 kcal/day
- **AND** return 200 with `{"recommended_calories": 2251, "tariff": {...}}`

#### Scenario: Female user calculation with maintenance goal

- **WHEN** POST `/api/calculator/calculate` with `{"gender": "female", "age": 25, "weight_kg": 65, "height_cm": 170, "activity_level": "moderate", "goal": "maintenance"}`
- **THEN** calculate BMR = (10 × 65) + (6.25 × 170) - (5 × 25) - 161 = 1426.5 kcal
- **AND** calculate TDEE = 1426.5 × 1.55 = 2211 kcal
- **AND** apply no adjustment (maintenance) = 2211 kcal/day
- **AND** return 200 with `{"recommended_calories": 2211, "tariff": {...}}`

#### Scenario: Invalid input data

- **WHEN** POST `/api/calculator/calculate` with invalid age (negative, zero, or >120)
- **THEN** return 422 with validation error details

### Requirement: Activity Level Multipliers

The system SHALL apply activity level multipliers to BMR based on standardized coefficients.

#### Scenario: Activity level mapping

- **WHEN** activity_level is "sedentary"
- **THEN** apply multiplier 1.2

- **WHEN** activity_level is "light"
- **THEN** apply multiplier 1.375

- **WHEN** activity_level is "moderate"
- **THEN** apply multiplier 1.55

- **WHEN** activity_level is "active"
- **THEN** apply multiplier 1.725

- **WHEN** activity_level is "very_active"
- **THEN** apply multiplier 1.9

### Requirement: Goal-Based Calorie Adjustment

The system SHALL adjust TDEE based on user fitness goals using configurable deficit/surplus values from settings.

#### Scenario: Weight loss adjustment

- **WHEN** goal is "weight_loss" and TDEE is 2500 kcal
- **AND** `CALCULATOR_CALORIE_DEFICIT` setting is 500
- **THEN** return recommended_calories = 2500 - 500 = 2000 kcal/day

#### Scenario: Muscle gain adjustment

- **WHEN** goal is "muscle_gain" and TDEE is 2200 kcal
- **AND** `CALCULATOR_CALORIE_SURPLUS` setting is 300
- **THEN** return recommended_calories = 2200 + 300 = 2500 kcal/day

#### Scenario: Maintenance (no adjustment)

- **WHEN** goal is "maintenance" and TDEE is 2100 kcal
- **THEN** return recommended_calories = 2100 kcal/day

### Requirement: Tariff Recommendation

The system SHALL recommend the tariff with the smallest absolute calorie difference to the calculated daily requirement.

#### Scenario: Exact tariff match

- **WHEN** calculated calories = 1800 kcal/day
- **AND** available tariffs have calories [1500, 1800, 2200]
- **THEN** recommend tariff with 1800 calories

#### Scenario: Nearest tariff selection

- **WHEN** calculated calories = 1950 kcal/day
- **AND** available tariffs have calories [1500, 1800, 2200]
- **THEN** recommend tariff with 2200 calories (|1950-2200| = 250 < |1950-1800| = 150 is false, so 1800)
- **CORRECTION**: recommend tariff with 1800 calories (|1950-1800| = 150 < |1950-2200| = 250)

#### Scenario: No tariffs with calorie data

- **WHEN** calculated calories = 2000 kcal/day
- **AND** no tariffs have `calories` field populated
- **THEN** return `null` for tariff field

### Requirement: Input Validation

The system SHALL validate all biometric inputs against physiological constraints.

#### Scenario: Age validation

- **WHEN** age < 15 or age > 120
- **THEN** return 422 with error "Age must be between 15 and 120"

#### Scenario: Weight validation

- **WHEN** weight_kg < 30 or weight_kg > 300
- **THEN** return 422 with error "Weight must be between 30 and 300 kg"

#### Scenario: Height validation

- **WHEN** height_cm < 100 or height_cm > 250
- **THEN** return 422 with error "Height must be between 100 and 250 cm"

#### Scenario: Enum validation

- **WHEN** gender not in ["male", "female"]
- **THEN** return 422 with validation error

- **WHEN** activity_level not in ["sedentary", "light", "moderate", "active", "very_active"]
- **THEN** return 422 with validation error

- **WHEN** goal not in ["weight_loss", "maintenance", "muscle_gain"]
- **THEN** return 422 with validation error

### Requirement: Stateless Calculation

The system SHALL NOT persist calculation requests or results to the database.

#### Scenario: No database interaction

- **WHEN** POST `/api/calculator/calculate` is called
- **THEN** perform calculation in-memory
- **AND** do not create any database records
- **AND** only query tariffs table for recommendation matching
