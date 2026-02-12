// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const fileLabel = document.querySelector('.file-upload-label');
const fileName = document.getElementById('fileName');
const submitBtn = document.getElementById('submitBtn');
const uploadSection = document.getElementById('uploadSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const newUploadBtn = document.getElementById('newUploadBtn');
const retryBtn = document.getElementById('retryBtn');

let currentFiles = null;

// File input handling
fileInput.addEventListener('change', (e) => {
    handleFileSelect(e.target.files);
});

// Drag and drop
fileLabel.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileLabel.classList.add('drag-over');
});

fileLabel.addEventListener('dragleave', () => {
    fileLabel.classList.remove('drag-over');
});

fileLabel.addEventListener('drop', (e) => {
    e.preventDefault();
    fileLabel.classList.remove('drag-over');
    handleFileSelect(e.dataTransfer.files);
});

function handleFileSelect(files) {
    if (files.length > 0) {
        const file = files[0];
        if (file.type === 'application/pdf') {
            currentFiles = files;
            fileName.textContent = file.name;
            fileLabel.classList.add('has-file');
        } else {
            showError('Please select a PDF file');
        }
    }
}

// Form submission
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!currentFiles || currentFiles.length === 0) {
        showError('Please select a file');
        return;
    }

    const formData = new FormData();
    formData.append('file', currentFiles[0]);
    formData.append('bom_type', document.getElementById('bomType').value);

    // Show loading state
    setLoading(true);
    hideError();

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
            displayResults(result);
        } else {
            showError(result.error || 'An error occurred during extraction');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        setLoading(false);
    }
});

function setLoading(loading) {
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    
    if (loading) {
        btnText.style.display = 'none';
        btnLoader.style.display = 'flex';
        submitBtn.disabled = true;
    } else {
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
        submitBtn.disabled = false;
    }
}

function displayResults(result) {
    const { data, files } = result;

    // Hide upload section, show results
    uploadSection.style.display = 'none';
    resultsSection.style.display = 'block';

    // Update summary stats
    document.getElementById('totalItems').textContent = data.total_items || data.items.length;
    document.getElementById('bomTypeDisplay').textContent = data.bom_type.toUpperCase();
    document.getElementById('documentTitle').textContent = data.document_title || 'BOM Document';

    // Create table
    createTable(data.items);

    // Setup download buttons
    document.getElementById('downloadJson').onclick = () => {
        window.location.href = `/download/json/${files.json}`;
    };
    document.getElementById('downloadCsv').onclick = () => {
        window.location.href = `/download/csv/${files.csv}`;
    };
}

function createTable(items) {
    if (items.length === 0) {
        document.getElementById('dataTable').innerHTML = '<p>No items found</p>';
        return;
    }

    // Get all unique keys from items
    const keys = Object.keys(items[0]);

    let html = '<table><thead><tr>';
    keys.forEach(key => {
        html += `<th>${formatHeader(key)}</th>`;
    });
    html += '</tr></thead><tbody>';

    items.forEach(item => {
        html += '<tr>';
        keys.forEach(key => {
            const value = item[key] !== null && item[key] !== undefined ? item[key] : '-';
            html += `<td>${escapeHtml(String(value))}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    document.getElementById('dataTable').innerHTML = html;
}

function formatHeader(key) {
    return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    errorSection.style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
    uploadSection.style.display = 'none';
    resultsSection.style.display = 'none';
}

function hideError() {
    errorSection.style.display = 'none';
}

function resetForm() {
    uploadSection.style.display = 'block';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    uploadForm.reset();
    fileName.textContent = 'Choose PDF file or drag & drop';
    fileLabel.classList.remove('has-file');
    currentFiles = null;
}

// New upload button
newUploadBtn.addEventListener('click', resetForm);
retryBtn.addEventListener('click', resetForm);