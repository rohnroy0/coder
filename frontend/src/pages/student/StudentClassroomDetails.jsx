import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { classroomsApi } from '../../api/classrooms';
import { assignmentsApi } from '../../api/assignments';
import { problemsApi } from '../../api/problems';
import { analyticsApi } from '../../api/analytics';
import { useAuth } from '../../context/AuthContext';
import ClassroomHeader from '../../components/classroom/ClassroomHeader';
import ProblemCard from '../../components/problems/ProblemCard';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { Code2, Trophy } from 'lucide-react';

export const StudentClassroomDetails = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const [classroom, setClassroom] = useState(null);
  const [problems, setProblems] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [clsData, assignments, allProblems, leaderboardData] = await Promise.all([
          classroomsApi.getClassroomDetail(id),
          assignmentsApi.getClassroomAssignments(id),
          problemsApi.getProblems(),
          analyticsApi.getClassroomLeaderboard(id).catch(() => []),
        ]);
        setClassroom(clsData);
        setLeaderboard(leaderboardData);

        // Scope "Available Coding Challenges" to problems actually assigned to
        // THIS classroom, rather than the whole global problem bank.
        const assignedProblemIds = new Set(
          assignments.flatMap((a) => a.problems.map((p) => p.problem_id))
        );
        setProblems(allProblems.filter((p) => assignedProblemIds.has(p.id)));
      } catch (err) {
        console.error('Failed to load classroom detail:', err);
        setError('Unable to load classroom details.');
      } finally {
        setLoading(false);
      }
    };

    if (id) fetchData();
  }, [id]);

  if (loading) return <LoadingSpinner message="Loading classroom details..." />;

  const myEntry = leaderboard.find((lb) => lb.student_id === user?.id);

  return (
    <div className="space-y-6">
      <ErrorMessage message={error} />

      {classroom && (
        <>
          <ClassroomHeader
            classroom={classroom}
            studentCount={classroom.students?.length || 0}
            isTeacher={false}
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
              Overview
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
              {myEntry && (
                <span className="ml-1 px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded-full text-[10px] font-extrabold">
                  You're #{myEntry.rank}
                </span>
              )}
            </button>
          </div>

          {activeTab === 'overview' && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center space-x-2">
                <Code2 className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-bold text-slate-900">Available Coding Challenges</h2>
              </div>

              {problems.length === 0 ? (
                <div className="text-center py-8 text-slate-500 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-sm">
                  No coding challenges assigned to this classroom yet. Check back later!
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {problems.map((prob) => (
                    <ProblemCard key={prob.id} problem={prob} isTeacher={false} />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'leaderboard' && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
              <div className="flex items-center space-x-2">
                <Trophy className="w-5 h-5 text-amber-500" />
                <h2 className="text-base font-bold text-slate-900">Classroom Leaderboard</h2>
              </div>

              {leaderboard.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-6">
                  No leaderboard entries yet — solve a problem to get on the board!
                </p>
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
                      {leaderboard.map((lb) => {
                        const isMe = lb.student_id === user?.id;
                        return (
                          <tr key={lb.student_id} className={isMe ? 'bg-indigo-50/70' : 'hover:bg-slate-50'}>
                            <td className="px-4 py-3 font-extrabold text-slate-900">#{lb.rank}</td>
                            <td className="px-4 py-3 font-semibold text-slate-800">
                              <span className="flex items-center space-x-1.5">
                                <span>{lb.student_name}</span>
                                {isMe && (
                                  <span className="px-1.5 py-0.5 bg-indigo-600 text-white rounded-full text-[10px] font-extrabold">
                                    You
                                  </span>
                                )}
                              </span>
                            </td>
                            <td className="px-4 py-3 font-extrabold text-indigo-600">{lb.points} pts</td>
                            <td className="px-4 py-3 font-semibold text-emerald-600">{lb.problems_solved}</td>
                            <td className="px-4 py-3 text-slate-700 font-bold">{lb.accuracy}%</td>
                            <td className="px-4 py-3 text-slate-500">{lb.avg_attempts}</td>
                            <td className="px-4 py-3 font-mono text-slate-500">{lb.avg_execution_time}s</td>
                          </tr>
                        );
                      })}
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

export default StudentClassroomDetails;
