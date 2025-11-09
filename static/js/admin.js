// Admin Panel JavaScript

// Modal Management
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close modal on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        closeModal(e.target.id);
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            closeModal(modal.id);
        });
    }
});

// Confirm Delete
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

// Feature Tag Management
let featureCounter = 0;

function addFeature() {
    const input = document.getElementById('feature-input');
    const value = input.value.trim();

    if (!value) return;

    const container = document.getElementById('features-container');
    const tag = document.createElement('div');
    tag.className = 'feature-tag';
    tag.innerHTML = `
        <span>${escapeHtml(value)}</span>
        <button type="button" onclick="removeFeature(this)">×</button>
        <input type="hidden" name="features" value="${escapeHtml(value)}">
    `;

    container.appendChild(tag);
    input.value = '';
}

function removeFeature(button) {
    button.closest('.feature-tag').remove();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Handle Enter key in feature input
document.addEventListener('DOMContentLoaded', () => {
    const featureInput = document.getElementById('feature-input');
    if (featureInput) {
        featureInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addFeature();
            }
        });
    }
});

// File Upload Preview
function handleFileUpload(input) {
    const file = input.files[0];
    if (!file) return;

    const preview = document.getElementById('file-preview');
    if (preview) {
        const fileSize = (file.size / 1024 / 1024).toFixed(2);
        preview.innerHTML = `
            <div class="file-info">
                <span class="file-icon">📄</span>
                <div>
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${fileSize} MB</div>
                </div>
            </div>
        `;
    }
}

// Auto-hide alerts
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

// Form Submit with Loading State
function submitWithLoading(form, button) {
    button.disabled = true;
    button.innerHTML = `<span class="loading"></span> ${button.textContent}`;
    form.submit();
}

// Price Formatting (cents to dollars)
function formatPrice(cents) {
    return `$${(cents / 100).toFixed(2)}`;
}

// File Size Formatting
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
