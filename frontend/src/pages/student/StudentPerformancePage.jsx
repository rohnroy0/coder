import React, { useState, useEffect } from 'react';
import { analyticsApi } from '../../api/analytics';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { 
  Trophy, 
  Target, 
  Zap, 
  Award, 
  TrendingUp, 
  BarChart3, 
  Brain, 
  CheckCircle2, 
  Clock, 
  AlertTriangle,
  Lightbulb
} from 'lucide-react';

export const StudentPerformancePage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const res = await analyticsApi.getMyAnalytics();
        setData(res);
      } catch (err) {
        console.error('Failed to fetch student performance analytics:', err);
        setError('Unable to load performance metrics.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) return <LoadingSpinner message="Calculating performance analytics..." fullScreen />;

  const overview = data?.overview || {};
  const topics = data?.topics || [];
  const errors = data?.error_distribution || {};
  const progress = data?.progress || [];
  const recentActivity = data?.recent_activity || [];

  const getStrengthBadge = (classification) => {
    switch (classification) {
      case 'Strong':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'Developing':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-rose-100 text-rose-800 border-rose-300';
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Personal Performance & Analytics</h1>
        <p className="text-slate-600 text-sm mt-1">
          Track your points, accuracy, topic mastery, error distributions, and learning progress
        </p>
      </div>

      <ErrorMessage message={error} onClose={() => setError('')} />

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Points */}
        <div className="bg-gradient-to-br from-indigo-900 to-slate-900 text-white p-5 rounded-2xl border border-indigo-800 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-indigo-300">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Score</span>
            <Trophy className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold">{overview.points ?? 0} <span className="text-sm font-normal text-indigo-300">pts</span></div>
          <p className="text-xs text-indigo-300">Class Rank: {overview.rank_in_classroom ? `#${overview.rank_in_classroom}` : 'N/A'}</p>
        </div>

        {/* Problems Solved */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Problems Solved</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
          </div>
          <div className="text-3xl font-extrabold text-slate-900">{overview.problems_solved ?? 0} <span className="text-sm font-normal text-slate-500">/ {overview.problems_attempted ?? 0}</span></div>
          <p className="text-xs text-slate-500">Completion: {overview.problem_completion_rate ?? 0}%</p>
        </div>

        {/* Submission Accuracy */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Submission Accuracy</span>
            <Target className="w-5 h-5 text-indigo-600" />
          </div>
          <div className="text-3xl font-extrabold text-slate-900">{overview.submission_accuracy ?? 0}%</div>
          <p className="text-xs text-slate-500">Avg attempts/solved: {overview.avg_attempts_per_solved ?? 0}</p>
        </div>

        {/* AI Hints Requested */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">AI Hints Used</span>
            <Lightbulb className="w-5 h-5 text-amber-500" />
          </div>
          <div className="text-3xl font-extrabold text-slate-900">{overview.ai_hints_requested ?? 0}</div>
          <p className="text-xs text-slate-500">Avg Exec Time: {overview.avg_execution_time ?? 0}s</p>
        </div>
      </div>

      {/* Main Grid: Topic Strengths & Error Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Topic Strengths (7 cols) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-bold text-slate-900">Topic Performance & Mastery</h2>
          </div>

          {topics.length === 0 ? (
            <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-500 text-sm">
              No coding activity recorded yet. Submit solutions to see topic mastery ratings!
            </div>
          ) : (
            <div className="space-y-4">
              {topics.map((t, idx) => (
                <div key={idx} className="space-y-1.5 p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-bold text-slate-800">{t.topic}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-slate-500 font-mono">{t.solved} / {t.attempted} solved • {t.accuracy}% accuracy</span>
                      <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full border ${getStrengthBadge(t.classification)}`}>
                        {t.classification}
                      </span>
                    </div>
                  </div>
                  {/* Progress bar */}
                  <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all rounded-full ${
                        t.accuracy >= 80 ? 'bg-emerald-500' : t.accuracy >= 50 ? 'bg-amber-500' : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.max(t.accuracy, 5)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Error Category Breakdown (5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center space-x-2">
            <Brain className="w-5 h-5 text-amber-500" />
            <h2 className="text-lg font-bold text-slate-900">Common Error Analysis</h2>
          </div>

          {Object.keys(errors).length === 0 ? (
            <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-500 text-sm">
              No AI feedback error distributions recorded yet.
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(errors).map(([errType, count], i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs">
                  <span className="font-semibold text-slate-700 font-mono">{errType}</span>
                  <span className="px-3 py-1 bg-amber-100 text-amber-900 font-bold rounded-full border border-amber-200">
                    {count} occurrence(s)
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Points History & Progress Timeline */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-5 h-5 text-indigo-600" />
          <h2 className="text-lg font-bold text-slate-900">Score & Points Event Log</h2>
        </div>

        {progress.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-sm">
            No scoring events logged yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Event Type</th>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Points Delta</th>
                  <th className="px-4 py-3">Accumulated Total</th>
                  <th className="px-4 py-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {progress.map((pe) => (
                  <tr key={pe.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono font-semibold text-slate-800">{pe.event_type}</td>
                    <td className="px-4 py-3 text-slate-600">{pe.description}</td>
                    <td className={`px-4 py-3 font-bold ${pe.points >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {pe.points >= 0 ? `+${pe.points}` : pe.points}
                    </td>
                    <td className="px-4 py-3 font-extrabold text-slate-900">{pe.total_points} pts</td>
                    <td className="px-4 py-3 text-slate-500">{new Date(pe.created_at).toLocaleString()}</td>
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

export default StudentPerformancePage;
