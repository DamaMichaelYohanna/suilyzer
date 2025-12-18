/**
 * Suilyzer Frontend - Main JavaScript
 */

// Configuration
// Use relative URL for API when served from backend, or localhost for development
const API_BASE_URL = window.location.hostname === 'localhost' && window.location.port === ''
    ? 'http://localhost:8001'
    : window.location.origin;

// DOM Elements
let analyzeForm;
let digestInput;
let analyzeBtn;
let loadingState;
let errorState;
let errorMessage;
let resultsSection;
let summaryContent;
let gasUsed;
let createdObjects;
let mutatedObjects;
let deletedObjects;
let packagesContainer;
let rawDataContainer;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    attachEventListeners();
});

/**
 * Initialize DOM element references
 */
function initializeElements() {
    analyzeForm = document.getElementById('analyzeForm');
    digestInput = document.getElementById('digestInput');
    analyzeBtn = document.getElementById('analyzeBtn');
    loadingState = document.getElementById('loadingState');
    errorState = document.getElementById('errorState');
    errorMessage = document.getElementById('errorMessage');
    resultsSection = document.getElementById('resultsSection');
    summaryContent = document.getElementById('summaryContent');
    gasUsed = document.getElementById('gasUsed');
    createdObjects = document.getElementById('createdObjects');
    mutatedObjects = document.getElementById('mutatedObjects');
    deletedObjects = document.getElementById('deletedObjects');
    packagesContainer = document.getElementById('packagesContainer');
    rawDataContainer = document.getElementById('rawDataContainer');
}

/**
 * Attach event listeners
 */
function attachEventListeners() {
    analyzeForm.addEventListener('submit', handleAnalyze);
}

/**
 * Handle form submission
 */
async function handleAnalyze(event) {
    event.preventDefault();

    const digest = digestInput.value.trim();

    if (!digest) {
        showError('Please enter a transaction digest');
        return;
    }

    // Show loading state
    showLoading();

    try {
        // Call backend API
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ digest })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || errorData.error || 'Failed to analyze transaction');
        }

        const data = await response.json();

        // Display results
        displayResults(data);

    } catch (error) {
        console.error('Error analyzing transaction:', error);
        showError(error.message || 'Failed to analyze transaction. Please try again.');
    }
}

/**
 * Display analysis results
 */
function displayResults(data) {
    // Hide loading and error states
    loadingState.classList.add('hidden');
    errorState.classList.add('hidden');

    // Re-enable analyze button
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = 'Analyze Transaction';

    // Show results section
    resultsSection.classList.remove('hidden');

    // Display summary
    summaryContent.innerHTML = formatSummary(data.summary);

    // Display gas used
    gasUsed.textContent = data.gas_used;

    // Display diagram
    if (data.diagram && data.diagram.nodes.length > 0) {
        renderDiagram(data.diagram);
    }

    // Display objects
    displayObjects(data.objects);

    // Display packages
    displayPackages(data.packages);

    // Display raw data
    if (data.raw_data) {
        rawDataContainer.textContent = JSON.stringify(data.raw_data, null, 2);
    }

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Format summary text with paragraphs
 */
function formatSummary(summary) {
    // Split by double newlines or periods followed by space and capital letter
    const paragraphs = summary.split(/\n\n|\.\s+(?=[A-Z])/).filter(p => p.trim());

    return paragraphs.map(p => {
        const text = p.trim();
        // Add period if missing
        const formatted = text.endsWith('.') ? text : text + '.';
        return `<p>${formatted}</p>`;
    }).join('');
}

/**
 * Display objects (created, mutated, deleted)
 */
function displayObjects(objects) {
    createdObjects.innerHTML = renderObjectList(objects.created, 'No objects created');
    mutatedObjects.innerHTML = renderObjectList(objects.mutated, 'No objects mutated');
    deletedObjects.innerHTML = renderObjectList(objects.deleted, 'No objects deleted');
}

/**
 * Render list of objects
 */
function renderObjectList(objectList, emptyMessage) {
    if (!objectList || objectList.length === 0) {
        return `<p class="empty-message">${emptyMessage}</p>`;
    }

    return objectList.map(obj => {
        const typeInfo = parseObjectType(obj.object_type);
        return `
            <div class="object-item">
                <div class="object-id">
                    <strong>ID:</strong> 
                    <code>${truncateAddress(obj.object_id)}</code>
                </div>
                <div class="object-type-display">
                    <strong>Type:</strong> 
                    <span class="type-struct">${typeInfo.struct || 'Unknown'}</span>
                    ${typeInfo.type_args ? `<span class="type-args">&lt;${typeInfo.type_args}&gt;</span>` : ''}
                </div>
                ${obj.owner ? `
                    <div class="object-owner">
                        <strong>Owner:</strong> 
                        <code>${truncateAddress(obj.owner)}</code>
                    </div>
                ` : ''}
                ${obj.version ? `
                    <div class="object-version">
                        <strong>Version:</strong> ${obj.version}
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

/**
 * Display packages
 */
function displayPackages(packages) {
    if (!packages || packages.length === 0) {
        packagesContainer.innerHTML = '<p class="empty-message">No packages involved</p>';
        return;
    }

    packagesContainer.innerHTML = packages.map(pkg => `
        <div class="package-item">
            <div class="package-id">
                <strong>Package:</strong> 
                <code>${truncateAddress(pkg.package_id)}</code>
            </div>
            ${pkg.module ? `
                <div class="package-module">
                    <strong>Module:</strong> 
                    <span class="module-name">${pkg.module}</span>
                </div>
            ` : ''}
            ${pkg.function ? `
                <div class="package-function">
                    <strong>Function:</strong> 
                    <span class="function-name">${pkg.function}</span>
                </div>
            ` : ''}
        </div>
    `).join('');
}

/**
 * Parse object type string
 */
function parseObjectType(objectType) {
    const result = {
        package: null,
        module: null,
        struct: null,
        type_args: null
    };

    try {
        // Split on < to separate base type from type arguments
        let baseType = objectType;
        if (objectType.includes('<')) {
            const parts = objectType.split('<');
            baseType = parts[0];
            result.type_args = parts[1].replace('>', '');
        }

        // Split base type into package::module::struct
        const typeParts = baseType.split('::');
        if (typeParts.length >= 3) {
            result.package = typeParts[0];
            result.module = typeParts[1];
            result.struct = typeParts.slice(2).join('::');
        } else if (typeParts.length === 2) {
            result.module = typeParts[0];
            result.struct = typeParts[1];
        } else {
            result.struct = baseType;
        }
    } catch (e) {
        result.struct = objectType;
    }

    return result;
}

/**
 * Truncate address for display
 */
function truncateAddress(address) {
    if (!address || address.length <= 12) {
        return address;
    }
    return `${address.substring(0, 8)}...${address.substring(address.length - 4)}`;
}

/**
 * Show loading state
 */
function showLoading() {
    loadingState.classList.remove('hidden');
    errorState.classList.add('hidden');
    resultsSection.classList.add('hidden');
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';
}

/**
 * Show error state
 */
function showError(message) {
    errorMessage.textContent = message;
    errorState.classList.remove('hidden');
    loadingState.classList.add('hidden');
    resultsSection.classList.add('hidden');
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = 'Analyze Transaction';
}

/**
 * Clear error state
 */
function clearError() {
    errorState.classList.add('hidden');
    digestInput.focus();
}

/**
 * Show about dialog
 */
function showAbout() {
    alert(
        'Suilyzer - Sui Transaction Analyzer\\n\\n' +
        'Version 1.0.0\\n\\n' +
        'Analyzes Sui blockchain transactions and explains them in plain English using Google Gemini AI.\\n\\n' +
        'Features:\\n' +
        '- Human-readable transaction summaries\\n' +
        '- Visual transaction flow diagrams\\n' +
        '- Object change tracking\\n' +
        '- Package and module information\\n' +
        '- Gas usage display'
    );
}

/**
 * Toggle raw data visibility
 */
function toggleRawData() {
    rawDataContainer.classList.toggle('hidden');
}

/**
 * Reset form after successful analysis
 */
function resetForm() {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = 'Analyze Transaction';
}

// Ensure reset on results display
window.addEventListener('load', () => {
    resetForm();
});
