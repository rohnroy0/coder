import apiClient from './axios';

export const assignmentsApi = {
  createAssignment: async (data) => {
    const response = await apiClient.post('/assignments', data);
    return response.data;
  },

  getClassroomAssignments: async (classroomId) => {
    const response = await apiClient.get(`/assignments/classroom/${classroomId}`);
    return response.data;
  },

  getAssignmentDetail: async (id) => {
    const response = await apiClient.get(`/assignments/${id}`);
    return response.data;
  },

  updateAssignment: async (id, data) => {
    const response = await apiClient.put(`/assignments/${id}`, data);
    return response.data;
  },

  publishAssignment: async (id) => {
    const response = await apiClient.post(`/assignments/${id}/publish`);
    return response.data;
  },

  closeAssignment: async (id) => {
    const response = await apiClient.post(`/assignments/${id}/close`);
    return response.data;
  },

  deleteAssignment: async (id) => {
    const response = await apiClient.delete(`/assignments/${id}`);
    return response.data;
  },

  getAssignmentProgress: async (id) => {
    const response = await apiClient.get(`/assignments/${id}/progress`);
    return response.data;
  }
};
