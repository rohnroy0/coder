import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { problemsApi } from '../../api/problems';
import ProblemForm from '../../components/problems/ProblemForm';

export const CreateProblem = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleCreate = async (formData) => {
    setLoading(true);
    setError('');

    try {
      const createdProblem = await problemsApi.createProblem(formData);
      // Redirect to problem details where teacher can add test cases
      navigate(`/teacher/problems/${createdProblem.id}`);
    } catch (err) {
      console.error('Failed to create problem:', err);
      const detail = err.response?.data?.detail || 'Unable to create problem. Please try again.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <ProblemForm onSubmit={handleCreate} loading={loading} error={error} />
    </div>
  );
};

export default CreateProblem;
