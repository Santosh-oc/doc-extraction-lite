const API_BASE_URL = 'http://10.42.1.250:8000/api';

let currentDocumentId = null;
let currentExtractionId = null;

// --- DOM Elements ---
const pdfUploadInput = document.getElementById('pdf-upload');
const uploadButton = document.getElementById('upload-button');
const uploadStatus = document.getElementById('upload-status');
const uploadedDocInfo = document.getElementById('uploaded-doc-info');
const docFilenameSpan = document.getElementById('doc-filename');
const docPageCountSpan = document.getElementById('doc-page-count');
const selectAnotherPdfButton = document.getElementById('select-another-pdf');

const extractionSection = document.getElementById('extraction-section');
const fieldDefinitionsDiv = document.getElementById('field-definitions');
const addFieldButton = document.getElementById('add-field-button');
const extractionInstructionsTextarea = document.getElementById('extraction-instructions');
const runExtractionButton = document.getElementById('run-extraction-button');
const extractionStatus = document.getElementById('extraction-status');

const resultsSection = document.getElementById('results-section');
const resultsTableBody = document.getElementById('results-table-body');
const downloadJsonButton = document.getElementById('download-json');
const downloadCsvButton = document.getElementById('download-csv');
const newExtractionButton = document.getElementById('new-extraction-button');

// --- Event Listeners ---
uploadButton.addEventListener('click', uploadPdf);
selectAnotherPdfButton.addEventListener('click', resetUploadSection);
addFieldButton.addEventListener('click', addFieldRow);
runExtractionButton.addEventListener('click', runExtraction);
downloadJsonButton.addEventListener('click', downloadJson);
downloadCsvButton.addEventListener('click', downloadCsv);
newExtractionButton.addEventListener('click', resetApp);

// --- Functions ---
async function uploadPdf() {
    const file = pdfUploadInput.files[0];
    if (!file) {
        uploadStatus.textContent = 'Please select a PDF file.';
        uploadStatus.style.color = 'red';
        return;
    }

    uploadStatus.textContent = 'Uploading...';
    uploadStatus.style.color = 'black';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/documents/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Upload failed');
        }

        const data = await response.json();
        currentDocumentId = data.id;
        docFilenameSpan.textContent = data.filename;
        docPageCountSpan.textContent = data.page_count;

        uploadStatus.textContent = 'Upload successful!';
        uploadStatus.style.color = 'green';
        uploadButton.style.display = 'none';
        pdfUploadInput.style.display = 'none';
        uploadedDocInfo.style.display = 'block';
        extractionSection.style.display = 'block';

        // Add a default field
        if (document.querySelectorAll('.field-row').length <= 1) { // Only header exists
            addFieldRow();
        }

    } catch (error) {
        uploadStatus.textContent = `Error: ${error.message}`;
        uploadStatus.style.color = 'red';
    }
}

function resetUploadSection() {
    currentDocumentId = null;
    pdfUploadInput.value = '';
    uploadStatus.textContent = '';
    uploadButton.style.display = 'inline-block';
    pdfUploadInput.style.display = 'inline-block';
    uploadedDocInfo.style.display = 'none';
    extractionSection.style.display = 'none';
    resultsSection.style.display = 'none';
    resetFieldDefinitions();
    extractionInstructionsTextarea.value = '';
    extractionStatus.textContent = '';
}

function addFieldRow(name = '', description = '', type = 'string', required = true) {
    const fieldRow = document.createElement('div');
    fieldRow.classList.add('field-row');
    fieldRow.innerHTML = `
        <input type="text" class="field-name" placeholder="Name" value="${name}">
        <input type="text" class="field-description" placeholder="Description" value="${description}">
        <select class="field-type">
            <option value="string" ${type === 'string' ? 'selected' : ''}>String</option>
            <option value="number" ${type === 'number' ? 'selected' : ''}>Number</option>
            <option value="boolean" ${type === 'boolean' ? 'selected' : ''}>Boolean</option>
            <option value="date" ${type === 'date' ? 'selected' : ''}>Date</option>
        </select>
        <input type="checkbox" class="field-required" ${required ? 'checked' : ''}>
        <button class="remove-field-button">Remove</button>
    `;
    fieldDefinitionsDiv.appendChild(fieldRow);

    fieldRow.querySelector('.remove-field-button').addEventListener('click', () => {
        fieldRow.remove();
    });
}

function resetFieldDefinitions() {
    const fieldRows = fieldDefinitionsDiv.querySelectorAll('.field-row:not(.header)');
    fieldRows.forEach(row => row.remove());
}

async function runExtraction() {
    if (!currentDocumentId) {
        extractionStatus.textContent = 'Please upload a document first.';
        extractionStatus.style.color = 'red';
        return;
    }

    const fieldRows = fieldDefinitionsDiv.querySelectorAll('.field-row:not(.header)');
    const field_defs = [];
    let hasError = false;

    fieldRows.forEach(row => {
        const name = row.querySelector('.field-name').value.trim();
        const description = row.querySelector('.field-description').value.trim();
        const type = row.querySelector('.field-type').value;
        const required = row.querySelector('.field-required').checked;

        if (!name || !description) {
            hasError = true;
        }
        field_defs.push({ name, description, type, required });
    });

    if (hasError) {
        extractionStatus.textContent = 'All field name and description must be filled.';
        extractionStatus.style.color = 'red';
        return;
    }
    if (field_defs.length === 0) {
        extractionStatus.textContent = 'Please define at least one field.';
        extractionStatus.style.color = 'red';
        return;
    }

    extractionStatus.textContent = 'Running extraction... This may take a moment.';
    extractionStatus.style.color = 'black';

    const instructions = extractionInstructionsTextarea.value.trim();

    try {
        const response = await fetch(`${API_BASE_URL}/extractions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                document_id: currentDocumentId,
                field_defs: field_defs,
                instructions: instructions || null,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Extraction failed');
        }

        const data = await response.json();
        currentExtractionId = data.id;

        if (data.status === 'done') {
            extractionStatus.textContent = 'Extraction successful!';
            extractionStatus.style.color = 'green';
            displayResults(data.results);
            resultsSection.style.display = 'block';
        } else if (data.status === 'failed') {
            extractionStatus.textContent = `Extraction failed: ${data.error || 'Unknown error'}`;
            extractionStatus.style.color = 'red';
        } else {
            extractionStatus.textContent = `Extraction status: ${data.status}`;
            extractionStatus.style.color = 'orange';
        }

    } catch (error) {
        extractionStatus.textContent = `Error: ${error.message}`;
        extractionStatus.style.color = 'red';
    }
}

function displayResults(results) {
    resultsTableBody.innerHTML = '';
    if (!results || results.length === 0) {
        resultsTableBody.innerHTML = '<tr><td colspan="5">No results found.</td></tr>';
        return;
    }

    results.forEach(result => {
        const row = resultsTableBody.insertRow();
        row.insertCell().textContent = result.field_name;
        row.insertCell().textContent = result.value !== null ? result.value : 'N/A';
        row.insertCell().textContent = result.confidence !== null ? result.confidence.toFixed(2) : 'N/A';
        row.insertCell().textContent = result.page !== null ? result.page : 'N/A';
        row.insertCell().textContent = result.evidence !== null ? result.evidence : 'N/A';
    });
}

async function downloadJson() {
    if (!currentExtractionId) return;
    window.open(`${API_BASE_URL}/extractions/${currentExtractionId}/download/json`, '_blank');
}

async function downloadCsv() {
    if (!currentExtractionId) return;
    window.open(`${API_BASE_URL}/extractions/${currentExtractionId}/download/csv`, '_blank');
}

function resetApp() {
    currentDocumentId = null;
    currentExtractionId = null;
    pdfUploadInput.value = '';
    uploadStatus.textContent = '';
    uploadButton.style.display = 'inline-block';
    pdfUploadInput.style.display = 'inline-block';
    uploadedDocInfo.style.display = 'none';

    extractionSection.style.display = 'none';
    resetFieldDefinitions();
    extractionInstructionsTextarea.value = '';
    extractionStatus.textContent = '';

    resultsSection.style.display = 'none';
    resultsTableBody.innerHTML = '';
}

// Initial setup
resetApp();
