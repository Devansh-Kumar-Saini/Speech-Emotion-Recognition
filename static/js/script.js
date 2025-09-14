// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const audioFileInput = document.getElementById('audioFile');
    const uploadStatus = document.getElementById('uploadStatus');
    const resultSection = document.querySelector('.result-section');
    const emotionText = document.getElementById('emotionText');
    const confidenceBar = document.getElementById('confidenceFill');
    const confidenceText = document.getElementById('confidenceText');

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const file = audioFileInput.files[0];
        if (!file) {
            updateStatus('Please select an audio file first.', 'error');
            return;
        }

        // Show loading state
        updateStatus('Analyzing audio...', 'processing');
        resultSection.style.display = 'none';

        const formData = new FormData();
        formData.append('audio', file);

        // Use relative URL for production
        fetch('/predict', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update UI with results
            const confidence = (data.confidence * 100).toFixed(2);
            emotionText.textContent = data.emotion.charAt(0).toUpperCase() + data.emotion.slice(1);
            confidenceBar.style.width = `${confidence}%`;
            confidenceText.textContent = `${confidence}%`;
            
            // Show result section
            resultSection.style.display = 'block';
            updateStatus('Analysis complete!', 'success');
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus(`Error: ${error.message}`, 'error');
        });
    });

    // Update status message
    function updateStatus(message, type = 'info') {
        uploadStatus.textContent = message;
        uploadStatus.className = 'recording-status';
        uploadStatus.classList.add(type);
    }
});