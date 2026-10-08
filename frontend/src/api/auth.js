import apiClient from './axios';

export const authApi = {
  register: async (userData) => {
    // userData: { name, email, password, role }
    const response = await apiClient.post('/auth/register', userData);
    return response.data;
  },

  login: async (credentials) => {
    // credentials: { email, password }
    const response = await apiClient.post('/auth/login', credentials);
    return response.data; // { access_token, token_type }
  },

  getMe: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data; // UserResponse
  },
};
