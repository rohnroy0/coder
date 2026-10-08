import apiClient from './axios';

export const classroomsApi = {
  createClassroom: async (data) => {
    // data: { name, description }
    const response = await apiClient.post('/classrooms', data);
    return response.data;
  },

  getTeacherClassrooms: async () => {
    const response = await apiClient.get('/classrooms/my');
    return response.data;
  },

  joinClassroom: async (data) => {
    // data: { join_code }
    const response = await apiClient.post('/classrooms/join', data);
    return response.data;
  },

  getStudentJoinedClassrooms: async () => {
    const response = await apiClient.get('/classrooms/joined');
    return response.data;
  },

  getClassroomDetail: async (id) => {
    const response = await apiClient.get(`/classrooms/${id}`);
    return response.data;
  },

  deleteClassroom: async (id) => {
    const response = await apiClient.delete(`/classrooms/${id}`);
    return response.data;
  },

  // Teacher-only: currently just { disable_paste }
  updateClassroomSettings: async (id, settings) => {
    const response = await apiClient.patch(`/classrooms/${id}/settings`, settings);
    return response.data;
  },

  // Teacher-only: student roster with rank/points/accuracy/progress
  getStudentRoster: async (classroomId) => {
    const response = await apiClient.get(`/classrooms/${classroomId}/students`);
    return response.data;
  },

  // Teacher-only: full Student Performance Profile
  getStudentProfile: async (classroomId, studentId) => {
    const response = await apiClient.get(`/classrooms/${classroomId}/students/${studentId}/profile`);
    return response.data;
  },

  // Teacher-only: one submission including its source code
  getStudentSubmission: async (classroomId, studentId, submissionId) => {
    const response = await apiClient.get(`/classrooms/${classroomId}/students/${studentId}/submissions/${submissionId}`);
    return response.data;
  },
};
