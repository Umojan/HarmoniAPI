/**
 * Harmoni Checkout - Stripe Elements Integration
 * Handles user verification and payment processing
 */

// ============================================================================
// Global State
// ============================================================================

const state = {
    currentStep: 'user-info',
    selectedTariffId: TARIFF_ID || null,
    userInfo: {
        name: '',
        surname: '',
        email: ''
    },
    paymentIntentClientSecret: null,
    paymentId: null,
    isVerified: false,
    resendTimer: 60
};

let stripe = null;
let cardElement = null;
let resendIntervalId = null;

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Initialize Stripe
        stripe = Stripe(STRIPE_PUBLIC_KEY);

        // Check if we need to show tariff selection
        if (!state.selectedTariffId) {
            await loadTariffs();
            showStep('step-tariff');
        } else {
            showStep('step-user-info');
        }

        // Setup event listeners
        setupEventListeners();
    } catch (error) {
        console.error('Initialization error:', error);
        showError('step-user-info-error', 'Failed to initialize payment system. Please refresh the page.');
    }
});

// ============================================================================
// Step Management
// ============================================================================

function showStep(stepId) {
    // Hide all steps
    document.querySelectorAll('.step').forEach(step => {
        step.style.display = 'none';
    });

    // Show target step
    const targetStep = document.getElementById(stepId);
    if (targetStep) {
        targetStep.style.display = 'block';
        state.currentStep = stepId;
    }
}

// ============================================================================
// Tariff Loading & Selection
// ============================================================================

async function loadTariffs() {
    try {
        const response = await fetch(`${API_BASE_URL}/tariffs`);
        if (!response.ok) throw new Error('Failed to load tariffs');

        const tariffs = await response.json();
        renderTariffs(tariffs);
    } catch (error) {
        console.error('Error loading tariffs:', error);
        showError('step-user-info-error', 'Failed to load available plans. Please refresh the page.');
    }
}

function renderTariffs(tariffs) {
    const tariffList = document.getElementById('tariff-list');
    tariffList.innerHTML = '';

    tariffs.forEach(tariff => {
        const card = document.createElement('div');
        card.className = 'tariff-card';
        card.innerHTML = `
            <div class="tariff-name">${escapeHtml(tariff.name)}</div>
            <div class="tariff-price">$${(tariff.base_price / 100).toFixed(2)}</div>
            ${tariff.description ? `<div class="tariff-description">${escapeHtml(tariff.description)}</div>` : ''}
        `;

        card.addEventListener('click', () => {
            document.querySelectorAll('.tariff-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            state.selectedTariffId = tariff.id;
        });

        tariffList.appendChild(card);
    });

    // Add continue button
    const continueBtn = document.createElement('button');
    continueBtn.className = 'btn-primary';
    continueBtn.textContent = 'Continue';
    continueBtn.onclick = () => {
        if (!state.selectedTariffId) {
            alert('Please select a plan');
            return;
        }
        showStep('step-user-info');
    };
    tariffList.appendChild(continueBtn);
}

// ============================================================================
// Event Listeners Setup
// ============================================================================

function setupEventListeners() {
    // User info form
    document.getElementById('user-info-form').addEventListener('submit', handleUserInfoSubmit);

    // Verification form
    document.getElementById('verification-form').addEventListener('submit', handleVerificationSubmit);

    // Resend button
    document.getElementById('btn-resend').addEventListener('click', handleResendCode);

    // Payment form
    document.getElementById('payment-form').addEventListener('submit', handlePaymentSubmit);
}

// ============================================================================
// Step 1: User Information
// ============================================================================

async function handleUserInfoSubmit(e) {
    e.preventDefault();

    const name = document.getElementById('name').value.trim();
    const surname = document.getElementById('surname').value.trim();
    const email = document.getElementById('email').value.trim();

    // Validate
    if (!name || !surname || !email) {
        showError('user-info-error', 'All fields are required');
        return;
    }

    // Save user info
    state.userInfo = { name, surname, email };

    // Disable button and show spinner
    setButtonLoading('btn-user-info', true);
    clearError('user-info-error');

    try {
        // Check if email is already verified
        const checkResponse = await fetch(`${API_BASE_URL}/auth/check-email/${encodeURIComponent(email)}`);
        if (!checkResponse.ok) throw new Error('Failed to check email');

        const checkData = await checkResponse.json();

        if (checkData.is_verified) {
            // User already verified, proceed to payment
            state.isVerified = true;
            await initializePayment();
        } else {
            // Send verification code
            await sendVerificationCode();
        }
    } catch (error) {
        console.error('User info submit error:', error);
        showError('user-info-error', error.message || 'An error occurred. Please try again.');
    } finally {
        setButtonLoading('btn-user-info', false);
    }
}

async function sendVerificationCode() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/send-verification-code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state.userInfo)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to send verification code');
        }

        // Show verification step
        document.getElementById('verification-email').textContent = state.userInfo.email;
        showStep('step-verification');
        startResendTimer();
    } catch (error) {
        // Handle rate limit error
        if (error.message.includes('Rate limit')) {
            showError('user-info-error', 'Too many requests. Please wait before trying again.');
        } else {
            showError('user-info-error', error.message);
        }
        throw error;
    }
}

// ============================================================================
// Step 2: Email Verification
// ============================================================================

async function handleVerificationSubmit(e) {
    e.preventDefault();

    const code = document.getElementById('code').value.trim();

    if (!/^\d{6}$/.test(code)) {
        showError('verification-error', 'Please enter a valid 6-digit code');
        return;
    }

    setButtonLoading('btn-verify', true);
    clearError('verification-error');

    try {
        const response = await fetch(`${API_BASE_URL}/auth/verify-code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Invalid or expired code');
        }

        const data = await response.json();
        state.isVerified = true;

        // Stop resend timer
        if (resendIntervalId) {
            clearInterval(resendIntervalId);
        }

        // Proceed to payment
        await initializePayment();
    } catch (error) {
        console.error('Verification error:', error);
        showError('verification-error', error.message || 'Verification failed. Please try again.');
    } finally {
        setButtonLoading('btn-verify', false);
    }
}

function startResendTimer() {
    state.resendTimer = 60;
    const btn = document.getElementById('btn-resend');
    const timer = document.getElementById('resend-timer');

    btn.disabled = true;

    resendIntervalId = setInterval(() => {
        state.resendTimer--;
        timer.textContent = `(${state.resendTimer}s)`;

        if (state.resendTimer <= 0) {
            clearInterval(resendIntervalId);
            btn.disabled = false;
            timer.textContent = '';
        }
    }, 1000);
}

async function handleResendCode() {
    setButtonLoading('btn-resend', true);
    clearError('verification-error');

    try {
        await sendVerificationCode();
    } catch (error) {
        // Error already shown in sendVerificationCode
    } finally {
        setButtonLoading('btn-resend', false);
    }
}

// ============================================================================
// Step 3: Payment Initialization
// ============================================================================

async function initializePayment() {
    if (!state.selectedTariffId) {
        showError('user-info-error', 'Please select a plan first');
        return;
    }

    try {
        // Create Payment Intent
        const response = await fetch(`${API_BASE_URL}/stripe/payment-intent`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: state.userInfo.email,
                tariff_id: state.selectedTariffId
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to initialize payment');
        }

        const data = await response.json();
        state.paymentIntentClientSecret = data.client_secret;
        state.paymentId = data.payment_id;

        // Update summary
        document.getElementById('summary-tariff-name').textContent = 'Selected Plan';
        document.getElementById('summary-amount').textContent = `$${(data.amount / 100).toFixed(2)}`;

        // Create Stripe Elements
        const elements = stripe.elements();
        cardElement = elements.create('card', {
            style: {
                base: {
                    fontSize: '16px',
                    color: '#1A1A1A',
                    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                    '::placeholder': {
                        color: '#D1D1D1'
                    }
                },
                invalid: {
                    color: '#EF4444',
                    iconColor: '#EF4444'
                }
            },
            hidePostalCode: false
        });

        cardElement.mount('#card-element');

        // Listen for card errors
        cardElement.on('change', (event) => {
            const displayError = document.getElementById('card-errors');
            if (event.error) {
                displayError.textContent = event.error.message;
            } else {
                displayError.textContent = '';
            }
        });

        // Show payment step
        showStep('step-payment');
    } catch (error) {
        console.error('Payment initialization error:', error);
        showError('user-info-error', error.message || 'Failed to initialize payment');
    }
}

// ============================================================================
// Step 4: Payment Processing
// ============================================================================

async function handlePaymentSubmit(e) {
    e.preventDefault();

    setButtonLoading('btn-pay', true);
    clearError('payment-error');

    try {
        // Confirm card payment
        const {paymentIntent, error} = await stripe.confirmCardPayment(
            state.paymentIntentClientSecret,
            {
                payment_method: {
                    card: cardElement,
                    billing_details: {
                        name: `${state.userInfo.name} ${state.userInfo.surname}`,
                        email: state.userInfo.email
                    }
                }
            }
        );

        if (error) {
            // Handle specific error codes
            if (error.code === 'card_declined') {
                throw new Error('Your card was declined. Please check your card details or try a different card.');
            } else if (error.code === 'insufficient_funds') {
                throw new Error('Insufficient funds. Please use a different card.');
            } else {
                throw new Error(error.message || 'Payment failed. Please try again.');
            }
        }

        // Check payment intent status after confirmation
        if (!paymentIntent) {
            throw new Error('Payment confirmation failed. Please try again.');
        }

        // If payment requires additional action (3D Secure, etc.), Stripe Elements will handle it
        // Otherwise, payment is processing or succeeded
        if (paymentIntent.status === 'succeeded') {
            // Immediate success
            window.location.href = `/payment/success?email=${encodeURIComponent(state.userInfo.email)}`;
            return;
        }

        // Show processing state
        showStep('step-processing');

        // Poll payment status (wait for webhook to process)
        await pollPaymentStatus(state.paymentId);
    } catch (error) {
        console.error('Payment error:', error);
        showError('payment-error', error.message || 'Payment failed. Please try again.');
        setButtonLoading('btn-pay', false);
    }
}

// ============================================================================
// Payment Status Polling
// ============================================================================

async function pollPaymentStatus(paymentId, maxAttempts = 20, interval = 2000) {
    let attempts = 0;

    const poll = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/stripe/payment/${paymentId}/status`);
            if (!response.ok) throw new Error('Failed to check payment status');

            const data = await response.json();

            if (data.status === 'succeeded') {
                // Payment successful - webhook processed
                window.location.href = `/payment/success?email=${encodeURIComponent(state.userInfo.email)}`;
                return;
            }

            // These statuses mean payment failed after confirmation attempt
            if (data.status === 'canceled' || data.status === 'failed') {
                window.location.href = `/payment/error?reason=${encodeURIComponent('Payment was not successful')}&tariff_id=${state.selectedTariffId}`;
                return;
            }

            // Processing, requires_capture, or still requires_payment_method (webhook pending)
            // Continue polling
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(poll, interval);
            } else {
                // Timeout - payment is taking too long
                window.location.href = `/payment/error?reason=${encodeURIComponent('Payment is taking longer than expected. Please check your email for confirmation.')}&tariff_id=${state.selectedTariffId}`;
            }
        } catch (error) {
            console.error('Poll error:', error);
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(poll, interval);
            } else {
                window.location.href = `/payment/error?reason=${encodeURIComponent('Unable to verify payment status. Please contact support.')}&tariff_id=${state.selectedTariffId}`;
            }
        }
    };

    poll();
}

// ============================================================================
// UI Helpers
// ============================================================================

function setButtonLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    button.disabled = isLoading;
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
    }
}

function clearError(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = '';
    }
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
