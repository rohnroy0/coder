import React from 'react';
import { Link } from 'react-router-dom';
import DifficultyBadge from './DifficultyBadge';
import { Code2, FileCode2, ArrowRight, Trash2, CheckCircle2 } from 'lucide-react';

export const ProblemCard = ({ problem, isTeacher = false, onDelete }) => {
  const detailPath = isTeacher
    ? `/teacher/problems/${problem.id}`
    : `/student/problems/${problem.id}/code`;
  const isSolved = !isTeacher && problem.solved;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-lg">
              <Code2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-semibold text-slate-900 text-lg leading-snug">{problem.title}</h3>
                {isSolved && (
                  <span
                    className="inline-flex items-center space-x-1 px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full text-[10px] font-bold shrink-0"
                    title="You've already solved this problem - you can solve it again if you'd like."
                  >
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Solved</span>
                  </span>
                )}
              </div>
              <div className="mt-1 flex items-center space-x-2">
                <DifficultyBadge difficulty={problem.difficulty} />
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs font-semibold text-slate-600 uppercase font-mono">
                  {problem.language || 'python'}
                </span>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs text-slate-500 font-medium">
                  {problem.test_case_count ?? 0} Test Cases
                </span>
              </div>
            </div>
          </div>

          {isTeacher && onDelete && (
            <button
              onClick={(e) => {
                e.preventDefault();
                onDelete(problem.id);
              }}
              className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Delete Problem"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>

        <p className="text-slate-600 text-sm mt-3 line-clamp-2">
          {problem.description}
        </p>
      </div>

      <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400">Problem #{problem.id}</span>
        <Link
          to={detailPath}
          className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors shadow-xs"
        >
          <FileCode2 className="w-3.5 h-3.5" />
          <span>{isTeacher ? 'Manage Problem' : isSolved ? 'Solve Again' : 'Solve Challenge'}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};

export default ProblemCard;
