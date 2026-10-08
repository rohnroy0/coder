import React, { useState } from 'react';
import { History, Calendar, Clock, Code, X } from 'lucide-react';

export const SubmissionHistory = ({ submissions = [], loading = false }) => {
  const [selectedSubmission, setSelectedSubmission] = useState(null);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'ACCEPTED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'WRONG_ANSWER':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'RUNTIME_ERROR':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'TIME_LIMIT_EXCEEDED':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
      <div className="flex items-center space-x-2 mb-4">
        <History className="w-5 h-5 text-indigo-600" />
        <h2 className="text-lg font-semibold text-slate-900">Submission History ({submissions.length})</h2>
      </div>

      {loading ? (
        <div className="text-center py-8 text-slate-500 text-sm">Loading submissions...</div>
      ) : submissions.length === 0 ? (
        <div className="text-center py-8 text-slate-500 bg-slate-50 rounded-lg border border-dashed border-slate-200 text-sm">
          No code submissions recorded yet.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-slate-700 text-xs font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Problem</th>
                <th className="px-4 py-3">Language</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Execution Time</th>
                <th className="px-4 py-3">Submitted At</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {submissions.map((sub) => (
                <tr key={sub.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-4 py-3.5 font-medium text-slate-900">{sub.problem}</td>
                  <td className="px-4 py-3.5 font-mono text-xs text-slate-600 uppercase">{sub.language}</td>
                  <td className="px-4 py-3.5">
                    <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${getStatusBadge(sub.status)}`}>
                      {sub.status}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-xs font-mono text-slate-500">
                    {sub.execution_time != null ? `${Number(sub.execution_time).toFixed(3)}s` : 'N/A'}
                  </td>
                  <td className="px-4 py-3.5 text-xs text-slate-500">
                    {new Date(sub.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    {sub.source_code && (
                      <button
                        onClick={() => setSelectedSubmission(sub)}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold inline-flex items-center space-x-1"
                      >
                        <Code className="w-3.5 h-3.5" />
                        <span>Inspect Code</span>
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Code Modal */}
      {selectedSubmission && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-slate-950 rounded-2xl max-w-2xl w-full p-6 text-slate-100 shadow-xl border border-slate-800 relative">
            <button
              onClick={() => setSelectedSubmission(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-lg font-bold mb-1 text-slate-100">{selectedSubmission.problem}</h3>
            <div className="flex items-center space-x-3 text-xs text-slate-400 mb-4">
              <span>Language: {selectedSubmission.language}</span>
              <span>•</span>
              <span>Submitted: {new Date(selectedSubmission.created_at).toLocaleString()}</span>
            </div>

            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 overflow-x-auto max-h-96">
              <pre className="font-mono text-xs text-slate-300 whitespace-pre-wrap">{selectedSubmission.source_code}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubmissionHistory;
