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

        console.log('Sending request to /predict endpoint...');
        
        // Use the correct endpoint for prediction
        fetch('/predict', {
            method: 'POST',
            body: formData,
            // No need for Content-Type header when using FormData
            // The browser will set it automatically with the correct boundary
            credentials: 'same-origin',  // Include cookies if needed
            // Add a timeout to handle unresponsive servers
            signal: AbortSignal.timeout(30000)  // 30 seconds timeout
        })
        .then(async response => {
            console.log('Response status:', response.status);
            const responseText = await response.text();
            console.log('Raw response:', responseText);
            
            if (!response.ok) {
                // Try to parse the error response as JSON, fallback to text
                let errorData;
                try {
                    errorData = JSON.parse(responseText);
                } catch (e) {
                    throw new Error(`Server error: ${response.status} - ${response.statusText}`);
                }
                throw new Error(errorData.error || errorData.message || 'Unknown server error');
            }
            
            // If we got here, the response is ok, parse as JSON
            return JSON.parse(responseText);
        })
        .then(data => {
            if (data && data.error) {
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
            console.error('Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            
            let errorMessage = 'Error processing your request';
            
            if (error.name === 'AbortError') {
                errorMessage = 'Request timed out. The server is taking too long to respond.';
            } else if (error.message.includes('NetworkError')) {
                errorMessage = 'Network error. Please check your internet connection.';
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            updateStatus(errorMessage, 'error');
            
            // Show result section with error state
            resultSection.style.display = 'block';
            emotionText.textContent = 'Error';
            confidenceBar.style.width = '0%';
            confidenceText.textContent = '0%';
        });
    });

    // Update status message
    function updateStatus(message, type = 'info') {
        uploadStatus.textContent = message;
        uploadStatus.className = 'recording-status';
        uploadStatus.classList.add(type);
    }
});