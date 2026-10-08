import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { classroomsApi } from '../../api/classrooms';
import { assignmentsApi } from '../../api/assignments';
import { problemsApi } from '../../api/problems';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import {
  ClipboardList,
  PlusCircle,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
  Calendar,
  Check
} from 'lucide-react';

export const TeacherAssignmentsPage = () => {
  const [classrooms, setClassrooms] = useState([]);
  const [selectedClassroomId, setSelectedClassroomId] = useState('');
  const [assignments, setAssignments] = useState([]);
  const [verifiedProblems, setVerifiedProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [modalClassroomId, setModalClassroomId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [selectedProblems, setSelectedProblems] = useState([]); // [{ problem_id, points, order }]
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState('');

  useEffect(() => {
    const fetchInitial = async () => {
      try {
        setLoading(true);
        const [clsList, probsList] = await Promise.all([
          classroomsApi.getTeacherClassrooms(),
          problemsApi.getProblems()
        ]);
        setClassrooms(clsList);
        if (clsList.length > 0) {
          setSelectedClassroomId(clsList[0].id.toString());
          setModalClassroomId(clsList[0].id.toString());
        }
        // Filter verified problems
        const verified = probsList.filter((p) => p.status === 'VERIFIED' || !p.status);
        setVerifiedProblems(verified);
      } catch (err) {
        console.error('Failed to fetch initial teacher data:', err);
        setError('Failed to load classrooms or problems.');
      } finally {
        setLoading(false);
      }
    };
    fetchInitial();
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

  const toggleProblemSelection = (problemId) => {
    if (selectedProblems.some((p) => p.problem_id === problemId)) {
      setSelectedProblems(selectedProblems.filter((p) => p.problem_id !== problemId));
    } else {
      setSelectedProblems([
        ...selectedProblems,
        { problem_id: problemId, points: 100, order: selectedProblems.length + 1 }
      ]);
    }
  };

  const handlePointsChange = (problemId, points) => {
    const val = Math.max(1, Number(points) || 0);
    setSelectedProblems(
      selectedProblems.map((p) => (p.problem_id === problemId ? { ...p, points: val } : p))
    );
  };

  const handleCreateAssignment = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      setModalError('Title is required.');
      return;
    }
    if (!modalClassroomId) {
      setModalError('Classroom selection is required.');
      return;
    }
    if (selectedProblems.length === 0) {
      setModalError('At least one verified problem must be selected.');
      return;
    }

    try {
      setSubmitting(true);
      setModalError('');
      const payload = {
        classroom_id: Number(modalClassroomId),
        title,
        description,
        due_at: dueDate ? new Date(dueDate).toISOString() : null,
        problems: selectedProblems
      };

      await assignmentsApi.createAssignment(payload);
      setShowCreateModal(false);
      setTitle('');
      setDescription('');
      setDueDate('');
      setSelectedProblems([]);
      // Refresh assignments if currently viewing modal classroom
      if (selectedClassroomId === modalClassroomId) {
        const updated = await assignmentsApi.getClassroomAssignments(modalClassroomId);
        setAssignments(updated);
      } else {
        setSelectedClassroomId(modalClassroomId);
      }
    } catch (err) {
      console.error('Failed to create assignment:', err);
      const detail = err.response?.data?.detail || 'Failed to create assignment.';
      setModalError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading Assignment Workspace..." />;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'DRAFT':
        return <span className="px-2.5 py-1 bg-amber-50 text-amber-700 font-bold text-xs rounded-full border border-amber-200">Draft</span>;
      case 'PUBLISHED':
        return <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 font-bold text-xs rounded-full border border-emerald-200">Published</span>;
      case 'CLOSED':
        return <span className="px-2.5 py-1 bg-slate-100 text-slate-700 font-bold text-xs rounded-full border border-slate-200">Closed</span>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 flex items-center space-x-2">
            <ClipboardList className="w-7 h-7 text-indigo-600" />
            <span>Assignment Management</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Create, publish, and track student assignments with strict deadlines and verified problem sets.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm rounded-xl transition-colors shadow-sm"
        >
          <PlusCircle className="w-5 h-5" />
          <span>Create Assignment</span>
        </button>
      </div>

      <ErrorMessage message={error} onClose={() => setError('')} />

      {classrooms.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center space-y-3">
          <AlertCircle className="w-10 h-10 text-slate-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-800">No Classrooms Available</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            You must create a classroom before assigning coursework to students.
          </p>
          <Link
            to="/teacher/classrooms/create"
            className="inline-block text-xs font-bold text-indigo-600 hover:underline"
          >
            Create your first classroom &rarr;
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
                  {cls.name} ({cls.join_code})
                </option>
              ))}
            </select>
          </div>

          {/* Assignment Cards List */}
          <div className="space-y-4">
            {assignments.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
                <FileText className="w-12 h-12 text-slate-300 mx-auto" />
                <h3 className="text-base font-bold text-slate-800">No Assignments Yet</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  There are no assignments created for this classroom. Click "Create Assignment" above to draft your first problem set.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {assignments.map((assign) => (
                  <div
                    key={assign.id}
                    className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs hover:border-indigo-200 transition-all flex flex-col justify-between"
                  >
                    <div className="space-y-3">
                      <div className="flex items-start justify-between">
                        <h3 className="text-base font-bold text-slate-900 line-clamp-1">{assign.title}</h3>
                        {getStatusBadge(assign.status)}
                      </div>

                      {assign.description && (
                        <p className="text-xs text-slate-600 line-clamp-2">{assign.description}</p>
                      )}

                      <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-2 border-t border-slate-100">
                        <span className="flex items-center space-x-1 font-semibold text-slate-700">
                          <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                          <span>{assign.problems?.length || 0} Problems</span>
                        </span>
                        <span className="font-extrabold text-indigo-600">{assign.total_points} Points</span>
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
                        to={`/teacher/assignments/${assign.id}`}
                        className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-lg transition-colors"
                      >
                        Manage & Track Progress &rarr;
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* CREATE ASSIGNMENT MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-2xl w-full p-6 space-y-5 shadow-xl my-8">
            <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              <ClipboardList className="w-5 h-5 text-indigo-600" />
              <span>Create New Assignment</span>
            </h2>

            <ErrorMessage message={modalError} onClose={() => setModalError('')} />

            <form onSubmit={handleCreateAssignment} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Target Classroom *</label>
                <select
                  value={modalClassroomId}
                  onChange={(e) => setModalClassroomId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800"
                >
                  {classrooms.map((cls) => (
                    <option key={cls.id} value={cls.id}>
                      {cls.name} ({cls.join_code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Assignment Title *</label>
                <input
                  type="text"
                  placeholder="e.g. Midterm Coding Assignment - Python Basics"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Description / Instructions</label>
                <textarea
                  rows="2"
                  placeholder="Optional instructions or guidelines for students..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1 flex items-center space-x-1">
                  <Calendar className="w-3.5 h-3.5 text-slate-500" />
                  <span>Due Date & Time (UTC)</span>
                </label>
                <input
                  type="datetime-local"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Select Verified Problems Section */}
              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-700">
                  Select Verified Problems * ({selectedProblems.length} selected)
                </label>
                {verifiedProblems.length === 0 ? (
                  <div className="p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-xs">
                    No verified problems found. Please create or verify problems using Ollama AI validator before adding to assignments.
                  </div>
                ) : (
                  <div className="max-h-48 overflow-y-auto border border-slate-200 rounded-xl divide-y divide-slate-100 p-1 bg-slate-50">
                    {verifiedProblems.map((prob) => {
                      const isSelected = selectedProblems.some((p) => p.problem_id === prob.id);
                      const currentItem = selectedProblems.find((p) => p.problem_id === prob.id);

                      return (
                        <div
                          key={prob.id}
                          className={`p-2.5 rounded-lg flex items-center justify-between text-xs transition-colors ${
                            isSelected ? 'bg-indigo-50/80 border border-indigo-200' : 'hover:bg-white'
                          }`}
                        >
                          <div
                            onClick={() => toggleProblemSelection(prob.id)}
                            className="flex items-center space-x-2 cursor-pointer flex-1"
                          >
                            <div className={`w-4 h-4 rounded border flex items-center justify-center ${isSelected ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-slate-300 bg-white'}`}>
                              {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                            </div>
                            <span className="font-bold text-slate-800">{prob.title}</span>
                            <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded font-bold text-[10px]">VERIFIED</span>
                          </div>

                          {isSelected && (
                            <div className="flex items-center space-x-1.5 ml-2">
                              <span className="text-[10px] text-slate-500 font-bold">Points:</span>
                              <input
                                type="number"
                                value={currentItem.points}
                                onChange={(e) => handlePointsChange(prob.id, e.target.value)}
                                className="w-16 px-2 py-1 bg-white border border-slate-300 rounded text-xs text-center font-bold text-slate-800"
                              />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition-colors shadow-xs disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Save Draft Assignment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeacherAssignmentsPage;
