import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { problemsApi } from '../../api/problems';
import DifficultyBadge from '../../components/problems/DifficultyBadge';
import TestCaseForm from '../../components/problems/TestCaseForm';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { Code2, Trash2, CheckCircle2, ShieldAlert } from 'lucide-react';

export const ProblemDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [problem, setProblem] = useState(null);
  const [testCases, setTestCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testCaseLoading, setTestCaseLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchProblemAndTestCases = async () => {
    try {
      setLoading(true);
      const [probData, tcData] = await Promise.all([
        problemsApi.getProblemDetail(id),
        problemsApi.getTestCases(id),
      ]);
      setProblem(probData);
      setTestCases(tcData);
    } catch (err) {
      console.error('Failed to load problem details:', err);
      setError('Unable to load problem details or test cases.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchProblemAndTestCases();
  }, [id]);

  const handleAddTestCase = async (testCaseData) => {
    setTestCaseLoading(true);
    setError('');

    try {
      const newTc = await problemsApi.addTestCase(id, testCaseData);
      setTestCases((prev) => [...prev, newTc]);
      setProblem((prev) => prev ? { ...prev, test_case_count: (prev.test_case_count || 0) + 1 } : prev);
    } catch (err) {
      console.error('Failed to add test case:', err);
      setError(err.response?.data?.detail || 'Failed to add test case.');
    } finally {
      setTestCaseLoading(false);
    }
  };

  const handleDeleteTestCase = async (tcId) => {
    if (!window.confirm('Delete this test case?')) return;
    try {
      await problemsApi.deleteTestCase(id, tcId);
      setTestCases((prev) => prev.filter((tc) => tc.id !== tcId));
      setProblem((prev) => prev ? { ...prev, test_case_count: Math.max(0, (prev.test_case_count || 0) - 1) } : prev);
    } catch (err) {
      console.error('Failed to delete test case:', err);
      alert(err.response?.data?.detail || 'Failed to delete test case.');
    }
  };

  const handleDeleteProblem = async () => {
    if (!window.confirm('Are you sure you want to delete this problem and all its test cases?')) return;
    try {
      await problemsApi.deleteProblem(id);
      navigate('/teacher');
    } catch (err) {
      console.error('Failed to delete problem:', err);
      alert(err.response?.data?.detail || 'Failed to delete problem.');
    }
  };

  if (loading) return <LoadingSpinner message="Loading problem details..." />;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <ErrorMessage message={error} onClose={() => setError('')} />

      {problem && (
        <>
          {/* Header */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-start space-x-4">
                <div className="p-3.5 bg-indigo-100 text-indigo-600 rounded-xl">
                  <Code2 className="w-8 h-8" />
                </div>
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <DifficultyBadge difficulty={problem.difficulty} />
                    <span className="text-xs text-slate-400">•</span>
                    <span className="text-xs text-slate-500 font-medium">
                      {testCases.length} Test Cases
                    </span>
                  </div>
                  <h1 className="text-2xl font-bold text-slate-900">{problem.title}</h1>
                </div>
              </div>

              <button
                onClick={handleDeleteProblem}
                className="px-4 py-2 text-xs font-semibold text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl transition-colors flex items-center space-x-1.5 self-start md:self-auto"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete Problem</span>
              </button>
            </div>

            <div className="mt-6 pt-6 border-t border-slate-100">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Problem Description & Statement
              </h3>
              <div className="text-sm text-slate-700 whitespace-pre-line leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200/60">
                {problem.description}
              </div>
            </div>
          </div>

          {/* Test Case Management Section */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-indigo-600" />
                <span>Hidden Evaluation Test Cases ({testCases.length})</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Add test cases used by the backend execution engine to grade student code submissions.
              </p>
            </div>

            {/* Existing Test Cases List */}
            {testCases.length === 0 ? (
              <div className="p-6 bg-amber-50/50 border border-amber-200/60 rounded-xl text-amber-800 text-xs text-center">
                <ShieldAlert className="w-5 h-5 text-amber-600 mx-auto mb-1" />
                No test cases added yet. Students will get <code>ACCEPTED</code> automatically until you add test cases.
              </div>
            ) : (
              <div className="space-y-3">
                {testCases.map((tc, index) => (
                  <div key={tc.id} className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-start justify-between">
                    <div className="space-y-2 flex-1 mr-4">
                      <div className="text-xs font-bold text-indigo-600 uppercase tracking-wider">
                        Test Case #{index + 1} (ID: {tc.id})
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <div>
                          <span className="font-medium text-slate-500 block mb-0.5">Input (stdin):</span>
                          <pre className="p-2 bg-white border border-slate-200 rounded-lg font-mono text-slate-800 whitespace-pre-wrap">{tc.input}</pre>
                        </div>
                        <div>
                          <span className="font-medium text-slate-500 block mb-0.5">Expected Output (stdout):</span>
                          <pre className="p-2 bg-white border border-slate-200 rounded-lg font-mono text-slate-800 whitespace-pre-wrap">{tc.expected_output}</pre>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => handleDeleteTestCase(tc.id)}
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete Test Case"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Add Test Case Form */}
            <TestCaseForm onAddTestCase={handleAddTestCase} loading={testCaseLoading} />
          </div>
        </>
      )}
    </div>
  );
};

export default ProblemDetails;
