import apiClient from './axios';

export const problemsApi = {
  createProblem: async (problemData) => {
    // problemData: { title, description, difficulty }
    const response = await apiClient.post('/problems', problemData);
    return response.data;
  },

  getProblems: async () => {
    const response = await apiClient.get('/problems');
    return response.data;
  },

  getProblemDetail: async (id) => {
    const response = await apiClient.get(`/problems/${id}`);
    return response.data;
  },

  addTestCase: async (problemId, testCaseData) => {
    // testCaseData: { input, expected_output }
    const response = await apiClient.post(`/problems/${problemId}/testcases`, testCaseData);
    return response.data;
  },

  getTestCases: async (problemId) => {
    const response = await apiClient.get(`/problems/${problemId}/testcases`);
    return response.data;
  },

  getSampleTestCases: async (problemId) => {
    const response = await apiClient.get(`/problems/${problemId}/sample-testcases`);
    return response.data;
  },

  deleteTestCase: async (problemId, testcaseId) => {
    const response = await apiClient.delete(`/problems/${problemId}/testcases/${testcaseId}`);
    return response.data;
  },

  deleteProblem: async (problemId) => {
    const response = await apiClient.delete(`/problems/${problemId}`);
    return response.data;
  },

  generateAIProblems: async (data) => {
    // data: { language, difficulty, topic, count }
    const response = await apiClient.post('/problems/generate', data);
    return response.data;
  },

  confirmAIProblem: async (problemId) => {
    const response = await apiClient.post(`/problems/${problemId}/confirm`);
    return response.data;
  },

  discardAIProblem: async (problemId) => {
    const response = await apiClient.post(`/problems/${problemId}/discard`);
    return response.data;
  },
};
