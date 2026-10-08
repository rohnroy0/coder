import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { assignmentsApi } from '../../api/assignments';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import {
  ClipboardList,
  ChevronLeft,
  Clock,
  CheckCircle2,
  Award,
  Code2,
  ArrowRight,
  AlertTriangle
} from 'lucide-react';

export const StudentAssignmentDetailPage = () => {
  const { id } = useParams();
  const [assignment, setAssignment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
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

    if (id) fetchDetail();
  }, [id]);

  if (loading) return <LoadingSpinner message="Loading Assignment workspace..." />;
  if (!assignment) return <ErrorMessage message="Assignment not found or access restricted." />;

  const prog = assignment.my_progress || {};
  const isClosed = assignment.status === 'CLOSED';
  const isOverdue = prog.status === 'OVERDUE';

  return (
    <div className="space-y-6">
      <Link
        to="/student/assignments"
        className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
        <span>Back to My Assignments</span>
      </Link>

      <ErrorMessage message={error} onClose={() => setError('')} />

      {/* Overdue/Closed Warning Banner */}
      {(isClosed || isOverdue) && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-center space-x-3 text-amber-900 text-xs font-semibold">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
          <span>
            {isClosed
              ? 'This assignment has been closed by the instructor. New submissions are no longer accepted.'
              : 'The deadline for this assignment has passed.'}
          </span>
        </div>
      )}

      {/* Assignment Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900">{assignment.title}</h1>
            {assignment.description && (
              <p className="text-sm text-slate-600 mt-1">{assignment.description}</p>
            )}
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <span className="px-3 py-1 bg-indigo-50 text-indigo-700 font-extrabold text-xs rounded-full border border-indigo-200">
              {prog.status || 'IN_PROGRESS'}
            </span>
          </div>
        </div>

        {/* Progress & Deadline Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <div className="flex items-center space-x-3 text-xs">
            <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <span className="text-slate-500 font-semibold block">My Score</span>
              <span className="text-lg font-extrabold text-indigo-600">
                {prog.score || 0} / {assignment.total_points} pts
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <span className="text-slate-500 font-semibold block">Completion</span>
              <span className="text-lg font-extrabold text-slate-900">
                {prog.completed_problems || 0} / {assignment.problems?.length || 0} Solved
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <span className="text-slate-500 font-semibold block">Due Date</span>
              <span className="text-xs font-bold text-slate-800 font-mono">
                {assignment.due_at ? new Date(assignment.due_at).toLocaleString() : 'No Deadline'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Problems Roster */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
          <Code2 className="w-5 h-5 text-indigo-600" />
          <span>Assignment Problems</span>
        </h2>

        <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
          {assignment.problems?.map((prob, idx) => (
            <div
              key={prob.id}
              className="p-4 bg-slate-50/50 hover:bg-slate-50 flex items-center justify-between text-xs transition-colors"
            >
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-slate-400 font-bold">#{idx + 1}</span>
                  <span className="font-bold text-slate-900 text-sm">{prob.title}</span>
                </div>
                <div className="flex items-center space-x-3 text-slate-500">
                  <span className="font-semibold">Difficulty: {prob.difficulty || 'EASY'}</span>
                  <span>•</span>
                  <span className="font-bold text-indigo-600">{prob.points} Points</span>
                </div>
              </div>

              <div>
                <Link
                  to={`/student/problems/${prob.problem_id}/code?assignment_id=${assignment.id}`}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl transition-colors shadow-xs"
                >
                  <span>Solve Problem</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StudentAssignmentDetailPage;
