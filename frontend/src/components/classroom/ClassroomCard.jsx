import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { School, Copy, Check, Trash2, ArrowRight } from 'lucide-react';

export const ClassroomCard = ({ classroom, isTeacher = false, onDelete }) => {
  const [copied, setCopied] = useState(false);

  const handleCopyCode = (e) => {
    e.stopPropagation();
    e.preventDefault();
    if (classroom.join_code) {
      navigator.clipboard.writeText(classroom.join_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const detailPath = isTeacher ? `/teacher/classrooms/${classroom.id}` : `/student/classrooms/${classroom.id}`;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-lg">
              <School className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 text-lg leading-snug">{classroom.name}</h3>
              <p className="text-xs text-slate-500">Created {new Date(classroom.created_at).toLocaleDateString()}</p>
            </div>
          </div>
          {isTeacher && onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                onDelete(classroom.id);
              }}
              className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Delete Classroom"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>

        <p className="text-slate-600 text-sm mt-3 line-clamp-2">
          {classroom.description || 'No description provided.'}
        </p>

        {isTeacher && classroom.join_code && (
          <div className="mt-4 p-2.5 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
            <div className="text-xs text-slate-500 font-medium">Join Code:</div>
            <div className="flex items-center space-x-2">
              <span className="font-mono font-bold text-slate-800 tracking-wider text-sm">{classroom.join_code}</span>
              <button
                onClick={handleCopyCode}
                className="p-1 text-slate-500 hover:text-indigo-600 transition-colors"
                title="Copy Join Code"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500">
          ID: #{classroom.id}
        </span>
        <Link
          to={detailPath}
          className="inline-flex items-center space-x-1 text-sm font-semibold text-indigo-600 hover:text-indigo-700 group"
        >
          <span>View Details</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>
    </div>
  );
};

export default ClassroomCard;
