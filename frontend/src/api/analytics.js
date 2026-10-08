import apiClient from './axios';

export const analyticsApi = {
  getMyAnalytics: async () => {
    const response = await apiClient.get('/analytics/student/me');
    return response.data;
  },

  getStudentAnalytics: async (studentId) => {
    const response = await apiClient.get(`/analytics/student/${studentId}`);
    return response.data;
  },

  getClassroomAnalytics: async (classroomId) => {
    const response = await apiClient.get(`/analytics/classroom/${classroomId}`);
    return response.data;
  },

  getClassroomLeaderboard: async (classroomId) => {
    const response = await apiClient.get(`/analytics/classroom/${classroomId}/leaderboard`);
    return response.data;
  },
};
