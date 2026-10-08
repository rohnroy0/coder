import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { classroomsApi } from '../../api/classrooms';
import { assignmentsApi } from '../../api/assignments';
import { problemsApi } from '../../api/problems';
import { analyticsApi } from '../../api/analytics';
import ClassroomHeader from '../../components/classroom/ClassroomHeader';
import StudentRoster from '../../components/classroom/StudentRoster';
import ProblemCard from '../../components/problems/ProblemCard';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { Code2, PlusCircle, Trophy, BarChart3, AlertTriangle, Users, Target, CheckCircle2 } from 'lucide-react';

export const ClassroomDetails = () => {
  const { id } = useParams();
  const [classroom, setClassroom] = useState(null);
  const [problems, setProblems] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [roster, setRoster] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pasteToggleLoading, setPasteToggleLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [clsData, assignments, allProblems, analyticsData, rosterData] = await Promise.all([
          classroomsApi.getClassroomDetail(id),
          assignmentsApi.getClassroomAssignments(id),
          problemsApi.getProblems(),
          analyticsApi.getClassroomAnalytics(id).catch(() => null),
          classroomsApi.getStudentRoster(id).catch(() => null),
        ]);
        setClassroom(clsData);

        // Scope "Available Problems" to problems actually assigned to THIS
        // classroom, rather than the whole global problem bank.
        const assignedProblemIds = new Set(
          assignments.flatMap((a) => a.problems.map((p) => p.problem_id))
        );
        setProblems(allProblems.filter((p) => assignedProblemIds.has(p.id)));
        setAnalytics(analyticsData);
        setRoster(rosterData);
      } catch (err) {
        console.error('Failed to fetch classroom details:', err);
        setError('Unable to load classroom details.');
      } finally {
        setLoading(false);
      }
    };

    if (id) fetchData();
  }, [id]);

  const handleTogglePasteDisabled = async () => {
    if (!classroom) return;
    setPasteToggleLoading(true);
    try {
      const updated = await classroomsApi.updateClassroomSettings(id, {
        disable_paste: !classroom.disable_paste,
      });
      setClassroom((prev) => ({ ...prev, disable_paste: updated.disable_paste }));
    } catch (err) {
      console.error('Failed to update paste setting:', err);
      setError('Unable to update the paste setting. Please try again.');
    } finally {
      setPasteToggleLoading(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading classroom details & analytics..." />;

  const overview = analytics?.overview || {};
  const leaderboard = analytics?.leaderboard || [];
  const topics = analytics?.topics || [];
  const struggling = analytics?.struggling_students || [];

  return (
    <div className="space-y-6">
      <ErrorMessage message={error} />

      {classroom && (
        <>
          <ClassroomHeader
            classroom={classroom}
            studentCount={classroom.students?.length || 0}
            isTeacher={true}
            onTogglePasteDisabled={handleTogglePasteDisabled}
            pasteToggleLoading={pasteToggleLoading}
          />

          {/* Navigation Tabs */}
          <div className="flex items-center space-x-2 border-b border-slate-200">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2.5 text-xs font-bold transition-colors border-b-2 ${
                activeTab === 'overview'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              Class Roster & Problems
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`px-4 py-2.5 text-xs font-bold transition-colors border-b-2 flex items-center space-x-1.5 ${
                activeTab === 'analytics'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Class Analytics</span>
            </button>
            <button
              onClick={() => setActiveTab('leaderboard')}
              className={`px-4 py-2.5 text-xs font-bold transition-colors border-b-2 flex items-center space-x-1.5 ${
                activeTab === 'leaderboard'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Trophy className="w-4 h-4 text-amber-500" />
              <span>Leaderboard ({leaderboard.length})</span>
            </button>
          </div>

          {/* TAB 1: Class Roster & Problems */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Student Roster (2 Cols) */}
              <div className="lg:col-span-2">
                <StudentRoster classroomId={id} students={classroom.students || []} roster={roster} />
              </div>

              {/* Classroom Problems Sidebar */}
              <div className="space-y-4">
                <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      <Code2 className="w-5 h-5 text-indigo-600" />
                      <h2 className="text-base font-bold text-slate-900">Classroom Problems</h2>
                    </div>
                    <Link
                      to="/teacher/assignments"
                      className="p-1 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                      title="Manage Assignments"
                    >
                      <PlusCircle className="w-5 h-5" />
                    </Link>
                  </div>

                  {problems.length === 0 ? (
                    <p className="text-xs text-slate-500 text-center py-4">
                      No problems assigned to this classroom yet. Create an{' '}
                      <Link to="/teacher/assignments" className="text-indigo-600 font-semibold hover:underline">
                        assignment
                      </Link>{' '}
                      to add problems here.
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {problems.map((prob) => (
                        <ProblemCard key={prob.id} problem={prob} isTeacher={true} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Class Analytics */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              {/* Class Overview Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Enrolled Students</span>
                  <div className="text-2xl font-extrabold text-slate-900">{overview.total_students ?? 0}</div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Class Avg Points</span>
                  <div className="text-2xl font-extrabold text-indigo-600">{overview.avg_class_score ?? 0} pts</div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Class Avg Accuracy</span>
                  <div className="text-2xl font-extrabold text-emerald-600">{overview.avg_class_accuracy ?? 0}%</div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Total Submissions</span>
                  <div className="text-2xl font-extrabold text-slate-900">{overview.total_submissions ?? 0}</div>
                </div>
              </div>

              {/* Struggling Students Alert Section */}
              {struggling.length > 0 && (
                <div className="bg-rose-50/80 border border-rose-200 rounded-xl p-5 space-y-3">
                  <div className="flex items-center space-x-2 text-rose-800 font-bold text-sm">
                    <AlertTriangle className="w-5 h-5 text-rose-600" />
                    <span>Students Requiring Attention ({struggling.length})</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {struggling.map((st) => (
                      <div key={st.student_id} className="bg-white p-3 rounded-lg border border-rose-200 text-xs flex justify-between items-center">
                        <div>
                          <Link to={`/teacher/classrooms/${id}/students/${st.student_id}`} className="font-bold text-slate-900 block hover:text-indigo-600 hover:underline">
                            {st.student_name}
                          </Link>
                          <span className="text-slate-500">Accuracy: {st.accuracy}% • Avg Attempts: {st.avg_attempts}</span>
                        </div>
                        <span className="px-2 py-1 bg-rose-100 text-rose-800 font-bold rounded-md text-[10px]">Needs Practice</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Topic Performance Table */}
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
                <h3 className="text-sm font-bold text-slate-900">Class Topic Performance</h3>
                {topics.length === 0 ? (
                  <p className="text-xs text-slate-500 py-4 text-center">No topic data available yet.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 text-slate-600 font-semibold uppercase border-b">
                        <tr>
                          <th className="px-4 py-2.5">Topic</th>
                          <th className="px-4 py-2.5">Students Attempting</th>
                          <th className="px-4 py-2.5">Avg Accuracy</th>
                          <th className="px-4 py-2.5">Avg Attempts</th>
                          <th className="px-4 py-2.5">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {topics.map((t, idx) => (
                          <tr key={idx}>
                            <td className="px-4 py-3 font-bold text-slate-800">{t.topic}</td>
                            <td className="px-4 py-3 text-slate-600">{t.students_attempting}</td>
                            <td className="px-4 py-3 font-bold text-slate-900">{t.avg_accuracy}%</td>
                            <td className="px-4 py-3 text-slate-600">{t.avg_attempts}</td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                                t.classification === 'Strong' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                              }`}>
                                {t.classification}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: Classroom Leaderboard */}
          {activeTab === 'leaderboard' && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
              <div className="flex items-center space-x-2">
                <Trophy className="w-5 h-5 text-amber-500" />
                <h2 className="text-base font-bold text-slate-900">Classroom Leaderboard</h2>
              </div>

              {leaderboard.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-6">No leaderboard entries available for this classroom.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b">
                      <tr>
                        <th className="px-4 py-3">Rank</th>
                        <th className="px-4 py-3">Student</th>
                        <th className="px-4 py-3">Points</th>
                        <th className="px-4 py-3">Solved</th>
                        <th className="px-4 py-3">Accuracy</th>
                        <th className="px-4 py-3">Avg Attempts</th>
                        <th className="px-4 py-3">Avg Exec Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {leaderboard.map((lb) => (
                        <tr key={lb.student_id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 font-extrabold text-slate-900">#{lb.rank}</td>
                          <td className="px-4 py-3 font-semibold text-slate-800">
                            <Link to={`/teacher/classrooms/${id}/students/${lb.student_id}`} className="hover:text-indigo-600 hover:underline">
                              {lb.student_name}
                            </Link>
                          </td>
                          <td className="px-4 py-3 font-extrabold text-indigo-600">{lb.points} pts</td>
                          <td className="px-4 py-3 font-semibold text-emerald-600">{lb.problems_solved}</td>
                          <td className="px-4 py-3 text-slate-700 font-bold">{lb.accuracy}%</td>
                          <td className="px-4 py-3 text-slate-500">{lb.avg_attempts}</td>
                          <td className="px-4 py-3 font-mono text-slate-500">{lb.avg_execution_time}s</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ClassroomDetails;
