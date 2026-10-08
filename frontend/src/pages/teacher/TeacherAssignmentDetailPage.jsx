import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { assignmentsApi } from '../../api/assignments';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import {
  ClipboardList,
  ChevronLeft,
  Clock,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Send,
  Lock,
  Users,
  Award
} from 'lucide-react';

export const TeacherAssignmentDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState('');

  const fetchDetail = async () => {
    try {
      setLoading(true);
      const data = await assignmentsApi.getAssignmentDetail(id);
      setAssignment(data);
    } catch (err) {
      console.error('Failed to fetch assignment detail:', err);
      setError('Unable to load assignment details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchDetail();
  }, [id]);

  const handlePublish = async () => {
    try {
      setUpdating(true);
      const updated = await assignmentsApi.publishAssignment(id);
      setAssignment(updated);
    } catch (err) {
      console.error('Failed to publish assignment:', err);
      setError(err.response?.data?.detail || 'Failed to publish assignment.');
    } finally {
      setUpdating(false);
    }
  };

  const handleClose = async () => {
    try {
      setUpdating(true);
      const updated = await assignmentsApi.closeAssignment(id);
      setAssignment(updated);
    } catch (err) {
      console.error('Failed to close assignment:', err);
      setError(err.response?.data?.detail || 'Failed to close assignment.');
    } finally {
      setUpdating(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this assignment?')) return;
    try {
      setUpdating(true);
      await assignmentsApi.deleteAssignment(id);
      navigate('/teacher/assignments');
    } catch (err) {
      console.error('Failed to delete assignment:', err);
      setError('Failed to delete assignment.');
      setUpdating(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading Assignment details..." />;
  if (!assignment) return <ErrorMessage message="Assignment not found." />;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'DRAFT':
        return <span className="px-3 py-1 bg-amber-100 text-amber-800 font-extrabold text-xs rounded-full border border-amber-300">Draft</span>;
      case 'PUBLISHED':
        return <span className="px-3 py-1 bg-emerald-100 text-emerald-800 font-extrabold text-xs rounded-full border border-emerald-300">Published</span>;
      case 'CLOSED':
        return <span className="px-3 py-1 bg-slate-200 text-slate-800 font-extrabold text-xs rounded-full border border-slate-300">Closed</span>;
      default:
        return null;
    }
  };

  const getProgressStatusBadge = (status) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 font-bold text-[10px] rounded-full">Completed</span>;
      case 'IN_PROGRESS':
        return <span className="px-2 py-0.5 bg-indigo-100 text-indigo-800 font-bold text-[10px] rounded-full">In Progress</span>;
      case 'OVERDUE':
        return <span className="px-2 py-0.5 bg-rose-100 text-rose-800 font-bold text-[10px] rounded-full">Overdue</span>;
      default:
        return <span className="px-2 py-0.5 bg-slate-100 text-slate-600 font-bold text-[10px] rounded-full">Not Started</span>;
    }
  };

  const studentProgressList = assignment.student_progress_list || [];

  return (
    <div className="space-y-6">
      <Link
        to="/teacher/assignments"
        className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
        <span>Back to Assignments</span>
      </Link>

      <ErrorMessage message={error} onClose={() => setError('')} />

      {/* Header Info Box */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-extrabold text-slate-900">{assignment.title}</h1>
              {getStatusBadge(assignment.status)}
            </div>
            {assignment.description && (
              <p className="text-sm text-slate-600">{assignment.description}</p>
            )}
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            {assignment.status === 'DRAFT' && (
              <button
                onClick={handlePublish}
                disabled={updating}
                className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl transition-colors shadow-xs"
              >
                <Send className="w-4 h-4" />
                <span>Publish Assignment</span>
              </button>
            )}

            {assignment.status === 'PUBLISHED' && (
              <button
                onClick={handleClose}
                disabled={updating}
                className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-slate-700 hover:bg-slate-800 text-white font-bold text-xs rounded-xl transition-colors shadow-xs"
              >
                <Lock className="w-4 h-4" />
                <span>Close Submissions</span>
              </button>
            )}

            <button
              onClick={handleDelete}
              disabled={updating}
              className="p-2 text-rose-600 hover:bg-rose-50 rounded-xl transition-colors border border-rose-200"
              title="Delete Assignment"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <div className="flex items-center space-x-3 text-xs">
            <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <span className="text-slate-500 font-semibold block">Total Points</span>
              <span className="text-lg font-extrabold text-slate-900">{assignment.total_points} pts</span>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <span className="text-slate-500 font-semibold block">Verified Problems</span>
              <span className="text-lg font-extrabold text-slate-900">{assignment.problems?.length || 0} Problems</span>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <span className="text-slate-500 font-semibold block">Deadline (UTC)</span>
              <span className="text-sm font-bold text-slate-800 font-mono">
                {assignment.due_at ? new Date(assignment.due_at).toLocaleString() : 'No Deadline Set'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Included Problems Section */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
          <ClipboardList className="w-5 h-5 text-indigo-600" />
          <span>Included Verified Problems</span>
        </h2>

        <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
          {assignment.problems?.map((p) => (
            <div key={p.id} className="p-3.5 bg-slate-50/50 flex items-center justify-between text-xs">
              <div>
                <span className="font-bold text-slate-900 text-sm block">{p.title}</span>
                <span className="text-slate-500 font-semibold">Difficulty: {p.difficulty || 'EASY'}</span>
              </div>
              <span className="px-3 py-1 bg-indigo-100 text-indigo-800 font-extrabold rounded-lg">
                {p.points} Points
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Student Progress Roster Table */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
            <Users className="w-5 h-5 text-indigo-600" />
            <span>Student Submission & Completion Progress</span>
          </h2>
          <span className="text-xs font-bold text-slate-500">
            {studentProgressList.length} Enrolled Students
          </span>
        </div>

        {studentProgressList.length === 0 ? (
          <p className="text-xs text-slate-500 py-6 text-center">No student progress recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b">
                <tr>
                  <th className="px-4 py-3">Student Name</th>
                  <th className="px-4 py-3">Completed Problems</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Last Activity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {studentProgressList.map((prog) => (
                  <tr key={prog.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-bold text-slate-800">{prog.student_name}</td>
                    <td className="px-4 py-3 font-semibold text-slate-700">
                      {prog.completed_problems} / {prog.total_problems}
                    </td>
                    <td className="px-4 py-3 font-extrabold text-indigo-600">{prog.score} pts</td>
                    <td className="px-4 py-3">{getProgressStatusBadge(prog.status)}</td>
                    <td className="px-4 py-3 text-slate-500 font-mono">
                      {prog.last_activity_at ? new Date(prog.last_activity_at).toLocaleString() : 'No activity'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default TeacherAssignmentDetailPage;
