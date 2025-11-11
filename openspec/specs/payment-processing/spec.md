# payment-processing Specification

## Purpose
TBD - created by archiving change add-stripe-payment-flow. Update Purpose after archive.
## Requirements
### Requirement: Stripe PaymentIntent Creation
The system SHALL create Stripe PaymentIntents for tariff purchases with verified user emails.

#### Scenario: Create PaymentIntent for tariff
- **GIVEN** verified user and valid tariff_id
- **WHEN** POST /api/stripe/payment-intent with {email, tariff_id}
- **THEN** system retrieves tariff price, creates Stripe PaymentIntent with metadata {email, tariff_id, user_name}, returns client_secret

#### Scenario: Reject unverified email
- **GIVEN** email not verified
- **WHEN** PaymentIntent creation requested
- **THEN** system returns 403 Forbidden indicating verification required

#### Scenario: Invalid tariff rejection
- **GIVEN** non-existent tariff_id
- **WHEN** PaymentIntent creation requested
- **THEN** system returns 404 Not Found

### Requirement: Payment Record Creation
The system SHALL create payment records when PaymentIntent is created and update status via webhooks.

#### Scenario: Initial payment record
- **GIVEN** PaymentIntent created successfully
- **WHEN** payment record inserted
- **THEN** record contains: stripe_payment_intent_id, user_id, tariff_id, amount, currency, status="requires_payment_method", created_at

#### Scenario: Payment metadata storage
- **GIVEN** Stripe PaymentIntent created
- **WHEN** payment record saved
- **THEN** metadata field stores JSON with tariff details, user info

### Requirement: Stripe Webhook Processing
The system SHALL process Stripe webhook events with signature verification.

#### Scenario: Webhook signature verification
- **GIVEN** Stripe webhook request with signature header
- **WHEN** POST /api/stripe/webhook received
- **THEN** system verifies signature using webhook_secret, rejects invalid signatures with 400

#### Scenario: Payment success event
- **GIVEN** webhook event type "payment_intent.succeeded"
- **WHEN** webhook processed
- **THEN** system updates payment status to "succeeded", triggers email with success message and tariff PDFs

#### Scenario: Payment failure event
- **GIVEN** webhook event type "payment_intent.payment_failed"
- **WHEN** webhook processed
- **THEN** system updates payment status to "failed", sends failure email to user

#### Scenario: Payment processing event
- **GIVEN** webhook event type "payment_intent.processing"
- **WHEN** webhook processed
- **THEN** system updates payment status to "processing"

#### Scenario: Payment canceled event
- **GIVEN** webhook event type "payment_intent.canceled"
- **WHEN** webhook processed
- **THEN** system updates payment status to "canceled"

### Requirement: Payment Status Verification
The system SHALL provide endpoint to verify payment status for frontend confirmation.

#### Scenario: Query payment status
- **GIVEN** payment record exists
- **WHEN** GET /api/stripe/payment/{payment_id}/status
- **THEN** system returns {payment_id, status, amount, currency, created_at}

#### Scenario: Non-existent payment query
- **GIVEN** invalid payment_id
- **WHEN** status query requested
- **THEN** system returns 404 Not Found

### Requirement: Post-Payment Email Notifications
The system SHALL send emails via Resend after payment status changes.

#### Scenario: Success email with PDFs
- **GIVEN** payment status "succeeded" and tariff has attached PDFs
- **WHEN** email notification triggered
- **THEN** Resend sends email with configurable success message, attaches all tariff PDF files

#### Scenario: Success email without PDFs
- **GIVEN** payment status "succeeded" and tariff has no PDFs
- **WHEN** email notification triggered
- **THEN** Resend sends email with success message only

#### Scenario: Failure email
- **GIVEN** payment status "failed"
- **WHEN** email notification triggered
- **THEN** Resend sends email with configurable failure message

#### Scenario: Email template configuration
- **GIVEN** success/failure email messages
- **WHEN** messages loaded from configuration
- **THEN** settings.py provides PAYMENT_SUCCESS_EMAIL_BODY and PAYMENT_FAILURE_EMAIL_BODY

### Requirement: Payment Status Synchronization
The system SHALL store all Stripe PaymentIntent status values for complete tracking.

#### Scenario: Status transitions tracking
- **GIVEN** PaymentIntent status changes
- **WHEN** webhook updates payment record
- **THEN** system supports statuses: requires_payment_method, requires_action, processing, requires_capture, succeeded, canceled, failed

#### Scenario: Idempotent webhook processing
- **GIVEN** duplicate webhook event received
- **WHEN** processing same event_id twice
- **THEN** system detects duplicate, skips processing, returns 200 OK

### Requirement: PDF Attachment Retrieval
The system SHALL retrieve tariff PDF files from file storage for email attachments.

#### Scenario: Load tariff PDFs
- **GIVEN** tariff_id in payment metadata
- **WHEN** success email prepared
- **THEN** system queries TariffFile records, reads files from uploads/tariffs/{tariff_id}/

#### Scenario: Missing PDF handling
- **GIVEN** TariffFile record exists but file missing on disk
- **WHEN** PDF retrieval attempted
- **THEN** system logs error, sends email without attachment, notifies admin

