import React from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  Loader2,
  Terminal,
  Zap
} from 'lucide-react';
import AITutorPanel from './AITutorPanel';

export const TestResultPanel = ({ result, loading }) => {
  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-slate-300 flex items-center justify-center space-x-3">
        <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
        <span className="text-sm font-medium">Running Python solution against test cases in Docker container...</span>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-slate-400 text-xs flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-slate-500" />
          <span>Execution results will appear here after clicking <strong>Submit Solution</strong>.</span>
        </div>
      </div>
    );
  }

  const { id, status, execution_time, failed_test_case, total_test_cases, error_message, newly_earned_badges } = result;

  const statusConfig = {
    ACCEPTED: {
      title: 'Accepted',
      message: 'Your solution passed all hidden test cases successfully!',
      bgColor: 'bg-emerald-950/80 border-emerald-800/80 text-emerald-300',
      icon: CheckCircle2,
      badgeColor: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    },
    WRONG_ANSWER: {
      title: 'Wrong Answer',
      message: 'Your solution did not produce the expected output for one or more hidden test cases.',
      bgColor: 'bg-rose-950/80 border-rose-800/80 text-rose-300',
      icon: XCircle,
      badgeColor: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
    },
    RUNTIME_ERROR: {
      title: 'Runtime Error',
      message: 'Your program encountered an error (exception/non-zero exit code) during execution.',
      bgColor: 'bg-amber-950/80 border-amber-800/80 text-amber-300',
      icon: AlertTriangle,
      badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    },
    TIME_LIMIT_EXCEEDED: {
      title: 'Time Limit Exceeded',
      message: 'Your code execution exceeded the allowed time limit (5 seconds timeout). Check for infinite loops.',
      bgColor: 'bg-purple-950/80 border-purple-800/80 text-purple-300',
      icon: Clock,
      badgeColor: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    },
  };

  const config = statusConfig[status] || {
    title: status,
    message: 'Submission processing complete.',
    bgColor: 'bg-slate-900 border-slate-800 text-slate-300',
    icon: Terminal,
    badgeColor: 'bg-slate-800 text-slate-300 border-slate-700',
  };

  const IconComponent = config.icon;

  return (
    <div className="space-y-3">
      {/* New Badge(s) Earned */}
      {newly_earned_badges && newly_earned_badges.length > 0 && (
        <div className="border border-amber-300 bg-amber-50 rounded-xl p-3 flex flex-wrap items-center gap-3">
          {newly_earned_badges.map((b) => (
            <div key={b.code} className="flex items-center space-x-2" title={b.description}>
              <span className="text-2xl">{b.icon}</span>
              <div>
                <div className="text-xs font-bold text-amber-900">Badge Earned!</div>
                <div className="text-xs text-amber-700">{b.name}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Judge Evaluation Panel */}
      <div className={`border rounded-xl p-4 transition-all ${config.bgColor}`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2.5">
            <IconComponent className="w-5 h-5 shrink-0" />
            <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full border ${config.badgeColor}`}>
              {config.title}
            </span>
          </div>

          {execution_time !== null && execution_time !== undefined && (
            <div className="flex items-center space-x-1.5 text-xs text-slate-400 font-mono">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>Execution Time: {Number(execution_time).toFixed(3)}s</span>
            </div>
          )}
        </div>

        <p className="text-xs leading-relaxed opacity-90 mt-1">{config.message}</p>

        {failed_test_case && (
          <p className="text-xs font-semibold mt-2">
            Failed on test case #{failed_test_case}
            {total_test_cases ? ` of ${total_test_cases}` : ''}
            {failed_test_case > 1 ? ` (passed the first ${failed_test_case - 1})` : ''}
          </p>
        )}

        {error_message && (
          <pre className="mt-3 p-3 bg-black/40 rounded-lg text-[11px] font-mono text-slate-200 whitespace-pre-wrap overflow-x-auto max-h-48">
            {error_message}
          </pre>
        )}
      </div>

      {/* AI Tutor Panel Integration - no hint needed once the solution is accepted */}
      {status !== 'ACCEPTED' && <AITutorPanel submissionId={id} status={status} />}
    </div>
  );
};

export default TestResultPanel;
