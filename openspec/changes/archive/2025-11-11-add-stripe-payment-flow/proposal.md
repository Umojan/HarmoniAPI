# Add Stripe Payment Flow with Email Verification

## Why

Currently, the platform has tariffs and a calorie calculator, but no payment processing capability. Users cannot purchase tariff plans or receive their PDF materials. We need a complete payment flow that:
- Verifies user email ownership before accepting payment
- Processes payments securely through Stripe without storing card data
- Delivers purchased tariff PDFs automatically via email
- Tracks payment history and status

## What Changes

- **User registration system** with email verification (name, surname, email fields)
- **Email verification module** with 6-digit codes (10min TTL, 1 code/min rate limit)
- **Stripe payment integration** (PaymentIntent creation, webhook processing, status verification)
- **Payment tracking** (full payment history with Stripe metadata)
- **Resend email service** integration for verification codes and post-payment notifications
- **Configuration** for email templates (success/failure messages)

### Endpoints Added
- `POST /api/auth/send-verification-code` - send verification code to email
- `POST /api/auth/verify-code` - verify code and register user
- `POST /api/stripe/payment-intent` - create Stripe PaymentIntent for tariff
- `POST /api/stripe/webhook` - handle Stripe events (payment success/failure)
- `GET /api/stripe/payment/{payment_id}/status` - check payment status

### Database Tables
- `users` - name, surname, email, is_verified
- `email_verifications` - email, code, expires_at, verified_at, attempts
- `payments` - stripe_payment_intent_id, user_id, tariff_id, amount, currency, status, metadata

### External Services
- Resend API for email delivery
- Stripe API for payment processing

## Impact

**Affected specs:**
- NEW: `email-verification` - verification code generation and validation
- NEW: `payment-processing` - Stripe integration and payment tracking
- NEW: `user-registration` - minimal user registration via email verification

**Affected code:**
- `src/core/settings.py` - add Resend API keys, Stripe keys, email templates config
- `src/modules/` - new modules: `auth`, `payment`, `users`
- `src/services/` - new services: `resend_adapter.py`, `stripe_adapter.py`
- `src/main.py` - register new routers
- `.env` - new environment variables

**No breaking changes** - purely additive functionality.
