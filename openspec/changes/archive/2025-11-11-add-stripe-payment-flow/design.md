# Design Document: Stripe Payment Flow with Email Verification

## Context

Harmoni platform needs payment processing to monetize tariff plans. Requirements:
- Email verification before payment (prove ownership)
- Stripe integration without storing card data (PCI compliance)
- Automatic PDF delivery post-payment
- Complete payment tracking and status synchronization

**Constraints:**
- No traditional user authentication (no passwords)
- Async-first architecture (FastAPI + SQLAlchemy async)
- Must follow existing module structure (models, schemas, exceptions, service, routes)
- Email delivery via Resend API
- Stripe webhook for authoritative payment status

## Goals / Non-Goals

**Goals:**
- Secure email verification with rate limiting and expiration
- Stripe PaymentIntent integration with full status tracking
- Reliable webhook processing with signature verification and idempotency
- Automatic email notifications with PDF attachments on success
- Simple, scalable database schema

**Non-Goals:**
- Traditional user authentication (passwords, sessions, JWT)
- Subscription/recurring payments (only one-time tariff purchases)
- Shopping cart (single tariff per transaction)
- Refund processing (future enhancement)
- Invoice generation (Stripe provides receipts)

## Decisions

### 1. User Model: Email-Only Registration
**Decision:** Users register by verifying email only (name, surname, email). No password field.

**Rationale:**
- Users only need to purchase once and receive PDFs
- Email verification proves ownership
- Simpler UX (no password management)
- Can add authentication later if needed

**Trade-off:** No user accounts for repeat purchases (acceptable for MVP).

### 2. Verification Code Storage: Dedicated Table
**Decision:** Store codes in `email_verifications` table with TTL, not in `users` table.

**Rationale:**
- Codes are temporary (10min), users are permanent
- Multiple verification attempts possible (new codes)
- Clean separation of concerns
- Easy cleanup of expired records

**Schema:**
```python
email_verifications:
  - id: UUID
  - email: String (indexed, not unique - allow retries)
  - code: String(6)
  - expires_at: DateTime
  - verified_at: DateTime (nullable)
  - attempts: Integer (default 0)
  - created_at: DateTime
```

### 3. Rate Limiting: Application-Level
**Decision:** Implement rate limiting in `AuthService`, not database constraints or middleware.

**Rationale:**
- Check last code creation timestamp per email
- Simple query: `SELECT created_at WHERE email = ? ORDER BY created_at DESC LIMIT 1`
- No external dependencies (Redis)
- Sufficient for moderate traffic

**Limitation:** Not distributed-system-safe (acceptable for single-instance deployment).

### 4. Payment Status: Store All Stripe Statuses
**Decision:** Track complete Stripe PaymentIntent status lifecycle.

**Statuses:** `requires_payment_method`, `requires_action`, `processing`, `requires_capture`, `succeeded`, `canceled`, `failed`

**Rationale:**
- Full observability of payment flow
- Debug failed payments easily
- Support async payment methods (bank transfers)
- Frontend can poll status endpoint

**Schema:**
```python
payments:
  - id: UUID
  - stripe_payment_intent_id: String (unique, indexed)
  - user_id: UUID (FK to users)
  - tariff_id: UUID (FK to tariffs, nullable)
  - amount: Integer (minor currency units)
  - currency: String(3) (e.g., "usd")
  - status: String (Stripe status values)
  - metadata: JSON (store {email, tariff_name, user_name})
  - created_at: DateTime
  - updated_at: DateTime
```

### 5. Webhook Idempotency: Event ID Tracking
**Decision:** Store processed webhook event IDs to prevent duplicate processing.

**Alternative considered:** Check payment status before update (not sufficient - race conditions).

**Implementation:**
- Add `webhook_events` table: (id, stripe_event_id unique, processed_at)
- On webhook: check if event_id exists, skip if duplicate, insert if new
- Cleanup old events periodically (keep 30 days)

### 6. Email Service: Resend Adapter Pattern
**Decision:** Wrap Resend SDK in adapter class within `src/services/resend/`.

**Interface:**
```python
class ResendAdapter:
    async def send_verification_code(to: str, name: str, code: str) -> None
    async def send_payment_success(to: str, name: str, tariff_name: str, pdf_paths: list[str]) -> None
    async def send_payment_failure(to: str, name: str, reason: str) -> None
```

**Rationale:**
- Hide Resend API details from business logic
- Easy to mock in tests
- Consistent with Stripe adapter pattern
- Can swap email provider later

### 7. PDF Attachment: Read from Disk
**Decision:** Load PDFs from `uploads/tariffs/{tariff_id}/` filesystem, attach to email.

**Alternatives considered:**
- Store in DB as bytea (inefficient for large files)
- Generate download links (requires authentication, complexity)

**Implementation:**
- Query `TariffFile` table for tariff PDFs
- Read files from disk: `Path(upload_dir) / "tariffs" / str(tariff_id) / filename`
- Attach to Resend email as file bytes
- Handle missing files gracefully (log error, skip attachment)

### 8. Email Templates: Configuration
**Decision:** Store email subject/body in `settings.py` as configurable strings.

**Format:**
```python
PAYMENT_SUCCESS_EMAIL_SUBJECT = "Payment Successful - {tariff_name}"
PAYMENT_SUCCESS_EMAIL_BODY = """
Hello {name},

Your payment for {tariff_name} was successful!
Amount: {amount} {currency}

Your materials are attached to this email.

Thank you for choosing Harmoni!
"""
```

**Rationale:**
- Simple to configure via .env
- No template engine needed (use string .format())
- Can migrate to template files later if needed

## Risks / Trade-offs

### Risk: Resend API Failure
**Impact:** Users cannot verify email or receive payment confirmations.

**Mitigation:**
- Return 503 Service Unavailable on email send failure
- Log errors with full context
- Consider retry queue for payment emails (future)
- Monitor Resend API status

### Risk: Webhook Delivery Failure
**Impact:** Payment succeeds in Stripe but status not updated, no email sent.

**Mitigation:**
- Stripe retries webhooks automatically (3 days)
- Implement idempotent webhook handler
- Provide manual payment status sync endpoint (admin)
- Monitor webhook delivery in Stripe dashboard

### Risk: Race Condition - Webhook vs Frontend
**Impact:** Frontend confirms payment before webhook updates DB.

**Mitigation:**
- Frontend polls payment status endpoint after confirmation
- Webhook updates are authoritative (overwrite frontend-initiated updates)
- Use database transactions for payment status updates

### Risk: Rate Limit Bypass
**Impact:** Attacker requests many codes for same email.

**Mitigation:**
- 1 code/min per email (application-level)
- Max 5 verification attempts per code
- Consider IP-based rate limiting (future)
- Monitor verification request volume

### Trade-off: No Distributed Rate Limiting
**Decision:** Single-process rate limiting (check last code timestamp).

**Consequence:** Multiple app instances can bypass rate limit (each checks own DB).

**Acceptance:** Acceptable for single-instance deployment. Migrate to Redis if scaling horizontally.

### Trade-off: Synchronous PDF Reading
**Decision:** Read PDF files from disk synchronously in webhook handler.

**Consequence:** Large PDF files block webhook response.

**Acceptance:** Webhook timeout is 30s, typical PDFs <10MB, acceptable latency. Move to background task if needed.

## Migration Plan

**Phase 1: Core Implementation**
1. Deploy database migrations (auto-generated via Alembic)
2. Add Resend/Stripe API keys to production .env
3. Deploy application code
4. Configure Stripe webhook endpoint: `https://harmoni.app/api/stripe/webhook`
5. Test with Stripe test mode

**Phase 2: Production Rollout**
1. Switch Stripe to live mode
2. Test end-to-end flow with real payment (refund afterward)
3. Monitor webhook delivery and email logs
4. Enable production CORS origins

**Rollback:** Remove routers from main.py, keep migrations (tables harmless if unused).

## Open Questions

1. **Currency support:** Only USD or multiple currencies?
   - **Proposed:** Start with single currency (USD), add currency field to tariffs later.

2. **Verification code resend limit:** Should we limit total codes per email per day?
   - **Proposed:** Monitor abuse first, add daily limit if needed.

3. **Payment confirmation page:** Should backend provide success/failure page redirect?
   - **Proposed:** Frontend handles display, backend provides status endpoint only.

4. **PDF attachment size limit:** What if tariff PDFs exceed email provider limits?
   - **Proposed:** Resend limit is 40MB per email, enforce 10MB per tariff via file upload validation.

5. **User deletion/GDPR:** How to handle data deletion requests?
   - **Proposed:** Add `deleted_at` soft delete field (future enhancement).
