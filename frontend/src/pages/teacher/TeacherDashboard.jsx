import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { classroomsApi } from '../../api/classrooms';
import ClassroomCard from '../../components/classroom/ClassroomCard';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { School, PlusCircle, ArrowRight } from 'lucide-react';

export const TeacherDashboard = () => {
  const [classrooms, setClassrooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const clsData = await classroomsApi.getTeacherClassrooms();
        setClassrooms(clsData);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setError('Unable to load teacher dashboard metrics.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <LoadingSpinner message="Loading Teacher Dashboard..." />;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Teacher Dashboard</h1>
        <p className="text-slate-600 text-sm mt-1">Overview of your managed classrooms and coding assessments</p>
      </div>

      <ErrorMessage message={error} />

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Classrooms</div>
            <div className="text-3xl font-extrabold text-slate-900 mt-2">{classrooms.length}</div>
          </div>
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
            <School className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Quick Actions</div>
          <div className="flex flex-col space-y-2">
            <Link
              to="/teacher/classrooms/create"
              className="px-3.5 py-2 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors flex items-center space-x-1.5"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create New Classroom</span>
            </Link>
            <Link
              to="/teacher/problems/create"
              className="px-3.5 py-2 text-xs font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors flex items-center space-x-1.5"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create Coding Problem</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Classrooms */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900">Your Classrooms</h2>
          <Link
            to="/teacher/classrooms"
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
          >
            <span>View All Classrooms</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {classrooms.length === 0 ? (
          <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center">
            <School className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <h3 className="font-semibold text-slate-800">No classrooms created yet</h3>
            <p className="text-xs text-slate-500 mt-1 mb-4">Create your first classroom to start enrolling students</p>
            <Link
              to="/teacher/classrooms/create"
              className="inline-flex items-center space-x-2 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create Classroom</span>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {classrooms.slice(0, 3).map((cls) => (
              <ClassroomCard key={cls.id} classroom={cls} isTeacher={true} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TeacherDashboard;
