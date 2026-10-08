import React, { useState, useEffect } from 'react';
import { classroomsApi } from '../../api/classrooms';
import ClassroomCard from '../../components/classroom/ClassroomCard';
import JoinClassroomModal from '../../components/classroom/JoinClassroomModal';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { School, UserPlus } from 'lucide-react';

export const StudentClassrooms = () => {
  const [classrooms, setClassrooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchClassrooms = async () => {
    try {
      setLoading(true);
      const data = await classroomsApi.getStudentJoinedClassrooms();
      setClassrooms(data);
    } catch (err) {
      console.error('Failed to load classrooms:', err);
      setError('Unable to load your joined classrooms.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClassrooms();
  }, []);

  if (loading) return <LoadingSpinner message="Loading enrolled classrooms..." />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Joined Classrooms</h1>
          <p className="text-slate-600 text-sm mt-1">Classrooms you are currently enrolled in</p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center space-x-2 px-4 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors shadow-xs"
        >
          <UserPlus className="w-4.5 h-4.5" />
          <span>Join New Classroom</span>
        </button>
      </div>

      <ErrorMessage message={error} onClose={() => setError('')} />

      {classrooms.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center">
          <School className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-800">No Joined Classrooms</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto mb-6">
            You haven't joined any classrooms yet. Enter a join code from your teacher to enroll.
          </p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center space-x-2 px-5 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors shadow-xs"
          >
            <UserPlus className="w-4 h-4" />
            <span>Join Classroom</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {classrooms.map((cls) => (
            <ClassroomCard key={cls.id} classroom={cls} isTeacher={false} />
          ))}
        </div>
      )}

      <JoinClassroomModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => fetchClassrooms()}
      />
    </div>
  );
};

export default StudentClassrooms;
