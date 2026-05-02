/* AI Exam Corrector - Main JavaScript */

// File upload handling
document.getElementById('fileInput').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        uploadFile(file);
    }
});

// Drag and drop
const imagePreview = document.getElementById('imagePreview');

imagePreview.addEventListener('dragover', (e) => {
    e.preventDefault();
    imagePreview.style.borderColor = '#3498db';
    imagePreview.style.background = '#ecf0f1';
});

imagePreview.addEventListener('dragleave', () => {
    imagePreview.style.borderColor = '#bdc3c7';
    imagePreview.style.background = '#f8f9fa';
});

imagePreview.addEventListener('drop', (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        uploadFile(file);
    }
});

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    showSpinner();
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        if (data.success) {
            displayImage(file);
            updateStatus(`Loaded: ${file.name}`);
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        hideSpinner();
        console.error('Error:', error);
        alert('Upload failed: ' + error);
    });
}

function displayImage(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = document.getElementById('imagePreview');
        preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
    };
    reader.readAsDataURL(file);
}

function useSample() {
    showSpinner();
    
    fetch('/use-sample', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        if (data.success) {
            const preview = document.getElementById('imagePreview');
            preview.innerHTML = `
                <div style="text-align: center; color: #666;">
                    <p style="font-size: 48px; margin-bottom: 10px;">📋</p>
                    <p>Using Sample Data</p>
                    <p style="font-size: 12px; margin-top: 10px;">Q1: What is AI?<br>Q2: 2+2=?<br>Q3: Capital of India?</p>
                </div>
            `;
            updateStatus('Sample data loaded');
        }
    });
}

function gradePaper() {
    const algorithm = document.querySelector('input[name="algorithm"]:checked').value;
    const subject = document.getElementById('subjectSelect').value;
    
    showSpinner();
    updateStatus('Processing...');
    
    fetch('/grade', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            algorithm: algorithm,
            subject: subject
        })
    })
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        if (data.success) {
            window.location.href = '/results';
        } else {
            alert('Error: ' + data.error);
            updateStatus('Error occurred');
        }
    })
    .catch(error => {
        hideSpinner();
        console.error('Error:', error);
        alert('Grading failed: ' + error);
        updateStatus('Error occurred');
    });
}

function runDemo() {
    useSample();
    setTimeout(() => {
        gradePaper();
    }, 500);
}

function updateStatus(message) {
    document.getElementById('statusText').textContent = message;
}

function showSpinner() {
    document.getElementById('loadingSpinner').classList.remove('hidden');
}

function hideSpinner() {
    document.getElementById('loadingSpinner').classList.add('hidden');
}
