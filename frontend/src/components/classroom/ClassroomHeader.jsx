import React, { useState } from 'react';
import { School, Copy, Check, Users, Calendar, ClipboardX } from 'lucide-react';

export const ClassroomHeader = ({
  classroom,
  studentCount = 0,
  isTeacher = false,
  onTogglePasteDisabled,
  pasteToggleLoading = false,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopyCode = () => {
    if (classroom?.join_code) {
      navigator.clipboard.writeText(classroom.join_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!classroom) return null;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start space-x-4">
          <div className="p-3.5 bg-indigo-100 text-indigo-600 rounded-xl">
            <School className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{classroom.name}</h1>
            <p className="text-slate-600 text-sm mt-1">{classroom.description || 'No description provided.'}</p>
            
            <div className="flex items-center space-x-4 mt-3 text-xs text-slate-500">
              <span className="flex items-center space-x-1">
                <Calendar className="w-3.5 h-3.5" />
                <span>Created {new Date(classroom.created_at).toLocaleDateString()}</span>
              </span>
              <span className="flex items-center space-x-1">
                <Users className="w-3.5 h-3.5" />
                <span>{studentCount} Enrolled Students</span>
              </span>
            </div>
          </div>
        </div>

        {isTeacher && classroom.join_code && (
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 self-start md:self-auto">
            <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl flex items-center space-x-3">
              <div>
                <div className="text-xs text-slate-500 font-medium">Classroom Join Code</div>
                <div className="font-mono font-bold text-slate-900 text-lg tracking-wider">{classroom.join_code}</div>
              </div>
              <button
                onClick={handleCopyCode}
                className="p-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-100 text-slate-600 hover:text-indigo-600 transition-colors flex items-center space-x-1 text-xs font-medium"
                title="Copy Join Code"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-600" />
                    <span className="text-emerald-600 font-semibold">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>

            {onTogglePasteDisabled && (
              <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl flex items-center space-x-3">
                <div className="p-2 bg-white border border-slate-200 rounded-lg text-slate-500">
                  <ClipboardX className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs text-slate-500 font-medium">Paste in Code Editor</div>
                  <div className={`font-bold text-sm ${classroom.disable_paste ? 'text-rose-600' : 'text-emerald-600'}`}>
                    {classroom.disable_paste ? 'Disabled for students' : 'Allowed'}
                  </div>
                </div>
                <button
                  onClick={onTogglePasteDisabled}
                  disabled={pasteToggleLoading}
                  role="switch"
                  aria-checked={classroom.disable_paste}
                  aria-label="Toggle whether students can paste into the code editor"
                  title={classroom.disable_paste ? 'Click to allow pasting again' : 'Click to block pasting for students'}
                  className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors disabled:opacity-50 ${
                    classroom.disable_paste ? 'bg-rose-500' : 'bg-slate-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                      classroom.disable_paste ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ClassroomHeader;
