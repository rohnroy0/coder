import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft, Mail, School, CalendarDays, Trophy, Star, CheckCircle2, Target, Percent, Gauge,
  Repeat, Timer, ClipboardCheck, Lightbulb, AlertTriangle, XCircle, UserPlus, PlayCircle,
  Award, Code2, X, ChevronDown, ChevronRight, Info, FileText,
} from 'lucide-react';
import { classroomsApi } from '../../api/classrooms';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import DifficultyBadge from '../../components/problems/DifficultyBadge';
import TrendChart from '../../components/profile/TrendChart';

// ─── Helpers ────────────────────────────────────────────────────────────────

// Backend timestamps are naive UTC (no "Z"); parse them as UTC.
const parseUtc = (s) => (s ? new Date(/[zZ]|[+-]\d\d:\d\d$/.test(s) ? s : `${s}Z`) : null);
const fmtDate = (s) => (s ? parseUtc(s).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }) : '—');
const fmtDateTime = (s) => (s ? parseUtc(s).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '—');
const fmtSecs = (v) => (v != null ? `${Number(v).toFixed(3)}s` : '—');
const label = (s) => (s ? s.replace(/_/g, ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase()) : '—');

const timeAgo = (s) => {
  const secs = Math.round((Date.now() - parseUtc(s).getTime()) / 1000);
  if (secs < 60) return 'just now';
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins} minute${mins === 1 ? '' : 's'} ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs} hour${hrs === 1 ? '' : 's'} ago`;
  const days = Math.round(hrs / 24);
  if (days === 1) return 'Yesterday';
  if (days < 30) return `${days} days ago`;
  return fmtDate(s);
};

const RESULT_STYLES = {
  ACCEPTED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  WRONG_ANSWER: 'bg-rose-50 text-rose-700 border-rose-200',
  RUNTIME_ERROR: 'bg-amber-50 text-amber-700 border-amber-200',
  TIME_LIMIT_EXCEEDED: 'bg-purple-50 text-purple-700 border-purple-200',
  COMPLETED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  IN_PROGRESS: 'bg-sky-50 text-sky-700 border-sky-200',
  NOT_STARTED: 'bg-slate-50 text-slate-600 border-slate-200',
  Solved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Attempted: 'bg-amber-50 text-amber-700 border-amber-200',
};

const Badge = ({ value }) => (
  <span className={`inline-block px-2 py-0.5 text-[11px] font-semibold rounded-full border whitespace-nowrap ${RESULT_STYLES[value] || 'bg-slate-50 text-slate-600 border-slate-200'}`}>
    {label(value)}
  </span>
);

const MASTERY_STYLES = {
  Strong: { bar: 'bg-emerald-500', chip: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  Developing: { bar: 'bg-amber-500', chip: 'bg-amber-50 text-amber-700 border-amber-200' },
  'Needs Practice': { bar: 'bg-rose-500', chip: 'bg-rose-50 text-rose-700 border-rose-200' },
};

const Card = ({ title, icon: Icon, children, className = '' }) => (
  <section className={`bg-white rounded-xl border border-slate-200 p-5 shadow-xs ${className}`}>
    {title && (
      <h3 className="flex items-center space-x-2 text-sm font-bold text-slate-900 mb-4">
        {Icon && <Icon className="w-4 h-4 text-indigo-600" />}
        <span>{title}</span>
      </h3>
    )}
    {children}
  </section>
);

const Stat = ({ icon: Icon, label: text, value, sub }) => (
  <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
    <div className="flex items-center justify-between text-slate-500">
      <span className="text-[11px] font-semibold uppercase tracking-wider">{text}</span>
      <Icon className="w-4 h-4 text-indigo-500" />
    </div>
    <div className="text-2xl font-extrabold text-slate-900 mt-1.5">{value}</div>
    {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
  </div>
);

const Empty = ({ children }) => <p className="text-xs text-slate-500 text-center py-6">{children}</p>;

const Table = ({ head, children }) => (
  <div className="overflow-x-auto -mx-5 px-5">
    <table className="w-full text-left text-xs">
      <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
        <tr>{head.map((h) => <th key={h} className="px-3 py-2.5 whitespace-nowrap">{h}</th>)}</tr>
      </thead>
      <tbody className="divide-y divide-slate-100">{children}</tbody>
    </table>
  </div>
);

const CountBars = ({ items, total, color = 'bg-indigo-500', format = label }) => (
  <div className="space-y-2.5">
    {items.map((it) => (
      <div key={it.name}>
        <div className="flex justify-between text-xs mb-1">
          <span className="font-medium text-slate-700">{format(it.name)}</span>
          <span className="text-slate-500">{it.count}{total ? ` (${Math.round((it.count / total) * 100)}%)` : ''}</span>
        </div>
        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div className={`h-full ${color} rounded-full`} style={{ width: `${total ? (it.count / total) * 100 : 0}%` }} />
        </div>
      </div>
    ))}
  </div>
);

const ACTIVITY_ICONS = {
  JOINED: { icon: UserPlus, color: 'text-indigo-600 bg-indigo-50' },
  ACCEPTED: { icon: CheckCircle2, color: 'text-emerald-600 bg-emerald-50' },
  WRONG_ANSWER: { icon: XCircle, color: 'text-rose-600 bg-rose-50' },
  RUNTIME_ERROR: { icon: AlertTriangle, color: 'text-amber-600 bg-amber-50' },
  TIME_LIMIT_EXCEEDED: { icon: Timer, color: 'text-purple-600 bg-purple-50' },
  HINT: { icon: Lightbulb, color: 'text-yellow-600 bg-yellow-50' },
  ASSIGNMENT_STARTED: { icon: PlayCircle, color: 'text-sky-600 bg-sky-50' },
  ASSIGNMENT_COMPLETED: { icon: Award, color: 'text-emerald-600 bg-emerald-50' },
};

const TABS = [
  { key: 'overview', label: 'Overview' },
  { key: 'assignments', label: 'Assignments' },
  { key: 'problems', label: 'Problems' },
  { key: 'submissions', label: 'Submissions' },
  { key: 'ai', label: 'AI Tutor & Errors' },
  { key: 'analytics', label: 'Analytics' },
];

// ─── Sections ───────────────────────────────────────────────────────────────

const Header = ({ h }) => (
  <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-wrap items-center justify-between gap-6">
    <div className="flex items-center space-x-4 min-w-0">
      <div className="w-14 h-14 rounded-2xl bg-indigo-600 text-white text-xl font-extrabold flex items-center justify-center shrink-0">
        {h.name?.[0]?.toUpperCase() || 'S'}
      </div>
      <div className="min-w-0 space-y-1">
        <h1 className="text-2xl font-extrabold text-slate-900 truncate">{h.name}</h1>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
          <span className="flex items-center space-x-1"><Mail className="w-3.5 h-3.5" /><span>{h.email}</span></span>
          <span className="flex items-center space-x-1"><School className="w-3.5 h-3.5" /><span>{h.classroom_name}</span></span>
          <span className="flex items-center space-x-1"><CalendarDays className="w-3.5 h-3.5" /><span>Joined {fmtDate(h.joined_at)}</span></span>
        </div>
      </div>
    </div>
    <div className="flex gap-3">
      <div className="px-5 py-3 rounded-xl bg-indigo-50 border border-indigo-100 text-center">
        <div className="text-[11px] font-semibold text-indigo-700 uppercase">Class Rank</div>
        <div className="text-2xl font-extrabold text-indigo-700">
          {h.rank ? `#${h.rank}` : '—'}<span className="text-sm font-semibold text-indigo-400"> / {h.total_students}</span>
        </div>
      </div>
      <div className="px-5 py-3 rounded-xl bg-amber-50 border border-amber-100 text-center">
        <div className="text-[11px] font-semibold text-amber-700 uppercase">Total Points</div>
        <div className="text-2xl font-extrabold text-amber-700">{h.total_points}</div>
      </div>
    </div>
  </div>
);

const TopicList = ({ title, topics, tone }) => (
  <div>
    <div className="text-[11px] font-semibold uppercase text-slate-500 mb-1">{title}</div>
    {topics.length ? (
      <div className="flex flex-wrap gap-1.5">
        {topics.map((t) => <span key={t} className={`px-2 py-0.5 rounded-full border text-xs font-medium ${tone}`}>{t}</span>)}
      </div>
    ) : <span className="text-xs text-slate-400">None</span>}
  </div>
);

const OverviewTab = ({ p }) => {
  const o = p.overall;
  const lb = p.leaderboard;
  return (
    <div className="space-y-6">
      <Card title="Performance Summary" icon={FileText}>
        <div className="grid md:grid-cols-2 gap-6">
          <ul className="space-y-1.5 text-sm text-slate-700 list-disc pl-5">
            {p.summary.lines.map((line) => <li key={line}>{line}</li>)}
          </ul>
          <div className="space-y-3">
            <TopicList title="Strong topics" topics={p.summary.strong_topics} tone={MASTERY_STYLES.Strong.chip} />
            <TopicList title="Developing" topics={p.summary.developing_topics} tone={MASTERY_STYLES.Developing.chip} />
            <TopicList title="Needs practice" topics={p.summary.needs_practice_topics} tone={MASTERY_STYLES['Needs Practice'].chip} />
          </div>
        </div>
        <p className="text-[11px] text-slate-400 mt-4">Generated directly from recorded submissions, points and AI tutor usage.</p>
      </Card>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat icon={Star} label="Total Points" value={o.total_points} />
        <Stat icon={CheckCircle2} label="Problems Solved" value={o.problems_solved} />
        <Stat icon={Target} label="Problems Attempted" value={o.problems_attempted} />
        <Stat icon={Percent} label="Submission Accuracy" value={`${o.submission_accuracy}%`} sub={`${o.total_submissions} submissions`} />
        <Stat icon={Gauge} label="Completion Rate" value={`${o.completion_rate}%`} sub="solved / attempted" />
        <Stat icon={Repeat} label="Average Attempts" value={o.avg_attempts} sub="per solved problem" />
        <Stat icon={Timer} label="Avg Execution Time" value={fmtSecs(o.avg_execution_time)} />
        <Stat icon={ClipboardCheck} label="Assignments Completed" value={`${o.assignments_completed} / ${o.assignments_total}`} />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card title="Leaderboard" icon={Trophy}>
          <div className="text-center py-2">
            <div className="text-4xl font-extrabold text-indigo-600">{lb.rank ? `#${lb.rank}` : '—'}</div>
            <div className="text-xs text-slate-500">of {lb.total_students} students</div>
          </div>
          <dl className="grid grid-cols-3 gap-2 mt-4 text-center">
            <div><dt className="text-[11px] text-slate-500 uppercase">Points</dt><dd className="font-bold text-slate-900">{lb.points}</dd></div>
            <div><dt className="text-[11px] text-slate-500 uppercase">Solved</dt><dd className="font-bold text-slate-900">{lb.problems_solved}</dd></div>
            <div><dt className="text-[11px] text-slate-500 uppercase">Accuracy</dt><dd className="font-bold text-slate-900">{lb.accuracy}%</dd></div>
          </dl>
        </Card>

        <Card title="Recent Activity" icon={CalendarDays} className="lg:col-span-2">
          {p.recent_activity.length === 0 ? <Empty>No activity yet.</Empty> : (
            <ul className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {p.recent_activity.map((a, i) => {
                const cfg = ACTIVITY_ICONS[a.type] || ACTIVITY_ICONS.JOINED;
                const Icon = cfg.icon;
                return (
                  <li key={i} className="flex items-start space-x-3">
                    <span className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${cfg.color}`}><Icon className="w-4 h-4" /></span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-slate-800">{a.description}</div>
                      <div className="text-[11px] text-slate-400" title={fmtDateTime(a.created_at)}>{timeAgo(a.created_at)}</div>
                    </div>
                    {a.points != null && (
                      <span className={`text-xs font-bold ${a.points >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {a.points > 0 ? '+' : ''}{a.points} pts
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
};

const AssignmentsTab = ({ p }) => {
  const [open, setOpen] = useState(null);
  if (p.assignments.length === 0) return <Card><Empty>This classroom has no assignments yet.</Empty></Card>;
  return (
    <Card title="Assignment Performance" icon={ClipboardCheck}>
      <Table head={['', 'Assignment', 'Status', 'Problems', 'Score', '%', 'Attempts', 'Deadline', 'Completed', 'Last Activity']}>
        {p.assignments.map((a) => (
          <React.Fragment key={a.assignment_id}>
            <tr className="hover:bg-slate-50 cursor-pointer" onClick={() => setOpen(open === a.assignment_id ? null : a.assignment_id)}>
              <td className="pl-3 py-3 text-slate-400">
                {open === a.assignment_id ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </td>
              <td className="px-3 py-3">
                <div className="font-semibold text-slate-900">{a.title}</div>
                {a.assignment_status === 'DRAFT' && <div className="text-[10px] text-slate-400">Draft (not visible to students)</div>}
              </td>
              <td className="px-3 py-3"><Badge value={a.progress_status} /></td>
              <td className="px-3 py-3">{a.completed_problems} / {a.total_problems}</td>
              <td className="px-3 py-3 font-mono">{a.score} / {a.max_score}</td>
              <td className="px-3 py-3 font-semibold">{a.percentage}%</td>
              <td className="px-3 py-3">{a.attempts}</td>
              <td className="px-3 py-3 whitespace-nowrap">{a.due_at ? fmtDateTime(a.due_at) : 'No deadline'}</td>
              <td className="px-3 py-3 whitespace-nowrap">{fmtDateTime(a.completed_at)}</td>
              <td className="px-3 py-3 whitespace-nowrap">{fmtDateTime(a.last_activity_at)}</td>
            </tr>
            {open === a.assignment_id && (
              <tr className="bg-slate-50/70">
                <td />
                <td colSpan={9} className="px-3 py-3">
                  <div className="space-y-2">
                    {a.problems.map((ap) => (
                      <div key={ap.problem_id} className="flex flex-wrap items-center gap-3 bg-white border border-slate-200 rounded-lg px-3 py-2">
                        <span className="font-medium text-slate-800 flex-1 min-w-40">{ap.title}</span>
                        <span className="text-slate-500">{ap.points} pts</span>
                        <span className="text-slate-500">{ap.attempts} attempt{ap.attempts === 1 ? '' : 's'}</span>
                        {ap.best_result ? <Badge value={ap.best_result} /> : <Badge value="NOT_STARTED" />}
                      </div>
                    ))}
                    <Link to={`/teacher/assignments/${a.assignment_id}`} className="inline-block text-xs font-semibold text-indigo-600 hover:underline mt-1">
                      Open assignment (whole class progress) →
                    </Link>
                  </div>
                </td>
              </tr>
            )}
          </React.Fragment>
        ))}
      </Table>
    </Card>
  );
};

const ProblemsTab = ({ p }) => (
  <Card title="Coding Problem Performance" icon={Code2}>
    {p.problems.length === 0 ? <Empty>No problems attempted yet.</Empty> : (
      <Table head={['Problem', 'Topic', 'Difficulty', 'Assignment', 'Attempts', 'First', 'Latest', 'Best', 'Best Time', 'Last Submission', 'Hints', 'Status']}>
        {p.problems.map((r) => (
          <tr key={r.problem_id} className="hover:bg-slate-50">
            <td className="px-3 py-3 font-semibold text-slate-900">{r.title}</td>
            <td className="px-3 py-3">{r.topic}</td>
            <td className="px-3 py-3"><DifficultyBadge difficulty={r.difficulty} /></td>
            <td className="px-3 py-3">{r.assignments.length ? r.assignments.join(', ') : <span className="text-slate-400">Practice</span>}</td>
            <td className="px-3 py-3 font-semibold">{r.attempts}</td>
            <td className="px-3 py-3"><Badge value={r.first_result} /></td>
            <td className="px-3 py-3"><Badge value={r.latest_result} /></td>
            <td className="px-3 py-3"><Badge value={r.best_result} /></td>
            <td className="px-3 py-3 font-mono">{fmtSecs(r.best_execution_time)}</td>
            <td className="px-3 py-3 whitespace-nowrap">{fmtDateTime(r.last_submission_at)}</td>
            <td className="px-3 py-3">{r.hints_requested}</td>
            <td className="px-3 py-3"><Badge value={r.completion_status} /></td>
          </tr>
        ))}
      </Table>
    )}
  </Card>
);

const CodeModal = ({ classroomId, studentId, submissionId, onClose }) => {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    classroomsApi.getStudentSubmission(classroomId, studentId, submissionId)
      .then(setData)
      .catch((e) => setError(e.response?.data?.detail || 'Unable to load submission.'));
  }, [classroomId, studentId, submissionId]);
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-label="Submitted code" className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between p-5 border-b border-slate-100">
          <div>
            <h3 className="font-bold text-slate-900">{data ? `${data.problem} — Attempt #${data.attempt_number}` : 'Submission'}</h3>
            {data && (
              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mt-1">
                <Badge value={data.result} />
                <span>{fmtDateTime(data.created_at)}</span>
                <span>• {data.language}</span>
                <span>• {fmtSecs(data.execution_time)}</span>
                {data.assignment && <span>• {data.assignment}</span>}
              </div>
            )}
          </div>
          <button onClick={onClose} aria-label="Close" className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-5 overflow-auto">
          {error && <ErrorMessage message={error} />}
          {!data && !error && <LoadingSpinner message="Loading code..." />}
          {data && (
            <pre className="bg-slate-900 text-slate-100 text-xs font-mono p-4 rounded-xl overflow-x-auto whitespace-pre">{data.source_code}</pre>
          )}
          <p className="text-[11px] text-slate-400 mt-3">Read-only view. Hidden test cases and reference solutions are never shown.</p>
        </div>
      </div>
    </div>
  );
};

const SubmissionsTab = ({ p, classroomId, studentId }) => {
  const [viewing, setViewing] = useState(null);
  return (
    <Card title={`Submission History (${p.submissions.length})`} icon={FileText}>
      {p.submissions.length === 0 ? <Empty>No submissions yet.</Empty> : (
        <Table head={['Timestamp', 'Problem', 'Assignment', 'Language', 'Result', 'Exec Time', 'Memory', 'Attempt', 'Code']}>
          {p.submissions.map((s) => (
            <tr key={s.submission_id} className="hover:bg-slate-50">
              <td className="px-3 py-2.5 whitespace-nowrap">{fmtDateTime(s.created_at)}</td>
              <td className="px-3 py-2.5 font-semibold text-slate-900">{s.problem}</td>
              <td className="px-3 py-2.5">{s.assignment || <span className="text-slate-400">—</span>}</td>
              <td className="px-3 py-2.5 capitalize">{s.language}</td>
              <td className="px-3 py-2.5"><Badge value={s.result} /></td>
              <td className="px-3 py-2.5 font-mono">{fmtSecs(s.execution_time)}</td>
              <td className="px-3 py-2.5 text-slate-400" title="Memory usage is not measured by the sandbox">N/A</td>
              <td className="px-3 py-2.5">#{s.attempt_number}</td>
              <td className="px-3 py-2.5">
                <button onClick={() => setViewing(s.submission_id)} className="text-indigo-600 font-semibold hover:underline whitespace-nowrap">
                  View Submission
                </button>
              </td>
            </tr>
          ))}
        </Table>
      )}
      {viewing && (
        <CodeModal classroomId={classroomId} studentId={studentId} submissionId={viewing} onClose={() => setViewing(null)} />
      )}
    </Card>
  );
};

const AITab = ({ p }) => {
  const ai = p.ai_tutor;
  const err = p.errors;
  const judgeTotal = err.judge_outcomes.reduce((n, j) => n + j.count, 0);
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat icon={Lightbulb} label="Total Hints" value={ai.total_hints} />
        <Stat icon={AlertTriangle} label="Most Common Issue" value={<span className="text-lg">{ai.most_common_error ? label(ai.most_common_error) : '—'}</span>} />
        <Stat icon={Code2} label="Problems Needing Help" value={ai.hints_by_problem.length} />
        <Stat icon={XCircle} label="Failed Submissions" value={judgeTotal} />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card title="Feedback Categories" icon={Lightbulb}>
          {ai.categories.length ? <CountBars items={ai.categories} total={ai.total_hints} color="bg-yellow-500" /> : <Empty>No AI hints requested yet.</Empty>}
        </Card>
        <Card title="Problems Requiring Most Assistance" icon={Code2}>
          {ai.hints_by_problem.length ? (
            <ul className="divide-y divide-slate-100">
              {ai.hints_by_problem.map((h) => (
                <li key={h.name} className="flex justify-between py-2 text-sm">
                  <span className="text-slate-800">{h.name}</span>
                  <span className="font-semibold text-slate-600">{h.count} hint{h.count === 1 ? '' : 's'}</span>
                </li>
              ))}
            </ul>
          ) : <Empty>No AI hints requested yet.</Empty>}
        </Card>
      </div>

      <Card title="Hint Progression" icon={Repeat}>
        {ai.progression.length ? (
          <div className="space-y-2">
            {ai.progression.map((pr) => (
              <div key={pr.problem} className="flex flex-wrap items-center gap-3 text-sm">
                <span className="font-medium text-slate-800 w-48 truncate">{pr.problem}</span>
                <div className="flex items-center gap-1">
                  {pr.levels.map((lv, i) => (
                    <span key={i} title={`Hint level ${lv}`} className={`w-6 h-6 rounded-md text-[11px] font-bold flex items-center justify-center ${lv === 1 ? 'bg-yellow-100 text-yellow-800' : lv === 2 ? 'bg-orange-100 text-orange-800' : 'bg-rose-100 text-rose-800'}`}>
                      L{lv}
                    </span>
                  ))}
                </div>
                <span className="text-xs text-slate-500">max level {pr.max_level}</span>
              </div>
            ))}
            <p className="text-[11px] text-slate-400 pt-1">L1 conceptual → L2 directional → L3 specific. Hint text is private to the student and not shown.</p>
          </div>
        ) : <Empty>No AI hints requested yet.</Empty>}
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card title="Error Distribution (AI tutor classification)" icon={AlertTriangle}>
          {err.ai_categories.length ? (
            <div className="space-y-3">
              {err.ai_categories.map((c) => (
                <div key={c.category}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium text-slate-700">{label(c.category)}</span>
                    <span className="text-slate-500">{c.percentage}% ({c.count})</span>
                  </div>
                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-rose-500 rounded-full" style={{ width: `${c.percentage}%` }} />
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">Topics: {c.topics.join(', ') || '—'}</div>
                </div>
              ))}
            </div>
          ) : <Empty>No classified errors yet (errors are classified when the student asks the AI tutor).</Empty>}
        </Card>
        <Card title="Failed Verdicts (judge)" icon={XCircle}>
          {err.judge_outcomes.length ? <CountBars items={err.judge_outcomes} total={judgeTotal} color="bg-slate-500" /> : <Empty>No failed submissions.</Empty>}
        </Card>
      </div>
    </div>
  );
};

const AnalyticsTab = ({ p }) => {
  const shortDate = (d) => new Date(`${d}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  const trend = (key) => p.trends.map((t) => ({ label: shortDate(t.date), value: t[key] }));
  return (
    <div className="space-y-6">
      <Card title="Topic Mastery" icon={Target}>
        {p.topics.length === 0 ? <Empty>No topics attempted yet.</Empty> : (
          <div className="space-y-3">
            {p.topics.map((t) => {
              const s = MASTERY_STYLES[t.classification] || MASTERY_STYLES.Developing;
              return (
                <div key={t.topic}>
                  <div className="flex flex-wrap justify-between items-center gap-2 text-xs mb-1">
                    <span className="font-semibold text-slate-800">{t.topic}</span>
                    <span className="flex items-center gap-2 text-slate-500">
                      {t.solved}/{t.attempted} solved • {t.accuracy}%
                      <span className={`px-2 py-0.5 rounded-full border font-semibold ${s.chip}`}>{t.classification}</span>
                    </span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full ${s.bar} rounded-full`} style={{ width: `${t.accuracy}%` }} />
                  </div>
                </div>
              );
            })}
            <p className="text-[11px] text-slate-400">≥80% Strong • 50–79% Developing • &lt;50% Needs Practice (submission accuracy per topic)</p>
          </div>
        )}
      </Card>

      <div className="grid lg:grid-cols-3 gap-4">
        <TrendChart title="Points over time" data={trend('points')} color="#d97706" />
        <TrendChart title="Problems solved over time" data={trend('problems_solved')} color="#059669" />
        <TrendChart title="Submission accuracy over time" data={trend('accuracy')} color="#4f46e5" unit="%" maxValue={100} />
      </div>

      <Card title="Point History" icon={Star}>
        {p.points_history.length === 0 ? <Empty>No points events yet.</Empty> : (
          <Table head={['Date', 'Reason', 'Problem', 'Points', 'Running Total']}>
            {p.points_history.map((e) => (
              <tr key={e.id} className="hover:bg-slate-50">
                <td className="px-3 py-2.5 whitespace-nowrap">{fmtDateTime(e.created_at)}</td>
                <td className="px-3 py-2.5">
                  <div className="text-slate-800">{e.reason}</div>
                  <div className="text-[10px] text-slate-400">{label(e.event_type)}</div>
                </td>
                <td className="px-3 py-2.5">{e.problem || '—'}</td>
                <td className={`px-3 py-2.5 font-bold ${e.points >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{e.points > 0 ? '+' : ''}{e.points}</td>
                <td className="px-3 py-2.5 font-mono">{e.running_total}</td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </div>
  );
};

// ─── Page ───────────────────────────────────────────────────────────────────

export const TeacherStudentProfilePage = () => {
  const { id: classroomId, studentId } = useParams();
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('overview');

  useEffect(() => {
    setProfile(null);
    setError('');
    classroomsApi.getStudentProfile(classroomId, studentId)
      .then(setProfile)
      .catch((e) => setError(e.response?.data?.detail || 'Unable to load student profile.'));
  }, [classroomId, studentId]);

  return (
    <div className="space-y-6">
      <Link to={`/teacher/classrooms/${classroomId}`} className="inline-flex items-center space-x-1.5 text-sm text-slate-500 hover:text-indigo-600">
        <ArrowLeft className="w-4 h-4" /><span>Back to classroom</span>
      </Link>

      {error && <ErrorMessage message={error} />}
      {!profile && !error && <LoadingSpinner message="Loading student performance profile..." />}

      {profile && (
        <>
          <Header h={profile.header} />

          <div className="flex overflow-x-auto border-b border-slate-200" role="tablist">
            {TABS.map((t) => (
              <button
                key={t.key}
                role="tab"
                aria-selected={tab === t.key}
                onClick={() => setTab(t.key)}
                className={`px-4 py-2.5 text-xs font-bold whitespace-nowrap border-b-2 transition-colors ${
                  tab === t.key ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === 'overview' && <OverviewTab p={profile} />}
          {tab === 'assignments' && <AssignmentsTab p={profile} />}
          {tab === 'problems' && <ProblemsTab p={profile} />}
          {tab === 'submissions' && <SubmissionsTab p={profile} classroomId={classroomId} studentId={studentId} />}
          {tab === 'ai' && <AITab p={profile} />}
          {tab === 'analytics' && <AnalyticsTab p={profile} />}

          <div className="flex items-start space-x-2 text-[11px] text-slate-400 bg-slate-50 border border-slate-200 rounded-lg p-3">
            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <ul className="space-y-0.5">{profile.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
          </div>
        </>
      )}
    </div>
  );
};

export default TeacherStudentProfilePage;
