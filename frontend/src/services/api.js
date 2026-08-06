import axios from 'axios';

// Get base API URL from Vite environment variable with clean fallback
const getBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl && envUrl.trim() !== '') {
    const trimmed = envUrl.trim().replace(/\/+$/, '');
    return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
  }
  // Fallback to relative /api (works with Vercel rewrites or local proxy)
  return '/api';
};

const API_BASE_URL = getBaseUrl();

// Create standard Axios client with extended timeout for long PDF ingestion tasks
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minute timeout for PDF text extraction & embedding generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to automatically attach Firebase Auth Bearer token
api.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem('rag_auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (e) {
      // Ignore localStorage access errors
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for unified backend error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorData = error.response?.data || {
      message: error.message || 'A network error occurred. Please verify your internet connection.',
      success: false
    };

    console.error('[API Network Error]:', errorData);
    return Promise.reject(errorData);
  }
);

export default api;
