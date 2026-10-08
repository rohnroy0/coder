import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { classroomsApi } from '../../api/classrooms';
import ErrorMessage from '../../components/common/ErrorMessage';
import { UserPlus, Loader2 } from 'lucide-react';

export const JoinClassroom = () => {
  const [joinCode, setJoinCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!joinCode.trim()) return;

    setLoading(true);
    setError('');

    try {
      const classroom = await classroomsApi.joinClassroom({ join_code: joinCode.trim() });
      navigate(`/student/classrooms/${classroom.id}`);
    } catch (err) {
      console.error('Failed to join classroom:', err);
      const detail = err.response?.data?.detail || 'Unable to join classroom. Please check the code.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-6 pt-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Join a Classroom</h1>
        <p className="text-slate-600 text-sm mt-1">Enter your teacher's 7-character join code to enroll</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <ErrorMessage message={error} onClose={() => setError('')} />

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="text-center pb-2">
            <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
              <UserPlus className="w-6 h-6" />
            </div>
            <label htmlFor="code" className="block text-sm font-medium text-slate-700">
              Classroom Join Code
            </label>
          </div>

          <input
            id="code"
            type="text"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
            placeholder="e.g. PY10192"
            maxLength={10}
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-mono tracking-widest text-center uppercase font-bold text-xl text-slate-900 placeholder:text-slate-400 placeholder:font-normal placeholder:tracking-normal placeholder:text-sm"
            required
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center items-center space-x-2 py-3 px-4 border border-transparent rounded-xl shadow-xs text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <span>Enroll in Classroom</span>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default JoinClassroom;
