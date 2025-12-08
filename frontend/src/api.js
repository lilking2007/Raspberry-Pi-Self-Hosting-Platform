import axios from 'axios';

// In dev, we can use localhost:8000 but cloudflared might route differently.
// For docker-composed frontend dev server, we should proxy /api to the admin container.
// Vite config needs proxy setup.
// If accessing from browser, we hit localhost:8000 (exposed port).

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;
