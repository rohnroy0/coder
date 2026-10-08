import apiClient from './axios';

export const badgesApi = {
  getCatalog: async () => {
    const response = await apiClient.get('/badges');
    return response.data;
  },

  getMyBadges: async () => {
    const response = await apiClient.get('/badges/me');
    return response.data;
  },
};
