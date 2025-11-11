# email-verification Specification

## Purpose
TBD - created by archiving change add-stripe-payment-flow. Update Purpose after archive.
## Requirements
### Requirement: Verification Code Generation
The system SHALL generate 6-digit numeric verification codes with 10-minute expiration.

#### Scenario: Code generation on request
- **GIVEN** user provides name, surname, and email
- **WHEN** POST /api/auth/send-verification-code is called
- **THEN** system generates random 6-digit code, stores with 10min TTL, sends via Resend

#### Scenario: Code format validation
- **GIVEN** code generation request
- **WHEN** code is created
- **THEN** code is exactly 6 digits (000000-999999)

### Requirement: Rate Limiting
The system SHALL enforce 1 code per minute per email address to prevent abuse.

#### Scenario: Rate limit enforcement
- **GIVEN** user requested code less than 60 seconds ago
- **WHEN** user requests new code
- **THEN** system returns 429 Too Many Requests with retry-after header

#### Scenario: Rate limit reset
- **GIVEN** 60+ seconds elapsed since last code request
- **WHEN** user requests new code
- **THEN** system generates and sends new code

### Requirement: Code Verification
The system SHALL verify codes within 10-minute validity window and track verification attempts.

#### Scenario: Valid code verification
- **GIVEN** user received code and code not expired
- **WHEN** POST /api/auth/verify-code with correct code
- **THEN** system marks verification as complete, creates user record, returns success

#### Scenario: Expired code rejection
- **GIVEN** code created more than 10 minutes ago
- **WHEN** user submits code
- **THEN** system returns error indicating code expired

#### Scenario: Invalid code rejection
- **GIVEN** user submits incorrect code
- **WHEN** verification attempted
- **THEN** system increments attempt counter, returns error

#### Scenario: Maximum attempts protection
- **GIVEN** 5 failed verification attempts
- **WHEN** user attempts 6th verification
- **THEN** system invalidates code, requires new code request

### Requirement: Email Delivery via Resend
The system SHALL use Resend SDK to deliver verification codes via email.

#### Scenario: Send verification email
- **GIVEN** verification code generated
- **WHEN** email sending initiated
- **THEN** Resend API receives request with from address, recipient email, subject, HTML body containing code

#### Scenario: Email delivery failure handling
- **GIVEN** Resend API returns error
- **WHEN** email sending fails
- **THEN** system logs error, returns 503 Service Unavailable to user

### Requirement: Verification State Management
The system SHALL track verification state (pending, verified, expired) per email.

#### Scenario: Pending verification state
- **GIVEN** code sent but not yet verified
- **WHEN** verification record queried
- **THEN** verified_at is NULL and expires_at > current time

#### Scenario: Verified state
- **GIVEN** user successfully verified code
- **WHEN** verification record queried
- **THEN** verified_at timestamp is set

#### Scenario: Cleanup expired verifications
- **GIVEN** verification records with expires_at < current time
- **WHEN** periodic cleanup runs
- **THEN** expired unverified records are deleted

