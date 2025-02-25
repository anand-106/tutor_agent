// Add base URL configuration
const API_BASE_URL = window.location.origin;

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const chatHistory = document.getElementById('chat-history');
    const queryInput = document.getElementById('query-input');
    const sendButton = document.getElementById('send-button');

    console.log("Page loaded. API Base URL:", API_BASE_URL);
    console.log("Current location:", window.location.href);
    
    // Test API endpoints
    fetch(`${API_BASE_URL}/api/ping`)
        .then(response => response.json())
        .then(data => console.log("Ping test:", data))
        .catch(error => console.error("Ping test failed:", error));

    async function handleResponse(response) {
        try {
            const contentType = response.headers.get("content-type");
            console.log("Response:", {
                url: response.url,
                status: response.status,
                contentType: contentType
            });
            
            if (contentType && contentType.includes("application/json")) {
                const result = await response.json();
                console.log("Response data:", result);
                return result;
            } else {
                const text = await response.text();
                console.error("Unexpected response:", {
                    url: response.url,
                    status: response.status,
                    contentType,
                    text: text.substring(0, 500) // First 500 chars
                });
                throw new Error(`Server error (${response.status}): ${text.substring(0, 100)}`);
            }
        } catch (error) {
            console.error("Response handling error:", error);
            throw error;
        }
    }

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const files = fileInput.files;
        if (files.length === 0) {
            uploadStatus.textContent = 'Please select files to upload';
            return;
        }

        uploadStatus.textContent = 'Uploading...';
        
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await handleResponse(response);
                
                if (!response.ok) {
                    throw new Error(result.detail || 'Upload failed');
                }
                
                uploadStatus.textContent = result.message || 'File uploaded successfully!';
                fileInput.value = '';
            } catch (error) {
                console.error("Upload error:", error);
                uploadStatus.textContent = `Error: ${error.message}`;
            }
        }
    });

    async function sendMessage() {
        const query = queryInput.value.trim();
        if (!query) return;

        // Add user message to chat
        addMessage(query, 'user');
        queryInput.value = '';

        try {
            const response = await fetch(`${API_BASE_URL}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: query })
            });

            const result = await handleResponse(response);
            
            if (!response.ok) {
                throw new Error(result.detail || 'Failed to get response');
            }

            addMessage(result.response, 'ai');
        } catch (error) {
            console.error("Chat error:", error);
            addMessage(`Error: ${error.message}`, 'ai');
        }
    }

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.textContent = text;
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    sendButton.addEventListener('click', sendMessage);
    queryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });
}); 