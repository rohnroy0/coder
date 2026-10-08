import React, { useState, useEffect } from 'react';
import { submissionsApi } from '../../api/submissions';
import SubmissionHistoryTable from '../../components/coding/SubmissionHistory';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';

export const SubmissionHistoryPage = () => {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchSubmissions = async () => {
      try {
        setLoading(true);
        const data = await submissionsApi.getMySubmissions();
        setSubmissions(data);
      } catch (err) {
        console.error('Failed to load submission history:', err);
        setError('Unable to fetch your submission history.');
      } finally {
        setLoading(false);
      }
    };

    fetchSubmissions();
  }, []);

  if (loading) return <LoadingSpinner message="Loading submission history..." />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Your Submission History</h1>
        <p className="text-slate-600 text-sm mt-1">
          Review your previous code evaluations and submission timestamps
        </p>
      </div>

      <ErrorMessage message={error} onClose={() => setError('')} />

      <SubmissionHistoryTable submissions={submissions} loading={loading} />
    </div>
  );
};

export default SubmissionHistoryPage;
