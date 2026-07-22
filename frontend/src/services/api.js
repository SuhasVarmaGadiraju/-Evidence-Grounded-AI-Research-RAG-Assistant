import axios from 'axios';

// Create standard Axios client configured for proxy prefix
const api = axios.create({
  baseURL: '/api',
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
