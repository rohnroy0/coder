import apiClient from './axios';

export const submissionsApi = {
  submitCode: async (submissionData) => {
    // submissionData: { problem_id, language, source_code }
    const response = await apiClient.post('/submissions', submissionData);
    return response.data;
  },

  runCode: async (runData) => {
    // runData: { problem_id, language, source_code }
    // Runs against the sample test cases only, no submission is recorded.
    const response = await apiClient.post('/submissions/run', runData);
    return response.data;
  },

  getMySubmissions: async () => {
    const response = await apiClient.get('/submissions/my');
    return response.data;
  },

  getFeedback: async (submissionId, hintLevel = 1) => {
    const response = await apiClient.post(`/submissions/${submissionId}/feedback`, {
      hint_level: hintLevel,
    });
    return response.data;
  },

  getFeedbackHistory: async (submissionId) => {
    const response = await apiClient.get(`/submissions/${submissionId}/feedback`);
    return response.data;
  },
};
