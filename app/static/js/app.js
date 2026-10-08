document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const chooseBtn = document.getElementById('chooseFileBtn');
    const dropzone = document.getElementById('dropzone');
    const statusBox = document.getElementById('statusBox');

    chooseBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files.length) {
            statusBox.textContent = 'Selected: ' + fileInput.files[0].name;
        }
    });

    dropzone.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropzone.style.borderColor = '#7fd8ff';
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.style.borderColor = 'rgba(130, 196, 255, 0.8)';
    });

    dropzone.addEventListener('drop', (event) => {
        event.preventDefault();
        const file = event.dataTransfer.files[0];
        if (file) {
            fileInput.files = event.dataTransfer.files;
            statusBox.textContent = 'Selected: ' + file.name;
        }
    });

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        const file = fileInput.files[0];
        if (!file) {
            statusBox.textContent = 'Please select a file first.';
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        statusBox.textContent = 'Uploading and analyzing...';
        try {
            const response = await fetch('/api/files/upload', {
                method: 'POST',
                body: formData,
            });
            const result = await response.json();
            if (!result.success) {
                statusBox.textContent = result.message || 'Upload failed.';
                return;
            }
            statusBox.textContent = 'Detected: ' + (result.analysis.detected_format || 'UNKNOWN');
            if (result.analysis.status === 'password_required') {
                const credential = prompt('Enter the password or key for this file:');
                if (!credential) {
                    statusBox.textContent = 'A valid password or key is required.';
                    return;
                }
                const unlockResponse = await fetch('/api/files/unlock', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ job_id: result.job_id, credential })
                });
                const unlockResult = await unlockResponse.json();
                if (!unlockResult.success) {
                    statusBox.textContent = unlockResult.message || 'Unlock failed.';
                    return;
                }
                statusBox.textContent = 'Unlock successful. Output ready.';
            }
        } catch (error) {
            statusBox.textContent = 'An unexpected error occurred.';
        }
    });
});
