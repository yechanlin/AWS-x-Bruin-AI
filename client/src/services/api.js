// Thin fetch wrapper (ApiService) used by App.js to call the FastAPI backend at REACT_APP_API_URL.
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const isUpload = options.body instanceof FormData;
    const config = {
      ...options,
      headers: {
        ...(isUpload ? {} : { 'Content-Type': 'application/json' }),
        ...options.headers,
      },
    };
    let response;
    try {
      response = await fetch(url, config);
    } catch {
      throw new Error('Cannot reach the backend. Check that the API is running on port 8000.');
    }
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const detail = Array.isArray(body.detail)
        ? body.detail.map(item => item.msg).join('; ')
        : body.detail;
      throw new Error(detail || `Request failed (${response.status}). Please try again.`);
    }
    return response.json();
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async uploadFile(endpoint, file) {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.request(endpoint, {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  }
}

const apiService = new ApiService();
export default apiService;