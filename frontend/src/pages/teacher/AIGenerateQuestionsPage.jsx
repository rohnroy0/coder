import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { problemsApi } from '../../api/problems';
import { classroomsApi } from '../../api/classrooms';
import { assignmentsApi } from '../../api/assignments';
import DifficultyBadge from '../../components/problems/DifficultyBadge';
import ErrorMessage from '../../components/common/ErrorMessage';
import {
  Sparkles,
  Loader2,
  CheckCircle2,
  Trash2,
  Save,
  Cpu,
  Terminal,
  ShieldCheck,
  ArrowRight,
  School,
  AlertTriangle,
} from 'lucide-react';

export const AIGenerateQuestionsPage = () => {
  const [classrooms, setClassrooms] = useState([]);
  const [classroomId, setClassroomId] = useState('');
  const [language, setLanguage] = useState('python');
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [topic, setTopic] = useState('recursion');
  const [count, setCount] = useState(2);

  const [loading, setLoading] = useState(false);
  const [statusStep, setStatusStep] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const [savedIds, setSavedIds] = useState(new Set());
  const [attachErrorIds, setAttachErrorIds] = useState(new Set());
  const [discardedIds, setDiscardedIds] = useState(new Set());
  const [batchAssignmentId, setBatchAssignmentId] = useState(null);
  const [batchPublished, setBatchPublished] = useState(false);
  const [publishing, setPublishing] = useState(false);

  // This generation batch's destination assignment: created on the first
  // "Save & Activate" click, then reused for every later save in this batch
  // so all confirmed questions land in the same classroom assignment. A ref
  // (not state) so rapid sequential confirms always see the latest problem
  // list, with no stale-closure risk; batchAssignmentId mirrors just the id
  // into state purely so the UI re-renders once it's created.
  const batchAssignment = useRef({ id: null, problems: [] });

  const navigate = useNavigate();

  useEffect(() => {
    classroomsApi.getTeacherClassrooms()
      .then((data) => {
        setClassrooms(data);
        if (data.length > 0) setClassroomId(String(data[0].id));
      })
      .catch((err) => console.error('Failed to load classrooms:', err));
  }, []);

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!classroomId) {
      setError('Please select which classroom these questions are for.');
      return;
    }
    if (!topic.trim()) {
      setError('Please specify a programming topic or concept.');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    setSavedIds(new Set());
    setAttachErrorIds(new Set());
    setDiscardedIds(new Set());
    // Fresh batch -> fresh destination assignment, even if it's the same classroom as last time
    batchAssignment.current = { id: null, problems: [] };
    setBatchAssignmentId(null);
    setBatchPublished(false);
    setStatusStep('Contacting Ollama LLM engine & generating questions...');

    try {
      setTimeout(() => setStatusStep('Verifying reference solutions in isolated Docker containers...'), 3000);
      setTimeout(() => setStatusStep('Running test cases & checking output consistency...'), 6000);

      const res = await problemsApi.generateAIProblems({
        language,
        difficulty,
        topic: topic.trim(),
        count: Number(count),
      });

      setResult(res);
    } catch (err) {
      console.error('AI generation failed:', err);
      const detail = err.response?.data?.detail || 'AI problem generation failed. Please try again.';
      setError(detail);
    } finally {
      setLoading(false);
      setStatusStep('');
    }
  };

  const selectedClassroom = classrooms.find((c) => String(c.id) === String(classroomId));

  const handleConfirm = async (id) => {
    try {
      await problemsApi.confirmAIProblem(id);
      setSavedIds((prev) => new Set(prev).add(id));
    } catch (err) {
      console.error('Failed to confirm problem:', err);
      alert(err.response?.data?.detail || 'Failed to save problem.');
      return;
    }

    // Attach the now-VERIFIED problem to this batch's classroom assignment,
    // since that's what actually makes it visible to that classroom's students.
    try {
      const batch = batchAssignment.current;
      const newProblems = [...batch.problems, { problem_id: id, points: 100, order: batch.problems.length }];

      if (batch.id) {
        await assignmentsApi.updateAssignment(batch.id, { problems: newProblems });
      } else {
        const topicLabel = topic.trim();
        const created = await assignmentsApi.createAssignment({
          classroom_id: Number(classroomId),
          title: `AI Generated - ${topicLabel} (${new Date().toLocaleDateString()})`,
          description: `Auto-created from the AI Problem Generator for topic "${topicLabel}".`,
          problems: newProblems,
        });
        batch.id = created.id;
        setBatchAssignmentId(created.id);
      }
      batch.problems = newProblems;
    } catch (err) {
      console.error('Failed to attach problem to classroom assignment:', err);
      setAttachErrorIds((prev) => new Set(prev).add(id));
    }
  };

  const handlePublishBatch = async () => {
    if (!batchAssignmentId) return;
    setPublishing(true);
    try {
      await assignmentsApi.publishAssignment(batchAssignmentId);
      setBatchPublished(true);
    } catch (err) {
      console.error('Failed to publish assignment:', err);
      alert(err.response?.data?.detail || 'Failed to publish assignment.');
    } finally {
      setPublishing(false);
    }
  };

  const handleDiscard = async (id) => {
    try {
      await problemsApi.discardAIProblem(id);
      setDiscardedIds((prev) => new Set(prev).add(id));
    } catch (err) {
      console.error('Failed to discard problem:', err);
      alert(err.response?.data?.detail || 'Failed to discard problem.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Title */}
      <div className="flex items-center space-x-3">
        <div className="p-3 bg-indigo-100 text-indigo-600 rounded-2xl">
          <Sparkles className="w-7 h-7" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">AI Problem Generator</h1>
          <p className="text-slate-600 text-sm mt-0.5">
            Automatically generate & Docker-verify coding challenges using Ollama (<code className="font-mono text-xs">qwen2.5-coder:7b</code>)
          </p>
        </div>
      </div>

      <ErrorMessage message={error} onClose={() => setError('')} />

      {/* Generation Form */}
      <form onSubmit={handleGenerate} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Classroom <span className="text-red-500">*</span>
            </label>
            {classrooms.length === 0 ? (
              <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-4 py-2.5">
                You don't have any classrooms yet. <Link to="/teacher/classrooms/create" className="font-semibold underline">Create one first</Link>.
              </p>
            ) : (
              <select
                value={classroomId}
                onChange={(e) => setClassroomId(e.target.value)}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900"
                required
              >
                {classrooms.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            )}
            <p className="text-xs text-slate-500 mt-1.5">
              Each question you save below is added to a new assignment in this classroom, so students there actually see it.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Programming Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900"
            >
              <option value="python">Python 3</option>
              <option value="c">C</option>
              <option value="cpp">C++</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Difficulty Level
            </label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900"
            >
              <option value="EASY">EASY</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HARD">HARD</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Programming Topic / Concept <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. recursion, dynamic programming, binary trees"
              className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900 placeholder:text-slate-400"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Number of Questions (1-5)
            </label>
            <select
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900"
            >
              <option value={1}>1 Problem</option>
              <option value={2}>2 Problems</option>
              <option value={3}>3 Problems</option>
              <option value={4}>4 Problems</option>
              <option value={5}>5 Problems</option>
            </select>
          </div>
        </div>

        <div className="pt-2 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <Cpu className="w-4 h-4 text-indigo-500" />
            <span>Executes reference solutions in Docker containers</span>
          </div>

          <button
            type="submit"
            disabled={loading || classrooms.length === 0}
            className="flex items-center space-x-2 px-6 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl transition-colors shadow-xs"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating & Verifying...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Generate Questions</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Loading Progress State */}
      {loading && (
        <div className="bg-slate-900 text-slate-200 rounded-2xl p-6 border border-slate-800 shadow-md text-center space-y-3 animate-pulse">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
          <h3 className="font-semibold text-base text-slate-100">AI Verification Pipeline Active</h3>
          <p className="text-xs text-indigo-300 font-mono">{statusStep}</p>
        </div>
      )}

      {/* Verification Results & Preview Cards */}
      {result && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Verification Summary</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Generated {result.generated} problem(s) • Verified {result.verified} • Failed {result.failed}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 bg-emerald-100 text-emerald-800 font-bold text-xs rounded-full border border-emerald-200">
                {result.verified} / {result.generated} Verified
              </span>
            </div>
          </div>

          {result.questions.length > 0 && selectedClassroom && !batchAssignmentId && (
            <div className="flex items-center space-x-2 text-xs text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-xl px-4 py-2.5">
              <School className="w-4 h-4 shrink-0" />
              <span>
                Saved questions will be added to a new assignment in <strong>{selectedClassroom.name}</strong>.
              </span>
            </div>
          )}

          {batchAssignmentId && !batchPublished && (
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
              <div className="flex items-center space-x-2 text-amber-800">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>
                  This assignment is still a <strong>draft</strong> — students in {selectedClassroom?.name} cannot see
                  it yet.{' '}
                  <Link to={`/teacher/assignments/${batchAssignmentId}`} className="font-semibold underline">
                    View assignment
                  </Link>
                </span>
              </div>
              <button
                onClick={handlePublishBatch}
                disabled={publishing}
                className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded-lg transition-colors shrink-0"
              >
                {publishing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ArrowRight className="w-3.5 h-3.5" />}
                <span>{publishing ? 'Publishing...' : 'Publish Now'}</span>
              </button>
            </div>
          )}

          {batchAssignmentId && batchPublished && (
            <div className="flex items-center space-x-2 text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-2.5">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>
                Published! Students in <strong>{selectedClassroom?.name}</strong> can now see these questions.{' '}
                <Link to={`/teacher/assignments/${batchAssignmentId}`} className="font-semibold underline">
                  View assignment
                </Link>
              </span>
            </div>
          )}

          {result.questions.length === 0 ? (
            <div className="p-6 bg-amber-50 border border-amber-200 rounded-2xl text-amber-900 text-sm space-y-3">
              <p className="text-center font-medium">
                Unable to verify any questions generated by Ollama. Please adjust the topic or difficulty and try again.
              </p>
              {result.failure_reasons?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-amber-700 mb-1">Why the attempts failed</p>
                  <ul className="list-disc pl-5 space-y-1 text-xs font-mono break-words">
                    {result.failure_reasons.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {result.questions.map((q) => {
                const isSaved = savedIds.has(q.id);
                const attachFailed = attachErrorIds.has(q.id);
                const isDiscarded = discardedIds.has(q.id);

                if (isDiscarded) return null;

                let examplesList = [];
                try {
                  if (q.examples) examplesList = JSON.parse(q.examples);
                } catch (e) {}

                return (
                  <div key={q.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                      <div>
                        <div className="flex items-center space-x-2 mb-1">
                          <DifficultyBadge difficulty={q.difficulty} />
                          <span className="text-xs text-slate-400">•</span>
                          <span className="text-xs font-semibold text-slate-600 uppercase font-mono">{q.language}</span>
                          <span className="text-xs text-slate-400">•</span>
                          <span className="text-xs text-slate-500">{q.topic}</span>
                        </div>
                        <h3 className="text-xl font-bold text-slate-900">{q.title}</h3>
                      </div>

                      <div className="flex items-center space-x-2 self-start sm:self-auto">
                        {isSaved ? (
                          attachFailed ? (
                            <span
                              className="px-3 py-1.5 bg-amber-50 text-amber-700 font-semibold text-xs rounded-xl border border-amber-200 flex items-center space-x-1"
                              title="The problem itself was saved to the global bank, but adding it to the classroom assignment failed - add it manually from the Assignments page."
                            >
                              <AlertTriangle className="w-4 h-4 text-amber-600" />
                              <span>Saved, but not added to classroom</span>
                            </span>
                          ) : (
                            <span className="px-3 py-1.5 bg-emerald-50 text-emerald-700 font-semibold text-xs rounded-xl border border-emerald-200 flex items-center space-x-1">
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                              <span>Saved to {selectedClassroom?.name || 'classroom'}</span>
                            </span>
                          )
                        ) : (
                          <>
                            <button
                              onClick={() => handleConfirm(q.id)}
                              className="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition-colors shadow-xs flex items-center space-x-1.5"
                            >
                              <Save className="w-3.5 h-3.5" />
                              <span>Save & Activate</span>
                            </button>
                            <button
                              onClick={() => handleDiscard(q.id)}
                              className="px-3 py-2 text-xs font-semibold text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors flex items-center space-x-1"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                              <span>Discard</span>
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Verification Status Banner */}
                    <div className="p-3 bg-emerald-50/80 border border-emerald-200/80 rounded-xl text-emerald-800 text-xs flex items-center space-x-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span className="font-semibold">{q.verification_message}</span>
                    </div>

                    {/* Problem Statement */}
                    <div>
                      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Description</h4>
                      <p className="text-sm text-slate-700 whitespace-pre-line bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                        {q.description}
                      </p>
                    </div>

                    {/* Input/Output Format */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div>
                        <span className="font-semibold text-slate-700 block mb-1">Input Format:</span>
                        <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-700">{q.input_format || 'N/A'}</div>
                      </div>
                      <div>
                        <span className="font-semibold text-slate-700 block mb-1">Output Format:</span>
                        <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-700">{q.output_format || 'N/A'}</div>
                      </div>
                    </div>

                    {/* Constraints */}
                    {q.constraints && (
                      <div className="text-xs">
                        <span className="font-semibold text-slate-700 block mb-1">Constraints:</span>
                        <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-700">{q.constraints}</div>
                      </div>
                    )}

                    {/* Sample Examples */}
                    {examplesList.length > 0 && (
                      <div className="text-xs space-y-2">
                        <span className="font-semibold text-slate-700 block">Sample Examples:</span>
                        {examplesList.map((ex, i) => (
                          <div key={i} className="p-3 bg-slate-900 text-slate-200 rounded-xl font-mono text-xs grid grid-cols-1 md:grid-cols-2 gap-2">
                            <div><span className="text-slate-500">Input:</span> {ex.input}</div>
                            <div><span className="text-slate-500">Output:</span> {ex.output}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AIGenerateQuestionsPage;
