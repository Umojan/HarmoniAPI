# user-registration Specification

## Purpose
TBD - created by archiving change add-stripe-payment-flow. Update Purpose after archive.
## Requirements
### Requirement: User Registration via Email Verification
The system SHALL register users through email verification without traditional username/password authentication. Users provide name, surname, and email; verification serves as registration confirmation.

#### Scenario: Successful registration
- **GIVEN** user provides valid name, surname, and email
- **WHEN** user completes email verification
- **THEN** user record is created with is_verified=true

#### Scenario: Duplicate email prevention
- **GIVEN** email already exists in database
- **WHEN** user attempts to verify with existing email
- **THEN** system returns error indicating email already registered

### Requirement: User Data Model
The system SHALL store minimal user information required for payment and communication.

#### Scenario: User record structure
- **GIVEN** user completes verification
- **WHEN** user record is created
- **THEN** record contains: id (UUID), name, surname, email, is_verified (boolean), created_at, updated_at

#### Scenario: Email uniqueness constraint
- **GIVEN** database constraint on email field
- **WHEN** attempting to insert duplicate email
- **THEN** database rejects insertion

### Requirement: Verified User Identification
The system SHALL identify verified users by email for payment operations.

#### Scenario: Lookup verified user
- **GIVEN** verified user exists
- **WHEN** payment flow queries user by email
- **THEN** system returns user record with is_verified=true

#### Scenario: Reject unverified users
- **GIVEN** unverified email in verification table
- **WHEN** attempting payment operation
- **THEN** system requires verification completion first

