import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { classroomsApi } from '../../api/classrooms';
import ClassroomCard from '../../components/classroom/ClassroomCard';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { School, PlusCircle } from 'lucide-react';

export const TeacherClassrooms = () => {
  const [classrooms, setClassrooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchClassrooms = async () => {
    try {
      setLoading(true);
      const data = await classroomsApi.getTeacherClassrooms();
      setClassrooms(data);
    } catch (err) {
      console.error('Failed to load classrooms:', err);
      setError('Unable to load classrooms list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClassrooms();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this classroom?')) return;
    try {
      await classroomsApi.deleteClassroom(id);
      setClassrooms((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.error('Delete classroom error:', err);
      alert(err.response?.data?.detail || 'Failed to delete classroom.');
    }
  };

  if (loading) return <LoadingSpinner message="Loading classrooms..." />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Managed Classrooms</h1>
          <p className="text-slate-600 text-sm mt-1">Create and manage your student classrooms and join codes</p>
        </div>

        <Link
          to="/teacher/classrooms/create"
          className="inline-flex items-center space-x-2 px-4 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors shadow-xs"
        >
          <PlusCircle className="w-4.5 h-4.5" />
          <span>Create New Classroom</span>
        </Link>
      </div>

      <ErrorMessage message={error} onClose={() => setError('')} />

      {classrooms.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center">
          <School className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-800">No Classrooms Found</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto mb-6">
            You haven't created any classrooms yet. Start by creating a classroom for your students.
          </p>
          <Link
            to="/teacher/classrooms/create"
            className="inline-flex items-center space-x-2 px-5 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors shadow-xs"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Create Classroom</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {classrooms.map((cls) => (
            <ClassroomCard key={cls.id} classroom={cls} isTeacher={true} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
};

export default TeacherClassrooms;
