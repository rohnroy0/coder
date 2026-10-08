import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { classroomsApi } from '../../api/classrooms';
import { assignmentsApi } from '../../api/assignments';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import {
  ClipboardList,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Award,
  ChevronRight,
  School
} from 'lucide-react';

export const StudentAssignmentsPage = () => {
  const [classrooms, setClassrooms] = useState([]);
  const [selectedClassroomId, setSelectedClassroomId] = useState('');
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchClassrooms = async () => {
      try {
        setLoading(true);
        const joined = await classroomsApi.getStudentJoinedClassrooms();
        setClassrooms(joined);
        if (joined.length > 0) {
          setSelectedClassroomId(joined[0].id.toString());
        }
      } catch (err) {
        console.error('Failed to fetch student classrooms:', err);
        setError('Unable to load joined classrooms.');
      } finally {
        setLoading(false);
      }
    };
    fetchClassrooms();
  }, []);

  useEffect(() => {
    if (!selectedClassroomId) return;
    const fetchAssignments = async () => {
      try {
        setError('');
        const list = await assignmentsApi.getClassroomAssignments(selectedClassroomId);
        setAssignments(list);
      } catch (err) {
        console.error('Failed to fetch assignments:', err);
        setError('Unable to load assignments for this classroom.');
      }
    };
    fetchAssignments();
  }, [selectedClassroomId]);

  if (loading) return <LoadingSpinner message="Loading your assignments..." />;

  const getProgressBadge = (myProgress) => {
    if (!myProgress) return null;
    const status = myProgress.status;

    switch (status) {
      case 'COMPLETED':
        return <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 font-extrabold text-xs rounded-full border border-emerald-200">Completed</span>;
      case 'IN_PROGRESS':
        return <span className="px-2.5 py-1 bg-indigo-50 text-indigo-700 font-extrabold text-xs rounded-full border border-indigo-200">In Progress</span>;
      case 'OVERDUE':
        return <span className="px-2.5 py-1 bg-rose-50 text-rose-700 font-extrabold text-xs rounded-full border border-rose-200">Overdue</span>;
      default:
        return <span className="px-2.5 py-1 bg-slate-100 text-slate-600 font-bold text-xs rounded-full border border-slate-200">Not Started</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 flex items-center space-x-2">
          <ClipboardList className="w-7 h-7 text-indigo-600" />
          <span>My Course Assignments</span>
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Complete assigned problem sets before deadlines to earn points and boost your mastery.
        </p>
      </div>

      <ErrorMessage message={error} onClose={() => setError('')} />

      {classrooms.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center space-y-3">
          <School className="w-10 h-10 text-slate-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-800">No Classrooms Joined</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            You are not enrolled in any classrooms. Join a classroom with a join code to view assignments.
          </p>
          <Link
            to="/student/join"
            className="inline-block text-xs font-bold text-indigo-600 hover:underline"
          >
            Join a classroom now &rarr;
          </Link>
        </div>
      ) : (
        <>
          {/* Classroom Selector */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center space-x-3">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">Select Classroom:</label>
            <select
              value={selectedClassroomId}
              onChange={(e) => setSelectedClassroomId(e.target.value)}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {classrooms.map((cls) => (
                <option key={cls.id} value={cls.id}>
                  {cls.name}
                </option>
              ))}
            </select>
          </div>

          {/* Assignments List */}
          <div className="space-y-4">
            {assignments.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center text-xs text-slate-500">
                No active assignments published for this classroom. Check back later!
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {assignments.map((assign) => {
                  const prog = assign.my_progress;
                  const isClosed = assign.status === 'CLOSED';

                  return (
                    <div
                      key={assign.id}
                      className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs hover:border-indigo-200 transition-all flex flex-col justify-between"
                    >
                      <div className="space-y-3">
                        <div className="flex items-start justify-between">
                          <h3 className="text-base font-bold text-slate-900 line-clamp-1">{assign.title}</h3>
                          {getProgressBadge(prog)}
                        </div>

                        {assign.description && (
                          <p className="text-xs text-slate-600 line-clamp-2">{assign.description}</p>
                        )}

                        <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-2 border-t border-slate-100">
                          <span className="font-semibold text-slate-700">
                            {prog?.completed_problems || 0} / {assign.problems?.length || 0} Solved
                          </span>
                          <span className="font-extrabold text-indigo-600">
                            Score: {prog?.score || 0} / {assign.total_points} pts
                          </span>
                          {assign.due_at && (
                            <span className="flex items-center space-x-1 font-mono text-slate-500">
                              <Clock className="w-3.5 h-3.5" />
                              <span>Due: {new Date(assign.due_at).toLocaleDateString()}</span>
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="pt-4 mt-3 flex justify-end">
                        <Link
                          to={`/student/assignments/${assign.id}`}
                          className="inline-flex items-center space-x-1 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl transition-colors shadow-xs"
                        >
                          <span>{isClosed ? 'View Assignment' : 'Start / Resume'}</span>
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default StudentAssignmentsPage;
