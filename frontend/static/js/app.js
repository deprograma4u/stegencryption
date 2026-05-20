/**
 * Frontend JavaScript for Secure Steganography System
 */

// API Base URL
const API_BASE = '/api';

// Global state
let currentEmbedFile = null;
let currentExtractFile = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupFileUploads();
    setupForms();
    loadKeys();
});

/**
 * Setup file upload areas with drag and drop
 */
function setupFileUploads() {
    // Embed image upload
    const embedUploadArea = document.getElementById('embedUploadArea');
    const embedImageInput = document.getElementById('embedImage');
    
    // Click handler removed - button handles it
    embedUploadArea.addEventListener('dragover', handleDragOver);
    embedUploadArea.addEventListener('dragleave', handleDragLeave);
    embedUploadArea.addEventListener('drop', (e) => handleDrop(e, 'embed'));
    embedImageInput.addEventListener('change', (e) => handleFileSelect(e, 'embed'));
    
    // Extract image upload
    const extractUploadArea = document.getElementById('extractUploadArea');
    const extractImageInput = document.getElementById('extractImage');
    
    // Click handler removed - button handles it
    extractUploadArea.addEventListener('dragover', handleDragOver);
    extractUploadArea.addEventListener('dragleave', handleDragLeave);
    extractUploadArea.addEventListener('drop', (e) => handleDrop(e, 'extract'));
    extractImageInput.addEventListener('change', (e) => handleFileSelect(e, 'extract'));
}

/**
 * Setup form submissions
 */
function setupForms() {
    // Embed form
    document.getElementById('embedForm').addEventListener('submit', handleEmbedSubmit);
    
    // Extract form
    document.getElementById('extractForm').addEventListener('submit', handleExtractSubmit);
    
    // Generate keys form
    document.getElementById('generateKeysForm').addEventListener('submit', handleGenerateKeys);
}

/**
 * Handle drag over event
 */
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

/**
 * Handle drag leave event
 */
function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
}

/**
 * Handle file drop event
 */
function handleDrop(e, type) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0], type);
    }
}

/**
 * Handle file selection from input
 */
function handleFileSelect(e, type) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file, type);
    }
}

/**
 * Process selected file
 */
function handleFile(file, type) {
    if (!file.type.startsWith('image/')) {
        showAlert('Please select an image file', 'danger');
        return;
    }
    
    if (file.size > 16 * 1024 * 1024) { // 16MB limit
        showAlert('File size exceeds 16MB limit', 'danger');
        return;
    }
    
    if (type === 'embed') {
        currentEmbedFile = file;
        showImagePreview(file, 'embedImagePreview');
    } else {
        currentExtractFile = file;
        showImagePreview(file, 'extractImagePreview');
    }
}

/**
 * Show image preview
 */
function showImagePreview(file, previewId) {
    const preview = document.getElementById(previewId);
    const reader = new FileReader();
    
    reader.onload = function(e) {
        preview.innerHTML = `
            <div class="card">
                <img src="${e.target.result}" class="card-img-top" style="max-height: 200px; object-fit: cover;">
                <div class="card-body p-2">
                    <small class="text-muted">
                        <strong>${file.name}</strong><br>
                        Size: ${formatFileSize(file.size)}
                    </small>
                </div>
            </div>
        `;
    };
    
    reader.readAsDataURL(file);
}

/**
 * Handle embed form submission
 */
async function handleEmbedSubmit(e) {
    e.preventDefault();
    
    if (!currentEmbedFile) {
        showAlert('Please select an image', 'warning');
        return;
    }
    
    const message = document.getElementById('embedMessage').value;
    if (!message.trim()) {
        showAlert('Please enter a message', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('image', currentEmbedFile);
    formData.append('message', message);
    formData.append('sender_key', document.getElementById('senderKey').value);
    formData.append('recipient_key', document.getElementById('recipientKey').value);
    
    const seed = document.getElementById('embedSeed').value;
    if (seed) {
        formData.append('seed', seed);
    }
    
    setLoading('embedForm', true);
    
    try {
        const response = await fetch(`${API_BASE}/stego/embed`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            // Download the stego image
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `stego_${Date.now()}.png`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showAlert('Message embedded successfully! Stego image downloaded.', 'success');
            showEmbedResult({
                success: true,
                message: 'Message embedded successfully',
                downloadTriggered: true
            });
        } else {
            const error = await response.json();
            showAlert(error.message || 'Embedding failed', 'danger');
            showEmbedResult({ success: false, error: error.message });
        }
    } catch (error) {
        showAlert('Network error: ' + error.message, 'danger');
        showEmbedResult({ success: false, error: error.message });
    } finally {
        setLoading('embedForm', false);
    }
}

/**
 * Handle extract form submission
 */
async function handleExtractSubmit(e) {
    e.preventDefault();
    
    if (!currentExtractFile) {
        showAlert('Please select a stego image', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('image', currentExtractFile);
    formData.append('sender_key', document.getElementById('extractSenderKey').value);
    formData.append('recipient_key', document.getElementById('extractRecipientKey').value);
    
    const seed = document.getElementById('extractSeed').value;
    if (seed) {
        formData.append('seed', seed);
    }
    
    setLoading('extractForm', true);
    
    try {
        const response = await fetch(`${API_BASE}/stego/extract`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showAlert('Message extracted successfully!', 'success');
            showExtractResult(result);
        } else {
            showAlert(result.message || 'Extraction failed', 'danger');
            showExtractResult({ success: false, error: result.message });
        }
    } catch (error) {
        showAlert('Network error: ' + error.message, 'danger');
        showExtractResult({ success: false, error: error.message });
    } finally {
        setLoading('extractForm', false);
    }
}

/**
 * Handle generate keys form submission
 */
async function handleGenerateKeys(e) {
    e.preventDefault();
    
    const userName = document.getElementById('userName').value.trim();
    if (!userName) {
        showAlert('Please enter a user name', 'warning');
        return;
    }
    
    setLoading('generateKeysForm', true);
    
    try {
        const response = await fetch(`${API_BASE}/keys/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_name: userName })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showAlert(`Keys generated successfully for ${userName}!`, 'success');
            document.getElementById('userName').value = '';
            loadKeys(); // Refresh the keys list
        } else {
            showAlert(result.message || 'Key generation failed', 'danger');
        }
    } catch (error) {
        showAlert('Network error: ' + error.message, 'danger');
    } finally {
        setLoading('generateKeysForm', false);
    }
}

/**
 * Load and display available keys
 */
async function loadKeys() {
    try {
        const response = await fetch(`${API_BASE}/keys/list`);
        const result = await response.json();
        
        if (response.ok && result.success) {
            displayKeys(result.data);
        } else {
            console.error('Failed to load keys:', result.message);
        }
    } catch (error) {
        console.error('Network error loading keys:', error);
    }
}

/**
 * Display keys in the keys list
 */
function displayKeys(keysData) {
    const keysList = document.getElementById('keysList');
    
    if (keysData.total_keys === 0) {
        keysList.innerHTML = '<p class="text-muted">No keys available. Generate some keys to get started.</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    
    // Display RSA keys
    if (keysData.rsa_keys.length > 0) {
        html += '<h6 class="mt-3 mb-2">RSA Key Pairs:</h6>';
        keysData.rsa_keys.forEach(key => {
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-key me-2"></i>${key}</span>
                    <span class="badge bg-primary">RSA</span>
                </div>
            `;
        });
    }
    
    // Display AES keys
    if (keysData.aes_keys.length > 0) {
        html += '<h6 class="mt-3 mb-2">AES Keys:</h6>';
        keysData.aes_keys.forEach(key => {
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-lock me-2"></i>${key}</span>
                    <span class="badge bg-success">AES</span>
                </div>
            `;
        });
    }
    
    html += '</div>';
    keysList.innerHTML = html;
}

/**
 * Show embed result
 */
function showEmbedResult(result) {
    const resultDiv = document.getElementById('embedResult');
    
    if (result.success) {
        resultDiv.innerHTML = `
            <div class="alert alert-success">
                <h6><i class="fas fa-check-circle me-2"></i>Embedding Successful!</h6>
                <p class="mb-0">${result.message}</p>
                ${result.downloadTriggered ? '<p class="mb-0 mt-2">Stego image has been downloaded to your device.</p>' : ''}
            </div>
        `;
    } else {
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <h6><i class="fas fa-exclamation-triangle me-2"></i>Embedding Failed</h6>
                <p class="mb-0">${result.error}</p>
            </div>
        `;
    }
    
    resultDiv.style.display = 'block';
}

/**
 * Show extract result
 */
function showExtractResult(result) {
    const resultDiv = document.getElementById('extractResult');
    
    if (result.success) {
        resultDiv.innerHTML = `
            <div class="alert alert-success">
                <h6><i class="fas fa-check-circle me-2"></i>Extraction Successful!</h6>
                <div class="mt-3">
                    <strong>Extracted Message:</strong>
                    <div class="bg-white p-3 rounded mt-2">
                        <pre class="mb-0">${result.data.message}</pre>
                    </div>
                </div>
                <div class="mt-3">
                    <small class="text-muted">
                        <strong>Verification Status:</strong> ${result.data.metadata.verification_status}<br>
                        <strong>Sender:</strong> ${result.data.metadata.sender}<br>
                        <strong>Timestamp:</strong> ${result.data.metadata.timestamp}
                    </small>
                </div>
            </div>
        `;
    } else {
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <h6><i class="fas fa-exclamation-triangle me-2"></i>Extraction Failed</h6>
                <p class="mb-0">${result.error}</p>
            </div>
        `;
    }
    
    resultDiv.style.display = 'block';
}

/**
 * Set loading state for forms
 */
function setLoading(formId, loading) {
    const form = document.getElementById(formId);
    const buttons = form.querySelectorAll('button[type="submit"]');
    const spinners = form.querySelectorAll('.loading');
    
    buttons.forEach(button => {
        button.disabled = loading;
    });
    
    spinners.forEach(spinner => {
        spinner.style.display = loading ? 'inline-block' : 'none';
    });
}

/**
 * Show alert message
 */
function showAlert(message, type) {
    // Create alert container if it doesn't exist
    let alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alertContainer';
        alertContainer.className = 'position-fixed top-0 start-50 translate-middle-x mt-3';
        alertContainer.style.zIndex = '9999';
        document.body.appendChild(alertContainer);
    }
    
    const alertId = 'alert-' + Date.now();
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertContainer.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
