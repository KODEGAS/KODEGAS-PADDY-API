// Global variables
let currentEditingDisease = null;
let currentEditingType = null;

// Authentication helper
function getAuthHeaders() {
    const auth = sessionStorage.getItem('auth');
    if (!auth) {
        window.location.href = '/admin';
        return {};
    }
    return {
        'Authorization': 'Basic ' + auth,
        'Content-Type': 'application/json'
    };
}

// Logout function
function logout() {
    sessionStorage.removeItem('auth');
    window.location.href = '/admin';
}

// Tab management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');

    // Load data for the tab
    if (tabName === 'disease-info') {
        loadDiseaseInfo();
    } else if (tabName === 'medicines') {
        loadMedicines();
    }
}

// Load disease information
async function loadDiseaseInfo() {
    try {
        const response = await fetch('/admin/api/disease-info', {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            displayDiseaseInfo(data);
        } else {
            console.error('Failed to load disease info');
        }
    } catch (error) {
        console.error('Error loading disease info:', error);
    }
}

// Display disease information
function displayDiseaseInfo(data) {
    const container = document.getElementById('disease-info-list');
    container.innerHTML = '';

    Object.entries(data).forEach(([key, info]) => {
        const item = document.createElement('div');
        item.className = 'data-item';
        item.innerHTML = `
            <h3>
                ${info.disease_name || key}
                <div class="data-item-actions">
                    <button onclick="editDiseaseInfo('${key}')" class="btn btn-success">Edit</button>
                    <button onclick="deleteDiseaseInfo('${key}')" class="btn btn-danger">Delete</button>
                </div>
            </h3>
            <p><strong>Caused by:</strong> ${info.caused_by || 'N/A'}</p>
            <p><strong>Description:</strong> ${info.description || 'N/A'}</p>
            <p><strong>Symptoms:</strong> ${Array.isArray(info.symptoms) ? info.symptoms.join(', ') : 'N/A'}</p>
        `;
        container.appendChild(item);
    });
}

// Load medicines
async function loadMedicines() {
    try {
        const response = await fetch('/admin/api/disease-medicines', {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            displayMedicines(data);
        } else {
            console.error('Failed to load medicines');
        }
    } catch (error) {
        console.error('Error loading medicines:', error);
    }
}

// Display medicines
function displayMedicines(data) {
    const container = document.getElementById('medicines-list');
    container.innerHTML = '';

    Object.entries(data).forEach(([key, medicines]) => {
        const item = document.createElement('div');
        item.className = 'data-item';

        const medicinesList = Array.isArray(medicines) ?
            medicines.map(med => `<li>${med.name || 'Unnamed'} (${med.brand || 'No brand'})</li>`).join('') :
            '<li>No medicines listed</li>';

        item.innerHTML = `
            <h3>
                ${key.replace(/_/g, ' ').toUpperCase()}
                <div class="data-item-actions">
                    <button onclick="editMedicines('${key}')" class="btn btn-success">Edit</button>
                    <button onclick="deleteMedicines('${key}')" class="btn btn-danger">Delete</button>
                </div>
            </h3>
            <p><strong>Medicines:</strong></p>
            <ul>${medicinesList}</ul>
        `;
        container.appendChild(item);
    });
}

// Show add form
function showAddForm(type) {
    currentEditingDisease = null;
    currentEditingType = type;

    if (type === 'info') {
        document.getElementById('info-form-title').textContent = 'Add Disease Information';
        document.getElementById('diseaseInfoForm').reset();
        document.getElementById('disease-info-form').classList.remove('hidden');
    } else if (type === 'medicines') {
        document.getElementById('medicines-form-title').textContent = 'Add Medicine Set';
        document.getElementById('medicinesForm').reset();
        resetMedicinesContainer();
        document.getElementById('medicines-form').classList.remove('hidden');
    }
}

// Hide form
function hideForm(type) {
    if (type === 'info') {
        document.getElementById('disease-info-form').classList.add('hidden');
    } else if (type === 'medicines') {
        document.getElementById('medicines-form').classList.add('hidden');
    }
}

// Edit disease info
async function editDiseaseInfo(diseaseKey) {
    try {
        const response = await fetch('/admin/api/disease-info', {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            const info = data[diseaseKey];

            currentEditingDisease = diseaseKey;
            currentEditingType = 'info';

            // Populate form
            document.getElementById('info-disease-key').value = diseaseKey;
            document.getElementById('info-disease-name').value = info.disease_name || '';
            document.getElementById('info-caused-by').value = info.caused_by || '';
            document.getElementById('info-description').value = info.description || '';
            document.getElementById('info-symptoms').value = Array.isArray(info.symptoms) ? info.symptoms.join('\n') : '';
            document.getElementById('info-factors').value = Array.isArray(info.factors) ? info.factors.join('\n') : '';
            document.getElementById('info-prevention').value = Array.isArray(info.prevention) ? info.prevention.join('\n') : '';
            document.getElementById('info-treatment').value = info.treatment || '';
            document.getElementById('info-note').value = info.note || '';

            document.getElementById('info-form-title').textContent = 'Edit Disease Information';
            document.getElementById('disease-info-form').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error loading disease info for edit:', error);
    }
}

// Edit medicines
async function editMedicines(diseaseKey) {
    try {
        const response = await fetch('/admin/api/disease-medicines', {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            const medicines = data[diseaseKey];

            currentEditingDisease = diseaseKey;
            currentEditingType = 'medicines';

            document.getElementById('med-disease-key').value = diseaseKey;

            // Populate medicines
            resetMedicinesContainer();
            if (Array.isArray(medicines)) {
                medicines.forEach((med, index) => {
                    if (index > 0) addMedicineItem();
                    const container = document.querySelectorAll('.medicine-item')[index];
                    if (container) {
                        container.querySelector('.med-name').value = med.name || '';
                        container.querySelector('.med-brand').value = med.brand || '';
                        container.querySelector('.med-type').value = med.type || '';
                        container.querySelector('.med-ingredient').value = med.active_ingredient || '';
                        container.querySelector('.med-pack').value = med.pack_size || '';
                        container.querySelector('.med-price').value = med.price || '';
                        container.querySelector('.med-rate').value = med.application_rate || '';
                        container.querySelector('.med-priority').value = med.priority || '';
                        container.querySelector('.med-method').value = med.method || '';
                        container.querySelector('.med-note').value = med.note || '';
                    }
                });
            }

            document.getElementById('medicines-form-title').textContent = 'Edit Medicine Set';
            document.getElementById('medicines-form').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error loading medicines for edit:', error);
    }
}

// Delete disease info
async function deleteDiseaseInfo(diseaseKey) {
    if (confirm(`Are you sure you want to delete disease info for "${diseaseKey}"?`)) {
        try {
            const response = await fetch(`/admin/api/disease-info/${diseaseKey}`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            });

            if (response.ok) {
                loadDiseaseInfo();
            } else {
                alert('Failed to delete disease info');
            }
        } catch (error) {
            console.error('Error deleting disease info:', error);
        }
    }
}

// Delete medicines
async function deleteMedicines(diseaseKey) {
    if (confirm(`Are you sure you want to delete medicines for "${diseaseKey}"?`)) {
        try {
            const response = await fetch(`/admin/api/disease-medicines/${diseaseKey}`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            });

            if (response.ok) {
                loadMedicines();
            } else {
                alert('Failed to delete medicines');
            }
        } catch (error) {
            console.error('Error deleting medicines:', error);
        }
    }
}

// Add medicine item
function addMedicineItem() {
    const container = document.getElementById('medicines-container');
    const count = container.children.length + 1;

    const medicineItem = document.createElement('div');
    medicineItem.className = 'medicine-item';
    medicineItem.innerHTML = `
        <h4>Medicine ${count}</h4>
        <div class="form-row">
            <input type="text" placeholder="Medicine Name" class="med-name" required>
            <input type="text" placeholder="Brand" class="med-brand">
            <input type="text" placeholder="Type" class="med-type">
        </div>
        <div class="form-row">
            <input type="text" placeholder="Active Ingredient" class="med-ingredient">
            <input type="text" placeholder="Pack Size" class="med-pack">
            <input type="text" placeholder="Price" class="med-price">
        </div>
        <div class="form-row">
            <input type="text" placeholder="Application Rate" class="med-rate">
            <input type="number" placeholder="Priority" class="med-priority" min="1">
            <button type="button" onclick="removeMedicineItem(this)" class="btn btn-danger">Remove</button>
        </div>
        <textarea placeholder="Method" class="med-method" rows="2"></textarea>
        <textarea placeholder="Note" class="med-note" rows="2"></textarea>
    `;

    container.appendChild(medicineItem);
}

// Remove medicine item
function removeMedicineItem(button) {
    button.closest('.medicine-item').remove();

    // Update numbering
    document.querySelectorAll('.medicine-item h4').forEach((h4, index) => {
        h4.textContent = `Medicine ${index + 1}`;
    });
}

// Reset medicines container
function resetMedicinesContainer() {
    const container = document.getElementById('medicines-container');
    container.innerHTML = `
        <div class="medicine-item">
            <h4>Medicine 1</h4>
            <div class="form-row">
                <input type="text" placeholder="Medicine Name" class="med-name" required>
                <input type="text" placeholder="Brand" class="med-brand">
                <input type="text" placeholder="Type" class="med-type">
            </div>
            <div class="form-row">
                <input type="text" placeholder="Active Ingredient" class="med-ingredient">
                <input type="text" placeholder="Pack Size" class="med-pack">
                <input type="text" placeholder="Price" class="med-price">
            </div>
            <div class="form-row">
                <input type="text" placeholder="Application Rate" class="med-rate">
                <input type="number" placeholder="Priority" class="med-priority" min="1">
            </div>
            <textarea placeholder="Method" class="med-method" rows="2"></textarea>
            <textarea placeholder="Note" class="med-note" rows="2"></textarea>
        </div>
    `;
}

// Form submissions
document.getElementById('diseaseInfoForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const diseaseKey = document.getElementById('info-disease-key').value;
    const formData = {
        disease_name: document.getElementById('info-disease-name').value,
        caused_by: document.getElementById('info-caused-by').value,
        description: document.getElementById('info-description').value,
        symptoms: document.getElementById('info-symptoms').value.split('\n').filter(s => s.trim()),
        factors: document.getElementById('info-factors').value.split('\n').filter(s => s.trim()),
        prevention: document.getElementById('info-prevention').value.split('\n').filter(s => s.trim()),
        treatment: document.getElementById('info-treatment').value,
        note: document.getElementById('info-note').value
    };

    try {
        const url = currentEditingDisease ?
            `/admin/api/disease-info/${currentEditingDisease}` :
            `/admin/api/disease-info/${diseaseKey}`;

        const response = await fetch(url, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            hideForm('info');
            loadDiseaseInfo();
        } else {
            alert('Failed to save disease info');
        }
    } catch (error) {
        console.error('Error saving disease info:', error);
    }
});

document.getElementById('medicinesForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const diseaseKey = document.getElementById('med-disease-key').value;
    const medicines = [];

    document.querySelectorAll('.medicine-item').forEach(item => {
        const medicine = {
            name: item.querySelector('.med-name').value,
            brand: item.querySelector('.med-brand').value,
            type: item.querySelector('.med-type').value,
            active_ingredient: item.querySelector('.med-ingredient').value,
            pack_size: item.querySelector('.med-pack').value,
            price: item.querySelector('.med-price').value,
            application_rate: item.querySelector('.med-rate').value,
            priority: parseInt(item.querySelector('.med-priority').value) || 1,
            method: item.querySelector('.med-method').value,
            note: item.querySelector('.med-note').value
        };

        if (medicine.name.trim()) {
            medicines.push(medicine);
        }
    });

    try {
        const url = currentEditingDisease ?
            `/admin/api/disease-medicines/${currentEditingDisease}` :
            `/admin/api/disease-medicines/${diseaseKey}`;

        const response = await fetch(url, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify(medicines)
        });

        if (response.ok) {
            hideForm('medicines');
            loadMedicines();
        } else {
            alert('Failed to save medicines');
        }
    } catch (error) {
        console.error('Error saving medicines:', error);
    }
});

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!sessionStorage.getItem('auth')) {
        window.location.href = '/admin';
        return;
    }

    // Load initial data
    loadDiseaseInfo();
});

// Mobile-specific enhancements
function initMobileEnhancements() {
    // Add touch feedback for buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('touchstart', function () {
            this.style.transform = 'scale(0.95)';
        });

        btn.addEventListener('touchend', function () {
            this.style.transform = 'scale(1)';
        });
    });

    // Prevent double-tap zoom on buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('touchend', function (e) {
            e.preventDefault();
        });
    });

    // Auto-resize textareas on mobile
    document.querySelectorAll('textarea').forEach(textarea => {
        textarea.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });

    // Close modal when tapping outside (mobile-friendly)
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('touchstart', function (e) {
            if (e.target === this) {
                const formType = this.id.includes('info') ? 'info' : 'medicines';
                hideForm(formType);
            }
        });
    });
}

// Enhanced form validation for mobile
function validateForm(formType) {
    const requiredFields = document.querySelectorAll(`#${formType === 'info' ? 'diseaseInfoForm' : 'medicinesForm'} [required]`);
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = '#dc3545';
            field.addEventListener('input', function () {
                this.style.borderColor = '#ddd';
            }, { once: true });
            isValid = false;
        }
    });

    if (!isValid) {
        // Show mobile-friendly error message
        showMobileAlert('Please fill in all required fields', 'error');
    }

    return isValid;
}

// Mobile-friendly alert system
function showMobileAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `mobile-alert ${type}`;
    alertDiv.textContent = message;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'error' ? '#dc3545' : type === 'success' ? '#28a745' : '#17a2b8'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 10000;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        max-width: 90%;
        text-align: center;
    `;

    document.body.appendChild(alertDiv);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        alertDiv.style.opacity = '0';
        alertDiv.style.transform = 'translateX(-50%) translateY(-20px)';
        setTimeout(() => alertDiv.remove(), 300);
    }, 3000);
}

// Detect mobile device
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Initialize mobile enhancements when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (isMobileDevice()) {
        initMobileEnhancements();

        // Add mobile class to body for CSS targeting
        document.body.classList.add('mobile-device');

        // Prevent zoom on input focus for iOS
        if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
            document.addEventListener('focusin', function (e) {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    document.querySelector('meta[name=viewport]').setAttribute(
                        'content',
                        'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'
                    );
                }
            });

            document.addEventListener('focusout', function (e) {
                document.querySelector('meta[name=viewport]').setAttribute(
                    'content',
                    'width=device-width, initial-scale=1.0, user-scalable=no'
                );
            });
        }
    }
});/
    / Enhanced medicine management functions

// Enhanced display medicines function
function displayMedicinesEnhanced(data) {
    const container = document.getElementById('medicines-list');
    container.innerHTML = '';

    Object.entries(data).forEach(([key, medicines]) => {
        const item = document.createElement('div');
        item.className = 'data-item';

        let medicinesDisplay = '<p>No medicines listed</p>';
        if (Array.isArray(medicines) && medicines.length > 0) {
            medicinesDisplay = medicines.map((med, index) => `
                <div class="medicine-display">
                    <h4>
                        ${med.name || 'Unnamed Medicine'}
                        <span class="priority-badge">Priority ${med.priority || 'N/A'}</span>
                    </h4>
                    <div class="medicine-details">
                        <div class="medicine-detail"><strong>Brand:</strong> ${med.brand || 'N/A'}</div>
                        <div class="medicine-detail"><strong>Type:</strong> ${med.type || 'N/A'}</div>
                        <div class="medicine-detail"><strong>Price:</strong> ${med.price || 'N/A'}</div>
                        <div class="medicine-detail"><strong>Pack Size:</strong> ${med.pack_size || 'N/A'}</div>
                    </div>
                    <div class="medicine-detail"><strong>Application:</strong> ${med.application_rate || 'N/A'}</div>
                    <div class="medicine-detail"><strong>Method:</strong> ${med.method || 'N/A'}</div>
                </div>
            `).join('');
        }

        item.innerHTML = `
            <h3>
                ${key.replace(/_/g, ' ').toUpperCase()}
                <div class="data-item-actions">
                    <button onclick="editMedicines('${key}')" class="btn btn-success">Edit</button>
                    <button onclick="deleteMedicines('${key}')" class="btn btn-danger">Delete</button>
                </div>
            </h3>
            <p><strong>${Array.isArray(medicines) ? medicines.length : 0} Medicine(s):</strong></p>
            ${medicinesDisplay}
        `;
        container.appendChild(item);
    });
}

// Enhanced add medicine item function
function addMedicineItemEnhanced() {
    const container = document.getElementById('medicines-container');
    const count = container.children.length + 1;

    const medicineItem = document.createElement('div');
    medicineItem.className = 'medicine-item';
    medicineItem.draggable = true;
    medicineItem.innerHTML = `
        <div class="medicine-header">
            <h4>Medicine ${count}</h4>
            <div class="medicine-controls">
                <button type="button" class="btn btn-sm move-up" onclick="moveMedicine(this, 'up')">↑</button>
                <button type="button" class="btn btn-sm move-down" onclick="moveMedicine(this, 'down')">↓</button>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeMedicineItem(this)">×</button>
            </div>
        </div>
        
        <!-- Basic Info -->
        <div class="form-section">
            <h5>Basic Information</h5>
            <div class="form-row">
                <input type="text" placeholder="Medicine Name *" class="med-name" required>
                <input type="text" placeholder="Brand" class="med-brand">
                <input type="text" placeholder="Type" class="med-type">
            </div>
            <div class="form-row">
                <input type="text" placeholder="Active Ingredient" class="med-ingredient">
                <input type="text" placeholder="Pack Size" class="med-pack">
                <input type="text" placeholder="Price (Rs. 1200)" class="med-price">
            </div>
        </div>
        
        <!-- Application Details -->
        <div class="form-section">
            <h5>Application Details</h5>
            <div class="form-row">
                <input type="text" placeholder="Application Rate" class="med-rate">
                <input type="text" placeholder="Frequency" class="med-frequency">
                <input type="number" placeholder="Priority (1-10)" class="med-priority" min="1" max="10">
            </div>
            <textarea placeholder="Method of Application" class="med-method" rows="2"></textarea>
        </div>
        
        <!-- Additional Info -->
        <div class="form-section">
            <h5>Additional Information</h5>
            <div class="form-row">
                <input type="url" placeholder="Image URL (optional)" class="med-image">
                <input type="text" placeholder="Availability" class="med-availability">
            </div>
            <textarea placeholder="Notes and Warnings" class="med-note" rows="2"></textarea>
        </div>
    `;

    container.appendChild(medicineItem);
    initializeDragAndDrop();
}

// Move medicine up/down
function moveMedicine(button, direction) {
    const medicineItem = button.closest('.medicine-item');
    const container = medicineItem.parentNode;

    if (direction === 'up' && medicineItem.previousElementSibling) {
        container.insertBefore(medicineItem, medicineItem.previousElementSibling);
    } else if (direction === 'down' && medicineItem.nextElementSibling) {
        container.insertBefore(medicineItem.nextElementSibling, medicineItem);
    }

    updateMedicineNumbers();
}

// Sort medicines by priority
function sortMedicinesByPriority() {
    const container = document.getElementById('medicines-container');
    const medicines = Array.from(container.children);

    medicines.sort((a, b) => {
        const priorityA = parseInt(a.querySelector('.med-priority').value) || 999;
        const priorityB = parseInt(b.querySelector('.med-priority').value) || 999;
        return priorityA - priorityB;
    });

    medicines.forEach(medicine => container.appendChild(medicine));
    updateMedicineNumbers();
}

// Update medicine numbers
function updateMedicineNumbers() {
    document.querySelectorAll('.medicine-item h4').forEach((h4, index) => {
        h4.textContent = `Medicine ${index + 1}`;
    });
}

// Enhanced reset medicines container
function resetMedicinesContainerEnhanced() {
    const container = document.getElementById('medicines-container');
    container.innerHTML = `
        <div class="medicine-item" draggable="true">
            <div class="medicine-header">
                <h4>Medicine 1</h4>
                <div class="medicine-controls">
                    <button type="button" class="btn btn-sm move-up" onclick="moveMedicine(this, 'up')">↑</button>
                    <button type="button" class="btn btn-sm move-down" onclick="moveMedicine(this, 'down')">↓</button>
                    <button type="button" class="btn btn-sm btn-danger" onclick="removeMedicineItem(this)">×</button>
                </div>
            </div>
            
            <!-- Basic Info -->
            <div class="form-section">
                <h5>Basic Information</h5>
                <div class="form-row">
                    <input type="text" placeholder="Medicine Name *" class="med-name" required>
                    <input type="text" placeholder="Brand" class="med-brand">
                    <input type="text" placeholder="Type" class="med-type">
                </div>
                <div class="form-row">
                    <input type="text" placeholder="Active Ingredient" class="med-ingredient">
                    <input type="text" placeholder="Pack Size" class="med-pack">
                    <input type="text" placeholder="Price (Rs. 1200)" class="med-price">
                </div>
            </div>
            
            <!-- Application Details -->
            <div class="form-section">
                <h5>Application Details</h5>
                <div class="form-row">
                    <input type="text" placeholder="Application Rate" class="med-rate">
                    <input type="text" placeholder="Frequency" class="med-frequency">
                    <input type="number" placeholder="Priority (1-10)" class="med-priority" min="1" max="10">
                </div>
                <textarea placeholder="Method of Application" class="med-method" rows="2"></textarea>
            </div>
            
            <!-- Additional Info -->
            <div class="form-section">
                <h5>Additional Information</h5>
                <div class="form-row">
                    <input type="url" placeholder="Image URL (optional)" class="med-image">
                    <input type="text" placeholder="Availability" class="med-availability">
                </div>
                <textarea placeholder="Notes and Warnings" class="med-note" rows="2"></textarea>
            </div>
        </div>
    `;
    initializeDragAndDrop();
}

// Enhanced edit medicines function
async function editMedicinesEnhanced(diseaseKey) {
    try {
        const response = await fetch('/admin/api/disease-medicines', {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            const medicines = data[diseaseKey];

            currentEditingDisease = diseaseKey;
            currentEditingType = 'medicines';

            document.getElementById('med-disease-key').value = diseaseKey;

            // Populate medicines with all fields
            resetMedicinesContainerEnhanced();
            if (Array.isArray(medicines)) {
                medicines.forEach((med, index) => {
                    if (index > 0) addMedicineItemEnhanced();
                    const container = document.querySelectorAll('.medicine-item')[index];
                    if (container) {
                        container.querySelector('.med-name').value = med.name || '';
                        container.querySelector('.med-brand').value = med.brand || '';
                        container.querySelector('.med-type').value = med.type || '';
                        container.querySelector('.med-ingredient').value = med.active_ingredient || '';
                        container.querySelector('.med-pack').value = med.pack_size || '';
                        container.querySelector('.med-price').value = med.price || '';
                        container.querySelector('.med-rate').value = med.application_rate || '';
                        container.querySelector('.med-frequency').value = med.frequency || '';
                        container.querySelector('.med-priority').value = med.priority || '';
                        container.querySelector('.med-method').value = med.method || '';
                        container.querySelector('.med-image').value = med.image_url || '';
                        container.querySelector('.med-availability').value = med.availability || '';
                        container.querySelector('.med-note').value = med.note || '';
                    }
                });
            }

            document.getElementById('medicines-form-title').textContent = 'Edit Medicine Set';
            document.getElementById('medicines-form').classList.remove('hidden');
            initializeDragAndDrop();
        }
    } catch (error) {
        console.error('Error loading medicines for edit:', error);
    }
}

// Enhanced form submission for medicines
function submitMedicinesFormEnhanced() {
    const diseaseKey = document.getElementById('med-disease-key').value;
    const medicines = [];

    document.querySelectorAll('.medicine-item').forEach(item => {
        const medicine = {
            name: item.querySelector('.med-name').value,
            brand: item.querySelector('.med-brand').value,
            type: item.querySelector('.med-type').value,
            active_ingredient: item.querySelector('.med-ingredient').value,
            pack_size: item.querySelector('.med-pack').value,
            price: item.querySelector('.med-price').value,
            application_rate: item.querySelector('.med-rate').value,
            frequency: item.querySelector('.med-frequency').value,
            priority: parseInt(item.querySelector('.med-priority').value) || 1,
            method: item.querySelector('.med-method').value,
            image_url: item.querySelector('.med-image').value,
            availability: item.querySelector('.med-availability').value,
            note: item.querySelector('.med-note').value
        };

        if (medicine.name.trim()) {
            medicines.push(medicine);
        }
    });

    return { diseaseKey, medicines };
}

// Initialize drag and drop functionality
function initializeDragAndDrop() {
    const container = document.getElementById('medicines-container');
    if (!container) return;

    let draggedElement = null;

    container.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('medicine-item')) {
            draggedElement = e.target;
            e.target.classList.add('dragging');
        }
    });

    container.addEventListener('dragend', (e) => {
        if (e.target.classList.contains('medicine-item')) {
            e.target.classList.remove('dragging');
            updateMedicineNumbers();
        }
    });

    container.addEventListener('dragover', (e) => {
        e.preventDefault();
        const afterElement = getDragAfterElement(container, e.clientY);
        if (afterElement == null) {
            container.appendChild(draggedElement);
        } else {
            container.insertBefore(draggedElement, afterElement);
        }
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.medicine-item:not(.dragging)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;

        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

// Override existing functions with enhanced versions
window.addMedicineItem = addMedicineItemEnhanced;
window.resetMedicinesContainer = resetMedicinesContainerEnhanced;
window.editMedicines = editMedicinesEnhanced;

// Update the medicines display when loading
const originalLoadMedicines = window.loadMedicines;
window.loadMedicines = async function () {
    try {
        const response = await fetch('/admin/api/disease-medicines', {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            displayMedicinesEnhanced(data);
        } else {
            console.error('Failed to load medicines');
        }
    } catch (error) {
        console.error('Error loading medicines:', error);
    }
};

// Enhanced form submission
document.addEventListener('DOMContentLoaded', () => {
    const medicinesForm = document.getElementById('medicinesForm');
    if (medicinesForm) {
        medicinesForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const { diseaseKey, medicines } = submitMedicinesFormEnhanced();

            try {
                const url = currentEditingDisease ?
                    `/admin/api/disease-medicines/${currentEditingDisease}` :
                    `/admin/api/disease-medicines/${diseaseKey}`;

                const response = await fetch(url, {
                    method: 'PUT',
                    headers: getAuthHeaders(),
                    body: JSON.stringify(medicines)
                });

                if (response.ok) {
                    hideForm('medicines');
                    loadMedicines();
                    if (isMobileDevice()) {
                        showMobileAlert('Medicines saved successfully!', 'success');
                    }
                } else {
                    if (isMobileDevice()) {
                        showMobileAlert('Failed to save medicines', 'error');
                    } else {
                        alert('Failed to save medicines');
                    }
                }
            } catch (error) {
                console.error('Error saving medicines:', error);
                if (isMobileDevice()) {
                    showMobileAlert('Error saving medicines', 'error');
                } else {
                    alert('Error saving medicines');
                }
            }
        });
    }
});