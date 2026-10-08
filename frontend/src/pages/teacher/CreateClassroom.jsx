import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { classroomsApi } from '../../api/classrooms';
import ErrorMessage from '../../components/common/ErrorMessage';
import { School, Loader2 } from 'lucide-react';

export const CreateClassroom = () => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    setError('');

    try {
      const classroom = await classroomsApi.createClassroom({
        name: name.trim(),
        description: description.trim(),
      });
      navigate(`/teacher/classrooms/${classroom.id}`);
    } catch (err) {
      console.error('Failed to create classroom:', err);
      const detail = err.response?.data?.detail || 'Unable to create classroom. Please try again.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Create a New Classroom</h1>
        <p className="text-slate-600 text-sm mt-1">
          Set up a classroom environment. A unique join code will be generated automatically.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div className="flex items-center space-x-3 pb-4 border-b border-slate-100">
          <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl">
            <School className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">Classroom Details</h2>
            <p className="text-xs text-slate-500">Provide name and optional course details</p>
          </div>
        </div>

        <ErrorMessage message={error} onClose={() => setError('')} />

        <div>
          <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1">
            Classroom Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Python Programming 101"
            className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900 placeholder:text-slate-400"
            required
          />
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-slate-700 mb-1">
            Description
          </label>
          <textarea
            id="description"
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief overview of course topics, target audience, or instructions..."
            className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900 placeholder:text-slate-400"
          />
        </div>

        <div className="flex justify-end space-x-3 pt-2">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="px-5 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center space-x-2 px-6 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl transition-colors shadow-xs"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            <span>Create Classroom</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateClassroom;
