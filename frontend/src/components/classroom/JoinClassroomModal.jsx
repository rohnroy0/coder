import React, { useState } from 'react';
import { classroomsApi } from '../../api/classrooms';
import ErrorMessage from '../common/ErrorMessage';
import { UserPlus, X, Loader2 } from 'lucide-react';

export const JoinClassroomModal = ({ isOpen, onClose, onSuccess }) => {
  const [joinCode, setJoinCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!joinCode.trim()) {
      setError('Please enter a join code.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const classroom = await classroomsApi.joinClassroom({ join_code: joinCode.trim() });
      setJoinCode('');
      onSuccess && onSuccess(classroom);
      onClose();
    } catch (err) {
      console.error('Join classroom error:', err);
      const detail = err.response?.data?.detail || 'Unable to join classroom. Please check the code.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100 relative animate-in fade-in zoom-in-95 duration-200">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
            <UserPlus className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Join a Classroom</h2>
            <p className="text-xs text-slate-500">Ask your teacher for the 7-character join code</p>
          </div>
        </div>

        <ErrorMessage message={error} onClose={() => setError('')} />

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="joinCode" className="block text-sm font-medium text-slate-700 mb-1">
              Classroom Join Code
            </label>
            <input
              type="text"
              id="joinCode"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              placeholder="e.g. PY10192"
              maxLength={10}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-mono tracking-widest text-center uppercase font-bold text-lg text-slate-900 placeholder:text-slate-400 placeholder:font-normal placeholder:tracking-normal placeholder:text-sm"
              required
            />
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center space-x-2 px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl transition-colors shadow-xs"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              <span>Join Classroom</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default JoinClassroomModal;
