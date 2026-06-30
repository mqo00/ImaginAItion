// API Configuration for different environments

const getApiBaseUrl = () => {
  // Check if VITE_API_URL is set and not empty
  if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.trim() !== '') {
    return import.meta.env.VITE_API_URL;
  }

  // In production (when VITE_ENVIRONMENT is set to 'production' or VITE_API_URL is empty)
  if (import.meta.env.VITE_ENVIRONMENT === 'production' || import.meta.env.VITE_API_URL === '') {
    return ''; // Use relative paths
  }

  // Development mode - use localhost
  if (import.meta.env.DEV) {
    return 'http://localhost:5001';
  }

  // Fallback to empty string for relative paths
  return '';
};

export const API_BASE_URL = getApiBaseUrl();
export const API_ENDPOINTS = {
  // Admin endpoints
  ADMIN_LOGIN: `${API_BASE_URL}/api/admin/login`,
  ADMIN_LOGOUT: `${API_BASE_URL}/api/admin/logout`,
  ADMIN_VERIFY: `${API_BASE_URL}/api/admin/verify`,
  ADMIN_LIST_LOGS: `${API_BASE_URL}/api/admin/list-game-logs-detailed`,
  ADMIN_GET_LOG: (gameId) => `${API_BASE_URL}/api/admin/game-log/${gameId}`,
  ADMIN_EXPORT_LOGS: `${API_BASE_URL}/api/admin/export-logs`,
};

// Utility function for image URLs
export const getImageUrl = (imagePath) => {
  if (!imagePath) return '';

  // If it's already a full URL, return as is
  if (imagePath.startsWith('http')) return imagePath;

  // Use API_BASE_URL for image paths
  const baseUrl = import.meta.env.VITE_ENVIRONMENT === 'production'
    ? '' // Use relative paths in production
    : 'http://localhost:5001'; // Use localhost in development

  return `${baseUrl}${imagePath}`;
};

console.log('API Base URL:', API_BASE_URL);