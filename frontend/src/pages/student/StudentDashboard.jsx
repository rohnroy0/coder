import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { classroomsApi } from '../../api/classrooms';
import { problemsApi } from '../../api/problems';
import { submissionsApi } from '../../api/submissions';
import { analyticsApi } from '../../api/analytics';
import { badgesApi } from '../../api/badges';
import ClassroomCard from '../../components/classroom/ClassroomCard';
import ProblemCard from '../../components/problems/ProblemCard';
import JoinClassroomModal from '../../components/classroom/JoinClassroomModal';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { School, Code2, History, UserPlus, ArrowRight, Award, CheckCircle, Trophy, Target, TrendingUp, Flame, Lock } from 'lucide-react';

export const StudentDashboard = () => {
  const [classrooms, setClassrooms] = useState([]);
  const [problems, setProblems] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [clsData, probData, subData, analyticsData, badgesData] = await Promise.all([
        classroomsApi.getStudentJoinedClassrooms(),
        problemsApi.getProblems(),
        submissionsApi.getMySubmissions(),
        analyticsApi.getMyAnalytics().catch(() => null),
        badgesApi.getMyBadges().catch(() => []),
      ]);
      setClassrooms(clsData);
      setProblems(probData);
      setSubmissions(subData);
      setAnalytics(analyticsData);
      setBadges(badgesData);
    } catch (err) {
      console.error('Failed to load student dashboard:', err);
      setError('Unable to load student dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const overview = analytics?.overview || {};
  const earnedBadgeCount = badges.filter((b) => b.earned).length;

  if (loading) return <LoadingSpinner message="Loading Student Dashboard..." />;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Student Dashboard</h1>
          <p className="text-slate-600 text-sm mt-1">Practice coding challenges, track your score, and monitor performance</p>
        </div>

        <div className="flex items-center space-x-3 self-start sm:self-auto">
          <Link
            to="/student/performance"
            className="inline-flex items-center space-x-2 px-4 py-2.5 text-sm font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-xl transition-colors shadow-xs"
          >
            <TrendingUp className="w-4.5 h-4.5 text-indigo-600" />
            <span>Full Performance Report</span>
          </Link>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center space-x-2 px-4 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors shadow-xs"
          >
            <UserPlus className="w-4.5 h-4.5" />
            <span>Join Classroom</span>
          </button>
        </div>
      </div>

      <ErrorMessage message={error} />

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
        <div className="bg-gradient-to-br from-orange-500 to-amber-600 text-white p-6 rounded-2xl border border-orange-400/50 shadow-xs flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-orange-100 uppercase tracking-wider">Learning Streak</div>
            <div className="text-3xl font-extrabold mt-1 flex items-baseline space-x-1">
              <span>{overview.current_streak ?? 0}</span>
              <span className="text-sm font-normal text-orange-100">day{(overview.current_streak ?? 0) === 1 ? '' : 's'}</span>
            </div>
            <div className="text-xs text-orange-100 mt-1">
              {overview.current_streak > 0 ? 'Keep it going!' : 'Solve something today to start one'}
            </div>
          </div>
          <div className="p-3 bg-white/20 rounded-xl">
            <Flame className="w-7 h-7 text-white" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-indigo-900 to-slate-900 text-white p-6 rounded-2xl border border-indigo-800 shadow-xs flex items-center justify-between">
          <div className="w-full">
            <div className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">Total Score</div>
            <div className="text-3xl font-extrabold mt-1">{overview.points ?? 0} <span className="text-sm font-normal text-indigo-300">pts</span></div>
            <div className="text-xs text-indigo-300 mt-1">
              Level {overview.level ?? 1} · {overview.level_title ?? 'Novice'}
              {overview.rank_in_classroom ? ` · Rank #${overview.rank_in_classroom}` : ''}
            </div>
            <div className="h-1 bg-indigo-800/60 rounded-full overflow-hidden mt-1.5">
              <div
                className="h-full bg-amber-400 rounded-full"
                style={{ width: `${overview.level_progress_pct ?? 0}%` }}
              />
            </div>
          </div>
          <div className="p-3 bg-indigo-800/50 rounded-xl shrink-0 ml-3">
            <Trophy className="w-7 h-7 text-amber-400" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Problems Solved</div>
            <div className="text-3xl font-extrabold text-slate-900 mt-1">{overview.problems_solved ?? 0}</div>
            <div className="text-xs text-slate-500 mt-1">Attempted: {overview.problems_attempted ?? 0}</div>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <CheckCircle className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Submission Accuracy</div>
            <div className="text-3xl font-extrabold text-slate-900 mt-1">{overview.submission_accuracy ?? 0}%</div>
            <div className="text-xs text-slate-500 mt-1">Submissions: {overview.total_submissions ?? 0}</div>
          </div>
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <Target className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Enrolled Classes</div>
            <div className="text-3xl font-extrabold text-slate-900 mt-1">{classrooms.length}</div>
            <div className="text-xs text-slate-500 mt-1">Active membership</div>
          </div>
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
            <School className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Badges Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900">Badges</h2>
          <span className="text-xs font-semibold text-slate-500">{earnedBadgeCount} / {badges.length} earned</span>
        </div>

        {badges.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 text-center text-slate-500 text-sm">
            No badges are available right now.
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
            {badges.map((b) => (
              <div
                key={b.code}
                title={b.description}
                className={`p-4 rounded-2xl border text-center transition-colors ${
                  b.earned
                    ? 'bg-amber-50 border-amber-200 shadow-xs'
                    : 'bg-slate-50 border-slate-200 opacity-60'
                }`}
              >
                <div className="text-3xl relative inline-block">
                  <span className={b.earned ? '' : 'grayscale'}>{b.icon}</span>
                  {!b.earned && (
                    <Lock className="w-3.5 h-3.5 text-slate-400 absolute -bottom-0.5 -right-1.5 bg-white rounded-full p-0.5" />
                  )}
                </div>
                <div className={`text-xs font-semibold mt-2 ${b.earned ? 'text-amber-900' : 'text-slate-500'}`}>
                  {b.name}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {b.earned ? 'Unlocked' : b.unlock_hint}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Joined Classrooms Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900">Your Enrolled Classrooms</h2>
          <Link
            to="/student/classrooms"
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {classrooms.length === 0 ? (
          <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center">
            <School className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <h3 className="font-semibold text-slate-800">You haven't joined any classrooms yet</h3>
            <p className="text-xs text-slate-500 mt-1 mb-4">Enter a join code from your teacher to enroll in a class</p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center space-x-2 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors"
            >
              <UserPlus className="w-4 h-4" />
              <span>Join Classroom</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {classrooms.slice(0, 3).map((cls) => (
              <ClassroomCard key={cls.id} classroom={cls} isTeacher={false} />
            ))}
          </div>
        )}
      </div>

      {/* Recommended Coding Challenges */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900">Coding Challenges</h2>
          <Link
            to="/student/problems"
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
          >
            <span>Explore All Problems</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {problems.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 text-center text-slate-500 text-sm">
            No coding problems available right now.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {problems.slice(0, 3).map((prob) => (
              <ProblemCard key={prob.id} problem={prob} isTeacher={false} />
            ))}
          </div>
        )}
      </div>

      {/* Join Modal */}
      <JoinClassroomModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => fetchData()}
      />
    </div>
  );
};

export default StudentDashboard;
