import { io } from 'socket.io-client';

// In production, use current origin without explicit URL
const getSocketUrl = () => {
  // Check if VITE_API_URL is set and not empty
  if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.trim() !== '') {
    return import.meta.env.VITE_API_URL;
  }

  // In production (when VITE_ENVIRONMENT is set to 'production' or VITE_API_URL is empty)
  if (import.meta.env.VITE_ENVIRONMENT === 'production' || import.meta.env.VITE_API_URL === '') {
    // Don't pass any URL - Socket.IO will use current page origin
    console.log('Using current origin for Socket.IO connection');
    return undefined;
  }

  // In development, use localhost
  return 'http://localhost:5001';
};

const socketUrl = getSocketUrl();
console.log('Socket.IO URL:', socketUrl || 'current origin');

const socket = io(socketUrl, {
  path: '/socket.io/',
  transports: ['polling', 'websocket'], // Try polling first, then websocket
  withCredentials: true,
});

socket.on('connect', () => console.log('Connected to Socket.io Server'));
socket.on('response', (data) => console.log('Received:', data));
socket.on('connect_error', (error) =>
  console.error('Connection Error:', error)
);

export default socket;
