// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const audioFileInput = document.getElementById('audioFile');
    const uploadStatus = document.getElementById('uploadStatus');
    const resultSection = document.querySelector('.result-section');
    const emotionText = document.getElementById('emotionText');
    const confidenceBar = document.getElementById('confidenceFill');
    const confidenceText = document.getElementById('confidenceText');

    // Make sure all required elements exist
    if (!uploadForm || !audioFileInput || !uploadStatus || !resultSection || 
        !emotionText || !confidenceBar || !confidenceText) {
        console.error('Required elements not found in the DOM');
        return;
    }

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
        
        // Create a new AbortController for the fetch request
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        // Get the current hostname and protocol
        const baseUrl = window.location.origin;
        const predictUrl = `${baseUrl}/predict`;
        
        console.log('Sending request to:', predictUrl);
        
        // Update UI to show processing
        const uploadStatus = document.getElementById('uploadStatus');
        uploadStatus.textContent = 'Processing your audio...';
        uploadStatus.style.color = '#4a90e2';
        
        // Show loading animation
        document.querySelector('.audio-visualizer').style.display = 'flex';
        
        // Set a timeout for the fetch request
        const TIMEOUT_DURATION = 60000; // 60 seconds
        
        // Create a promise that rejects after timeout
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => {
                reject(new Error('Request timed out. The server is taking too long to respond.'));
            }, TIMEOUT_DURATION);
        });
        
        // Make the fetch request
        const fetchPromise = fetch(predictUrl, {
            method: 'POST',
            body: formData,
            signal: controller.signal,
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        // Race between fetch and timeout
        return Promise.race([fetchPromise, timeoutPromise.then(() => { throw new Error('timeout'); })])
        .then(async response => {
            clearTimeout(timeoutId);
            const responseText = await response.text();
            console.log('Response status:', response.status);
            console.log('Response text:', responseText);
            
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
            try {
                return JSON.parse(responseText);
            } catch (e) {
                throw new Error('Invalid JSON response from server');
            }
        })
        .then(data => {
            if (!data) {
                throw new Error('No data received from server');
            }
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (!data.emotion || data.confidence === undefined) {
                throw new Error('Invalid response format from server');
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
            clearTimeout(timeoutId);
            
            console.error('Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            
            let errorMessage = 'Error processing your request';
            
            if (error.name === 'AbortError') {
                errorMessage = 'Request timed out. The server is taking too long to respond.';
            } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                errorMessage = 'Cannot connect to the server. Please check your internet connection and try again.';
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
        if (!uploadStatus) return;
        
        uploadStatus.textContent = message;
        uploadStatus.className = 'recording-status';
        
        // Remove any existing status classes
        uploadStatus.classList.remove('error', 'success', 'processing');
        
        // Add the new status class if provided
        if (type) {
            uploadStatus.classList.add(type);
        }
    }
});