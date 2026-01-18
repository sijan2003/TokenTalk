const API_BASE_URL = 'http://127.0.0.1:8000/api';

/**
 * Centralized API Client
 * This class wraps the native 'fetch' API to handle repetitive tasks:
 * 1. Attaching JWT tokens to headers.
 * 2. Handling global errors (like 401 Unauthorized redirecting to login).
 * 3. Correctly managing Content-Type (especially for FormData/File uploads).
 */
class API {
    // Getter to retrieve the current user token from browser storage
    static get token() {
        return localStorage.getItem('token');
    }

    // Default headers for JSON requests
    static get headers() {
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }

    /**
     * The master request method.
     * @param {string} endpoint - The API path (e.g., '/auth/login')
     * @param {object} options - Fetch options (method, body, headers)
     */
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = options.headers || this.headers;

        // SPECIAL CASE: For file uploads (FormData), the browser MUST set the 
        // boundary header itself. If we manually set 'application/json', the upload fails.
        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);

            // GLOBAL ERROR HANDLER: If the token is expired or fake, the backend returns 401.
            // We immediately clear the local session and kick the user to the login page.
            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.href = 'index.html';
                return;
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'API request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // --- Authentication Endpoints ---
    static async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    static async register(email, password, fullName) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password, full_name: fullName })
        });
    }

    // --- Document Management (PDFs) ---
    static async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);
        return this.request('/documents/upload', {
            method: 'POST',
            body: formData
        });
    }

    static async getDocuments() {
        return this.request('/documents/');
    }

    static async deleteDocument(id) {
        return this.request(`/documents/${id}`, { method: 'DELETE' });
    }

    // --- YouTube Integration ---
    static async processYouTube(url) {
        return this.request('/youtube/process', {
            method: 'POST',
            body: JSON.stringify({ url, source_type: 'youtube' })
        });
    }

    static async getVideos() {
        return this.request('/youtube/');
    }

    // --- Webpage Integration ---
    static async processWebpage(url) {
        return this.request('/webpage/process', {
            method: 'POST',
            body: JSON.stringify({ url, source_type: 'webpage' })
        });
    }

    static async getWebpages() {
        return this.request('/webpage/');
    }

    // --- Chat Logic ---
    /**
     * Sends a chat question to the correct source endpoint.
     */
    static async chat(sourceId, sourceType, question) {
        let endpoint = '';
        // Route questions to different backend controllers based on the 'sourceType'
        if (sourceType === 'document' || sourceType === 'pdf') endpoint = `/documents/${sourceId}/chat`;
        else if (sourceType === 'youtube') endpoint = `/youtube/${sourceId}/chat`;
        else if (sourceType === 'webpage' || sourceType === 'web') endpoint = `/webpage/${sourceId}/chat`;

        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify({
                question,
                source_id: sourceId,
                source_type: sourceType
            })
        });
    }

    /**
     * Fetches previous Q&A for the specific source.
     */
    static async getHistory(sourceId, sourceType) {
        let endpoint = '';
        if (sourceType === 'document' || sourceType === 'pdf') endpoint = `/documents/${sourceId}/history`;
        else if (sourceType === 'youtube') endpoint = `/youtube/${sourceId}/history`;
        else if (sourceType === 'webpage' || sourceType === 'web') endpoint = `/webpage/${sourceId}/history`;

        return this.request(endpoint);
    }
}
