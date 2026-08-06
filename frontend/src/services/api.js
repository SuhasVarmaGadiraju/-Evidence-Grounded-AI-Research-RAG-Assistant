import axios from 'axios';

// Base API URL loaded from environment variable or fallback to deployed Render backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://evidence-ai-backend.onrender.com/api';

// Create standard Axios client configured with VITE_API_URL
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for unified backend error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorData = error.response?.data || {
      message: 'A network error occurred. Please try again.',
      success: false
    };
    
    // Log error to console in dev mode
    console.error('[API Error]:', errorData);
    
    return Promise.reject(errorData);
  }
);

export default api;
