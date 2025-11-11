# Implementation Tasks

## 1. Configuration and Dependencies
- [x] 1.1 Add Resend, Stripe dependencies to pyproject.toml
- [x] 1.2 Add configuration to settings.py: RESEND_API_KEY, RESEND_FROM_EMAIL, STRIPE_SECRET_KEY, STRIPE_PUBLIC_KEY, STRIPE_WEBHOOK_SECRET
- [x] 1.3 Add email template configuration: PAYMENT_SUCCESS_EMAIL_SUBJECT, PAYMENT_SUCCESS_EMAIL_BODY, PAYMENT_FAILURE_EMAIL_SUBJECT, PAYMENT_FAILURE_EMAIL_BODY
- [x] 1.4 Add verification config: VERIFICATION_CODE_TTL_MINUTES=10, VERIFICATION_CODE_LENGTH=6, VERIFICATION_RATE_LIMIT_SECONDS=60, VERIFICATION_MAX_ATTEMPTS=5
- [x] 1.5 Update .env.example with new variables

## 2. Database Models
- [x] 2.1 Create src/modules/users/models.py with User model (id, name, surname, email unique index, is_verified, timestamps)
- [x] 2.2 Create src/modules/auth/models.py with EmailVerification model (id, email, code, expires_at, verified_at, attempts, created_at)
- [x] 2.3 Create src/modules/payment/models.py with Payment model (id, stripe_payment_intent_id unique, user_id FK, tariff_id FK nullable, amount, currency, status, metadata JSON, created_at, updated_at)
- [x] 2.4 Register models in src/db/all_models.py

## 3. External Service Adapters
- [x] 3.1 Create src/services/resend/adapter.py with ResendAdapter class (send_verification_code, send_payment_success, send_payment_failure methods)
- [x] 3.2 Create src/services/stripe/adapter.py with StripeAdapter class (create_payment_intent, verify_webhook_signature, construct_event methods)
- [x] 3.3 Initialize Stripe API key in adapter singleton
- [x] 3.4 Initialize Resend API key in adapter singleton

## 4. Auth Module (Email Verification)
- [x] 4.1 Create src/modules/auth/schemas.py (SendVerificationCodeRequest, VerifyCodeRequest, VerificationResponse)
- [x] 4.2 Create src/modules/auth/exceptions.py (CodeExpiredException, CodeInvalidException, RateLimitExceededException, MaxAttemptsExceededException)
- [x] 4.3 Create src/modules/auth/service.py with AuthService class:
  - [x] 4.3.1 generate_verification_code() - random 6-digit code
  - [x] 4.3.2 send_verification_code(name, surname, email) - rate limit check, create verification record, send via Resend
  - [x] 4.3.3 verify_code(email, code) - validate code, check expiry, check attempts, create User record, mark verified
  - [x] 4.3.4 cleanup_expired_verifications() - delete expired records
- [x] 4.4 Create src/modules/auth/routes.py with endpoints:
  - [x] 4.4.1 POST /api/auth/send-verification-code
  - [x] 4.4.2 POST /api/auth/verify-code

## 5. Users Module
- [x] 5.1 Create src/modules/users/schemas.py (UserUpdateRequest, UserResponse)
- [x] 5.2 Create src/modules/users/exceptions.py (UserNotFoundException, UserAlreadyExistsException)
- [x] 5.3 Create src/modules/users/service.py with UserService class:
  - [x] 5.3.1 get_user_by_email(email) -> User | None
  - [x] 5.3.2 get_user_by_id(user_id) -> User | None
  - [x] 5.3.3 check_email_exists(email) -> bool
  - [x] 5.3.4 update_user(user_id, name?, surname?, email?) -> User
  - [x] 5.3.5 delete_user(user_id) -> None
- [x] 5.4 Create src/modules/users/routes.py with endpoints:
  - [x] 5.4.1 GET /api/users/{user_id} (admin-only)
  - [x] 5.4.2 GET /api/users/email/{email} (admin-only)
  - [x] 5.4.3 PATCH /api/users/{user_id} (admin-only)
  - [x] 5.4.4 DELETE /api/users/{user_id} (admin-only)

## 6. Payment Module
- [x] 6.1 Create src/modules/payment/schemas.py (CreatePaymentIntentRequest, PaymentIntentResponse, PaymentStatusResponse, StripeWebhookEvent)
- [x] 6.2 Create src/modules/payment/exceptions.py (PaymentNotFoundException, UserNotVerifiedException, TariffNotFoundException, StripeWebhookException)
- [x] 6.3 Create src/modules/payment/service.py with PaymentService class:
  - [x] 6.3.1 create_payment_intent(email, tariff_id) - verify user, get tariff, create Stripe PaymentIntent, save Payment record
  - [x] 6.3.2 handle_webhook_event(event_type, payment_intent_data) - update payment status, trigger email
  - [x] 6.3.3 get_payment_status(payment_id) -> Payment
  - [x] 6.3.4 send_success_email(payment) - load tariff PDFs, send via Resend
  - [x] 6.3.5 send_failure_email(payment) - send failure notification
  - [x] 6.3.6 check_duplicate_webhook(event_id) - idempotency check (placeholder, TODO: implement with Redis)
- [x] 6.4 Create src/modules/payment/routes.py with endpoints:
  - [x] 6.4.1 POST /api/stripe/payment-intent
  - [x] 6.4.2 POST /api/stripe/webhook (with signature verification)
  - [x] 6.4.3 GET /api/stripe/payment/{payment_id}/status

## 7. Integration and Testing
- [x] 7.1 Register auth router in src/main.py (prefix: /api/auth)
- [x] 7.2 Register payment router in src/main.py (prefix: /api)
- [x] 7.3 Register users router in src/main.py (prefix: /api)
