import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Clock, Loader2, Terminal } from 'lucide-react';
import AITutorPanel from './AITutorPanel';

const STATUS_META = {
  PASSED: { label: 'Passed', color: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10', icon: CheckCircle2 },
  WRONG_ANSWER: { label: 'Wrong Answer', color: 'text-rose-400 border-rose-500/30 bg-rose-500/10', icon: XCircle },
  RUNTIME_ERROR: { label: 'Runtime Error', color: 'text-amber-400 border-amber-500/30 bg-amber-500/10', icon: AlertTriangle },
  TIME_LIMIT_EXCEEDED: { label: 'Time Limit Exceeded', color: 'text-purple-400 border-purple-500/30 bg-purple-500/10', icon: Clock },
};

export const RunResultPanel = ({ result, loading, problemId, language, sourceCode }) => {
  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-slate-300 flex items-center justify-center space-x-3">
        <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
        <span className="text-sm font-medium">Running your code against the sample test cases...</span>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-slate-400 text-xs flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-slate-500" />
          <span>Click <strong>Run</strong> to check your code against the sample test cases first.</span>
        </div>
      </div>
    );
  }

  const { results, all_passed } = result;

  if (!results || results.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-slate-400 text-xs">
        No sample test cases are available for this problem yet.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div
        className={`flex items-center space-x-2 px-3 py-2 rounded-lg border text-xs font-semibold ${
          all_passed
            ? 'bg-emerald-950/80 border-emerald-800/80 text-emerald-300'
            : 'bg-rose-950/80 border-rose-800/80 text-rose-300'
        }`}
      >
        {all_passed ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
        <span>
          {all_passed
            ? `All ${results.length} sample test case${results.length > 1 ? 's' : ''} passed`
            : `${results.filter((r) => r.passed).length} / ${results.length} sample test cases passed`}
        </span>
      </div>

      {results.map((r, i) => {
        const meta = STATUS_META[r.status] || STATUS_META.WRONG_ANSWER;
        const Icon = meta.icon;
        return (
          <div key={i} className={`border rounded-xl p-3 ${meta.color} border-opacity-40`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-200">Sample Test Case {i + 1}</span>
              <span className={`flex items-center space-x-1 px-2 py-0.5 text-[11px] font-bold rounded-full border ${meta.color}`}>
                <Icon className="w-3 h-3" />
                <span>{meta.label}</span>
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] font-mono">
              <div className="bg-slate-950 rounded-lg p-2.5">
                <div className="text-slate-500 mb-1">Input</div>
                <pre className="whitespace-pre-wrap text-slate-200">{r.input}</pre>
              </div>
              <div className="bg-slate-950 rounded-lg p-2.5">
                <div className="text-slate-500 mb-1">Expected Output</div>
                <pre className="whitespace-pre-wrap text-slate-200">{r.expected_output}</pre>
              </div>
              <div className="bg-slate-950 rounded-lg p-2.5">
                <div className="text-slate-500 mb-1">Your Output</div>
                <pre className="whitespace-pre-wrap text-slate-200">{r.actual_output ?? '(no output)'}</pre>
              </div>
            </div>

            {r.error_message && (
              <pre className="mt-2 p-2.5 bg-black/40 rounded-lg text-[11px] font-mono text-slate-200 whitespace-pre-wrap overflow-x-auto max-h-32">
                {r.error_message}
              </pre>
            )}
          </div>
        );
      })}

      {!all_passed && (
        <AITutorPanel
          runContext={{ problemId, language, sourceCode }}
          status={results.find((r) => !r.passed)?.status || 'WRONG_ANSWER'}
        />
      )}
    </div>
  );
};

export default RunResultPanel;
