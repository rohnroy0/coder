import apiClient from './axios';

export const learningApi = {
  getPath: async (language) => {
    const response = await apiClient.get(`/learning/path/${language}`);
    return response.data;
  },

  getChapterDetail: async (chapterId) => {
    const response = await apiClient.get(`/learning/chapters/${chapterId}/detail`);
    return response.data;
  },
};
