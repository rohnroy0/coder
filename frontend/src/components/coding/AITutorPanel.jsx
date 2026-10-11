import React, { useState } from 'react';
import { 
  Sparkles, 
  Lightbulb, 
  HelpCircle, 
  ArrowRight, 
  Loader2, 
  AlertCircle,
  ShieldAlert,
  Bot
} from 'lucide-react';
import { submissionsApi } from '../../api/submissions';

export const AITutorPanel = ({ submissionId, runContext, status }) => {
  const [feedback, setFeedback] = useState(null);
  const [hintLevel, setHintLevel] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // A correct solution needs no hint - the backend also enforces this, this
  // just avoids offering a button that would error if clicked.
  if (status === 'ACCEPTED') {
    return null;
  }

  const fetchFeedback = async (level) => {
    if (!submissionId && !runContext) return;
    setLoading(true);
    setError('');

    try {
      const data = submissionId
        ? await submissionsApi.getFeedback(submissionId, level)
        : await submissionsApi.getRunFeedback({ ...runContext, status, hintLevel: level });
      setFeedback(data);
      setHintLevel(level);
    } catch (err) {
      console.error('Failed to fetch AI tutor feedback:', err);
      const detail = err.response?.data?.detail || 'AI Tutor is currently unavailable. Please try again later.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  const getErrorBadgeClass = (type) => {
    switch (type) {
      case 'LOGIC_ERROR':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'SYNTAX_ERROR':
      case 'RUNTIME_ERROR':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      case 'TIME_COMPLEXITY':
      case 'ALGORITHM_ERROR':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'EDGE_CASE':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      default:
        return 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30';
    }
  };

  return (
    <div className="mt-3 border border-indigo-900/60 rounded-xl bg-slate-900/90 p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 text-indigo-400">
          <Bot className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-bold text-slate-100">AI Coding Tutor</h3>
        </div>

        {!feedback && !loading && (
          <button
            onClick={() => fetchFeedback(1)}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Get AI Hint</span>
          </button>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 flex items-center justify-center space-x-3 text-slate-300 text-xs">
          <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
          <span>AI Tutor is analyzing your code and generating Socratic feedback...</span>
        </div>
      )}

      {/* Error / Fallback State */}
      {error && !loading && (
        <div className="p-3 bg-amber-950/60 border border-amber-800/60 rounded-lg text-amber-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => fetchFeedback(hintLevel)}
            className="text-xs font-semibold underline text-amber-200 hover:text-white"
          >
            Retry
          </button>
        </div>
      )}

      {/* AI Feedback View */}
      {feedback && !loading && (
        <div className="space-y-3 pt-1">
          {/* Top Summary & Badge */}
          <div className="flex items-center justify-between bg-slate-950/80 p-2.5 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-300 font-medium">{feedback.feedback.summary}</span>
            <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full border ${getErrorBadgeClass(feedback.feedback.error_type)}`}>
              {feedback.feedback.error_type}
            </span>
          </div>

          {/* Explanation */}
          <div className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800/60 space-y-1">
            <div className="flex items-center space-x-1.5 text-indigo-400 font-semibold mb-1">
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Explanation:</span>
            </div>
            <p className="whitespace-pre-line text-slate-300">{feedback.feedback.explanation}</p>
          </div>

          {/* Hint Card */}
          <div className="text-xs bg-indigo-950/40 border border-indigo-800/50 p-3 rounded-lg space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5 text-amber-300 font-bold">
                <Lightbulb className="w-4 h-4 text-amber-400" />
                <span>💡 Hint (Level {feedback.hint_level} of 3)</span>
              </div>
              <span className="text-[10px] text-indigo-300 font-mono">
                {feedback.hint_level === 1 && 'Conceptual'}
                {feedback.hint_level === 2 && 'Directional'}
                {feedback.hint_level === 3 && 'Targeted Guidance'}
              </span>
            </div>
            <p className="text-slate-200 leading-relaxed font-medium">{feedback.feedback.hint}</p>
          </div>

          {/* Actionable Next Step */}
          <div className="text-xs bg-slate-950/60 border border-slate-800 p-2.5 rounded-lg flex items-start space-x-2 text-slate-300">
            <ArrowRight className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-200">Next Step: </span>
              <span>{feedback.feedback.next_step}</span>
            </div>
          </div>

          {/* Progressive Hint Progression Buttons */}
          <div className="flex items-center justify-between pt-1">
            <span className="text-[10px] text-slate-500">
              Socratic guidance • Direct code fixes are intentionally omitted
            </span>

            {feedback.hint_level < 3 ? (
              <button
                onClick={() => fetchFeedback(feedback.hint_level + 1)}
                className="flex items-center space-x-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors border border-slate-700"
              >
                <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                <span>Show Stronger Hint (Level {feedback.hint_level + 1})</span>
              </button>
            ) : (
              <span className="text-xs text-amber-400 font-semibold px-2 py-0.5 bg-amber-950/40 border border-amber-800/40 rounded-md">
                Level 3 Max Hint Active
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AITutorPanel;
