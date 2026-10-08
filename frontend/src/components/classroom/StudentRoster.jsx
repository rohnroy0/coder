import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Search, ChevronRight } from 'lucide-react';

/**
 * Teacher roster. `roster` rows come from GET /classrooms/{id}/students
 * (rank, points, accuracy, progress). Falls back to the basic `students`
 * list if the roster could not be loaded. Clicking a row opens the
 * Student Performance Profile.
 */
export const StudentRoster = ({ classroomId, students = [], roster = null }) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');

  const rows = useMemo(() => {
    const base = roster ?? students.map((s) => ({ student_id: s.id, name: s.name, email: s.email, joined_at: s.joined_at }));
    const q = query.trim().toLowerCase();
    return q ? base.filter((r) => r.name.toLowerCase().includes(q) || r.email.toLowerCase().includes(q)) : base;
  }, [roster, students, query]);

  const total = roster ? roster.length : students.length;
  const open = (studentId) => navigate(`/teacher/classrooms/${classroomId}/students/${studentId}`);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-2">
          <Users className="w-5 h-5 text-indigo-600" />
          <h2 className="text-lg font-semibold text-slate-900">Students ({total})</h2>
        </div>
        {total > 0 && (
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search students..."
              aria-label="Search students"
              className="pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 w-56"
            />
          </div>
        )}
      </div>

      {total === 0 ? (
        <div className="text-center py-8 text-slate-500 bg-slate-50 rounded-lg border border-dashed border-slate-200">
          <p className="text-sm font-medium">No students enrolled yet.</p>
          <p className="text-xs text-slate-400 mt-1">Share the join code with your students so they can join.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-slate-700 text-xs font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Rank</th>
                <th className="px-4 py-3">Points</th>
                <th className="px-4 py-3">Accuracy</th>
                <th className="px-4 py-3">Progress</th>
                <th className="px-4 py-3 sr-only">Open</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((r) => (
                <tr
                  key={r.student_id}
                  onClick={() => open(r.student_id)}
                  onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && open(r.student_id)}
                  tabIndex={0}
                  role="link"
                  aria-label={`Open ${r.name}'s performance profile`}
                  className="hover:bg-indigo-50/60 cursor-pointer transition-colors focus:outline-none focus:bg-indigo-50"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2.5">
                      <div className="w-8 h-8 rounded-full bg-indigo-50 text-indigo-700 font-bold text-xs flex items-center justify-center shrink-0">
                        {r.name ? r.name[0].toUpperCase() : 'S'}
                      </div>
                      <div className="min-w-0">
                        <div className="font-medium text-slate-900 truncate">{r.name}</div>
                        <div className="text-xs text-slate-500 truncate">{r.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-semibold text-slate-800">{r.rank ? `#${r.rank}` : '—'}</td>
                  <td className="px-4 py-3 font-mono">{r.points ?? '—'}</td>
                  <td className="px-4 py-3">{r.accuracy != null ? `${r.accuracy}%` : '—'}</td>
                  <td className="px-4 py-3">
                    {r.progress != null ? (
                      <div className="flex items-center space-x-2">
                        <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${r.progress}%` }} />
                        </div>
                        <span className="text-xs">{r.progress}%</span>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-400">No assignments</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <ChevronRight className="w-4 h-4 text-slate-400 inline" />
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-xs text-slate-500">
                    No students match "{query}".
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default StudentRoster;
