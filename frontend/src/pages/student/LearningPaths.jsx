import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { learningApi } from '../../api/learning';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import {
  Lock, CheckCircle2, Star, Flame, PlayCircle, MapPin, X, ChevronRight, Zap,
} from 'lucide-react';

const LANGUAGES = [
  { key: 'python', label: 'Python' },
  { key: 'c', label: 'C' },
  { key: 'cpp', label: 'C++' },
];

const ROW_HEIGHT = 168; // vertical px between node centers
const WAVE_AMPLITUDE = 24; // % of track width the node wanders left/right
const CENTER_PCT = 50;

const DIFFICULTY_STYLES = {
  EASY: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  MEDIUM: 'bg-amber-50 text-amber-700 border-amber-200',
  HARD: 'bg-rose-50 text-rose-700 border-rose-200',
};

// State visuals: color, icon, label - kept in one place so node + legend stay in sync
const STATE_META = {
  LOCKED: { ring: 'ring-slate-300', bg: 'bg-slate-200', text: 'text-slate-400', label: 'Locked' },
  AVAILABLE: { ring: 'ring-indigo-400', bg: 'bg-indigo-600', text: 'text-white', label: 'Available' },
  IN_PROGRESS: { ring: 'ring-amber-400', bg: 'bg-amber-500', text: 'text-white', label: 'In Progress' },
  COMPLETED: { ring: 'ring-emerald-400', bg: 'bg-emerald-500', text: 'text-white', label: 'Completed' },
  MASTERED: { ring: 'ring-fuchsia-400', bg: 'bg-gradient-to-br from-fuchsia-500 to-purple-600', text: 'text-white', label: 'Mastered' },
};

const nodeXPct = (index) => CENTER_PCT + Math.sin(index * 1.05) * WAVE_AMPLITUDE;

const buildWavePath = (count, totalHeight) => {
  const points = [];
  const step = 6;
  for (let y = 54; y <= totalHeight - 54; y += step) {
    const fIndex = (y - 54) / ROW_HEIGHT;
    points.push(`${nodeXPct(fIndex).toFixed(2)},${y}`);
  }
  return points.length ? `M ${points.join(' L ')}` : '';
};

const StateIcon = ({ state, className }) => {
  if (state === 'LOCKED') return <Lock className={className} />;
  if (state === 'MASTERED') return <Star className={className} fill="currentColor" />;
  if (state === 'COMPLETED') return <CheckCircle2 className={className} />;
  return <Flame className={className} />;
};

const NodeDetailCard = ({ chapter, onClose }) => {
  const meta = STATE_META[chapter.state];
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-lg p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full border ${DIFFICULTY_STYLES[chapter.difficulty] || DIFFICULTY_STYLES.EASY}`}>
              {chapter.difficulty}
            </span>
            <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${meta.bg} ${meta.text}`}>
              {meta.label}
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900">{chapter.title}</h3>
          <p className="text-xs text-slate-500 mt-0.5">{chapter.description}</p>
        </div>
        <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-700 shrink-0">
          <X className="w-4 h-4" />
        </button>
      </div>

      {chapter.state === 'LOCKED' ? (
        <div className="flex items-center space-x-2 text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-xl p-3">
          <Lock className="w-4 h-4 shrink-0" />
          <span>
            Complete{chapter.prerequisite_title ? ` "${chapter.prerequisite_title}"` : ' the previous concept'} to unlock.
          </span>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-600">
              {chapter.completed_problems}/{chapter.total_problems} solved
            </span>
            <span className="flex items-center space-x-1 font-bold text-amber-600">
              <Zap className="w-3.5 h-3.5 fill-current" />
              <span>+{chapter.xp_earned}/{chapter.xp_reward} XP</span>
            </span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${chapter.is_mastered ? 'bg-gradient-to-r from-fuchsia-500 to-purple-600' : chapter.is_completed ? 'bg-emerald-500' : 'bg-indigo-500'}`}
              style={{ width: `${chapter.progress_pct}%` }}
            />
          </div>

          <div className="space-y-2 pt-1">
            {chapter.problems.map((p) => (
              <div key={p.problem_id} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2">
                <div className="flex items-center space-x-2 min-w-0">
                  {p.solved ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-slate-300 shrink-0" />
                  )}
                  <span className="text-sm text-slate-800 truncate">{p.title}</span>
                </div>
                <Link
                  to={`/student/problems/${p.problem_id}/code`}
                  className="inline-flex items-center space-x-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 shrink-0 ml-2"
                >
                  <PlayCircle className="w-3.5 h-3.5" />
                  <span>{p.solved ? 'Review' : 'Solve'}</span>
                </Link>
              </div>
            ))}
          </div>

          {chapter.is_mastered && (
            <div className="flex items-center space-x-2 text-xs font-semibold text-fuchsia-700 bg-fuchsia-50 border border-fuchsia-200 rounded-xl p-2.5">
              <Star className="w-4 h-4 fill-current" />
              <span>Mastered — solved every problem correctly on the first try!</span>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export const LearningPaths = () => {
  const [activeLanguage, setActiveLanguage] = useState('python');
  const [paths, setPaths] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true);
        const results = await Promise.all(LANGUAGES.map((l) => learningApi.getPath(l.key).catch(() => [])));
        const merged = {};
        LANGUAGES.forEach((l, i) => { merged[l.key] = results[i]; });
        setPaths(merged);
      } catch (err) {
        console.error('Failed to load learning paths:', err);
        setError('Unable to load learning paths.');
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const chapters = paths[activeLanguage] || [];
  const selected = chapters.find((c) => c.id === selectedId) || null;

  // The student's current frontier: first node that's available or mid-progress
  const currentIndex = useMemo(
    () => chapters.findIndex((c) => c.state === 'AVAILABLE' || c.state === 'IN_PROGRESS'),
    [chapters]
  );

  const totalXpEarned = chapters.reduce((sum, c) => sum + c.xp_earned, 0);
  const totalXpAvailable = chapters.reduce((sum, c) => sum + c.xp_reward, 0);
  const masteredCount = chapters.filter((c) => c.is_mastered).length;

  useEffect(() => { setSelectedId(null); }, [activeLanguage]);

  if (loading) return <LoadingSpinner message="Loading learning paths..." />;

  const totalHeight = chapters.length * ROW_HEIGHT + 60;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Learning Paths</h1>
        <p className="text-slate-600 text-sm mt-1">
          Your journey through each language — complete a concept to unlock the next
        </p>
      </div>

      <ErrorMessage message={error} />

      {/* Language Tabs */}
      <div className="flex items-center space-x-1.5 bg-slate-200/60 p-1 rounded-xl w-fit">
        {LANGUAGES.map((l) => (
          <button
            key={l.key}
            onClick={() => setActiveLanguage(l.key)}
            className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
              activeLanguage === l.key ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {l.label}
          </button>
        ))}
      </div>

      {chapters.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center">
          <MapPin className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="font-semibold text-slate-800 text-base">No path published yet</h3>
          <p className="text-xs text-slate-500 mt-1">Check back later for this language's learning path.</p>
        </div>
      ) : (
        <>
          {/* Summary strip */}
          <div className="flex flex-wrap items-center gap-3 bg-white rounded-2xl border border-slate-200 p-4 shadow-xs">
            <div className="flex items-center space-x-1.5 text-amber-600 font-bold text-sm">
              <Zap className="w-4 h-4 fill-current" />
              <span>{totalXpEarned} / {totalXpAvailable} XP</span>
            </div>
            <span className="text-slate-300">•</span>
            <div className="flex items-center space-x-1.5 text-fuchsia-600 font-bold text-sm">
              <Star className="w-4 h-4 fill-current" />
              <span>{masteredCount} Mastered</span>
            </div>
            <span className="text-slate-300">•</span>
            <div className="text-sm text-slate-500">
              {chapters.filter((c) => c.is_completed).length} / {chapters.length} concepts complete
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* The winding path */}
            <div className="lg:col-span-3 relative" style={{ height: totalHeight }}>
              <svg
                className="absolute inset-0 w-full h-full pointer-events-none"
                viewBox={`0 0 100 ${totalHeight}`}
                preserveAspectRatio="none"
              >
                <path
                  d={buildWavePath(chapters.length, totalHeight)}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.2"
                  strokeDasharray="0.1 3.2"
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                  className="text-slate-300"
                />
              </svg>

              {chapters.map((chapter, i) => {
                const xPct = nodeXPct(i);
                const top = i * ROW_HEIGHT + 54;
                const meta = STATE_META[chapter.state];
                const isCurrent = i === currentIndex;
                const isSelected = chapter.id === selectedId;

                return (
                  <div
                    key={chapter.id}
                    className="absolute flex flex-col items-center"
                    style={{ left: `${xPct}%`, top, transform: 'translate(-50%, -50%)' }}
                  >
                    {isCurrent && (
                      <div className="absolute -top-9 flex items-center space-x-1 px-2.5 py-1 bg-indigo-600 text-white text-[10px] font-bold rounded-full shadow-md whitespace-nowrap animate-bounce">
                        <MapPin className="w-3 h-3" />
                        <span>You are here</span>
                      </div>
                    )}

                    <button
                      onClick={() => setSelectedId(isSelected ? null : chapter.id)}
                      title={chapter.title}
                      className={`relative w-16 h-16 rounded-full flex items-center justify-center shadow-md ring-4 transition-transform hover:scale-110 cursor-pointer ${meta.ring} ${meta.bg} ${
                        chapter.state === 'LOCKED' ? 'opacity-70' : ''
                      } ${isSelected ? 'scale-110 ring-8' : ''}`}
                    >
                      <StateIcon state={chapter.state} className={`w-6 h-6 ${meta.text}`} />
                      {chapter.state === 'IN_PROGRESS' && (
                        <span className="absolute -bottom-1 -right-1 bg-white text-amber-600 text-[9px] font-extrabold rounded-full px-1.5 py-0.5 border border-amber-300 shadow-sm">
                          {Math.round(chapter.progress_pct)}%
                        </span>
                      )}
                    </button>

                    <div className="mt-2 text-center w-28">
                      <div className={`text-[11px] font-bold leading-tight ${chapter.state === 'LOCKED' ? 'text-slate-400' : 'text-slate-800'}`}>
                        {chapter.title}
                      </div>
                      {chapter.state !== 'LOCKED' && (
                        <div className="text-[10px] text-amber-600 font-semibold mt-0.5 flex items-center justify-center space-x-0.5">
                          <Zap className="w-2.5 h-2.5 fill-current" />
                          <span>+{chapter.xp_reward} XP</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Detail panel */}
            <div className="lg:col-span-2">
              <div className="lg:sticky lg:top-4">
                {selected ? (
                  <NodeDetailCard chapter={selected} onClose={() => setSelectedId(null)} />
                ) : (
                  <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500 flex flex-col items-center space-y-2">
                    <ChevronRight className="w-6 h-6 text-slate-400" />
                    <span>Tap a node on the path to see its details.</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default LearningPaths;
