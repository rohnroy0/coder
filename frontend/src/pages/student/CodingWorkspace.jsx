import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { problemsApi } from '../../api/problems';
import { submissionsApi } from '../../api/submissions';
import { useAuth } from '../../context/AuthContext';
import ProblemDescription from '../../components/coding/ProblemDescription';
import CodeEditor from '../../components/coding/CodeEditor';
import TestResultPanel from '../../components/coding/TestResultPanel';
import RunResultPanel from '../../components/coding/RunResultPanel';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ChevronLeft, Terminal, CheckCircle2 } from 'lucide-react';

// Keeps an in-progress (unsubmitted) solution around across refreshes/navigation,
// scoped per student+problem so it never leaks across accounts on a shared machine.
const draftKey = (userId, problemId) => `coder:draft:${userId}:${problemId}`;

const loadDraft = (userId, problemId) => {
  if (!userId || !problemId) return null;
  try {
    return localStorage.getItem(draftKey(userId, problemId));
  } catch {
    return null;
  }
};

const saveDraft = (userId, problemId, value) => {
  if (!userId || !problemId) return;
  try {
    localStorage.setItem(draftKey(userId, problemId), value);
  } catch {
    // Storage full/unavailable (e.g. private browsing) - draft persistence is a
    // nice-to-have, so fail silently rather than interrupting the student.
  }
};

const STARTER_TEMPLATES = {
  python: `# Write your Python solution below
import sys

def main():
    # Read input from standard input
    # Example: input_data = sys.stdin.read().split()
    pass

if __name__ == "__main__":
    main()
`,
  c: `#include <stdio.h>

int main(void) {
    // Read input from stdin and print your answer to stdout
    return 0;
}
`,
  cpp: `#include <iostream>
using namespace std;

int main() {
    // Read input from stdin and print your answer to stdout
    return 0;
}
`,
};

const ENGINE_LABELS = {
  python: 'Python 3.11 Execution Engine',
  c: 'C (gcc) Execution Engine',
  cpp: 'C++ (g++) Execution Engine',
};

export const CodingWorkspace = () => {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const assignmentId = searchParams.get('assignment_id');
  const { user } = useAuth();
  const [problem, setProblem] = useState(null);
  const [sampleTestCases, setSampleTestCases] = useState([]);
  const [code, setCode] = useState(STARTER_TEMPLATES.python);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [ranCode, setRanCode] = useState('');
  const [lastAction, setLastAction] = useState(null); // 'run' | 'submit' | null
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [solved, setSolved] = useState(false);

  const language = problem?.language || 'python';

  useEffect(() => {
    const fetchProblem = async () => {
      try {
        setLoading(true);
        const data = await problemsApi.getProblemDetail(id);
        setProblem(data);
        setSolved(Boolean(data.solved));
        const template = STARTER_TEMPLATES[data.language] || STARTER_TEMPLATES.python;
        const draft = loadDraft(user?.id, id);
        setCode(draft !== null && draft !== '' ? draft : template);

        try {
          const samples = await problemsApi.getSampleTestCases(id);
          setSampleTestCases(samples);
        } catch (sampleErr) {
          console.error('Failed to load sample test cases:', sampleErr);
          setSampleTestCases([]);
        }
      } catch (err) {
        console.error('Failed to load problem workspace:', err);
        setError('Unable to load coding challenge.');
      } finally {
        setLoading(false);
      }
    };

    if (id) fetchProblem();
  }, [id]);

  // Save on every edit so a refresh (or navigating away and back) restores
  // exactly what was in the editor, not the starter template.
  useEffect(() => {
    if (loading) return;
    saveDraft(user?.id, id, code);
  }, [code, id, user?.id, loading]);

  const handleRun = async () => {
    if (!code.trim()) {
      setError('Cannot run empty code.');
      return;
    }

    setRunning(true);
    setError('');
    setLastAction('run');

    try {
      const result = await submissionsApi.runCode({
        problem_id: Number(id),
        language,
        source_code: code,
      });
      setRunResult(result);
      setRanCode(code);
    } catch (err) {
      console.error('Run failed:', err);
      const detail = err.response?.data?.detail || 'Unable to run code. Please try again.';
      setError(detail);
    } finally {
      setRunning(false);
    }
  };

  const handleSubmit = async () => {
    if (!code.trim()) {
      setError('Cannot submit empty code.');
      return;
    }

    setSubmitting(true);
    setError('');
    setLastAction('submit');

    try {
      const payload = {
        problem_id: Number(id),
        language,
        source_code: code,
      };
      if (assignmentId) {
        payload.assignment_id = Number(assignmentId);
      }

      const result = await submissionsApi.submitCode(payload);
      setSubmissionResult(result);
      if (result.status === 'ACCEPTED') {
        setSolved(true);
      }
    } catch (err) {
      console.error('Submission failed:', err);
      const detail = err.response?.data?.detail || 'Unable to submit code. Please try again.';
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading Coding Workspace..." fullScreen />;

  const backUrl = assignmentId ? `/student/assignments/${assignmentId}` : '/student/problems';

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col bg-slate-900 text-slate-100 overflow-hidden">
      {/* Top Workspace Navigation Bar */}
      <div className="bg-slate-950 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-3">
          <Link
            to={backUrl}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors flex items-center space-x-1 text-xs font-semibold"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>{assignmentId ? 'Back to Assignment' : 'Problems'}</span>
          </Link>
          <span className="text-slate-700">|</span>
          <span className="font-semibold text-slate-200 text-sm truncate max-w-md">
            {problem?.title || 'Coding Challenge'}
          </span>
          {solved && (
            <span
              className="inline-flex items-center space-x-1 px-2 py-0.5 bg-emerald-950/60 text-emerald-300 border border-emerald-800/60 rounded-full text-[10px] font-bold shrink-0"
              title="You've already solved this problem - submitting again will attempt to solve it again."
            >
              <CheckCircle2 className="w-3 h-3" />
              <span>Solved</span>
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <Terminal className="w-4 h-4 text-indigo-400" />
          <span>{ENGINE_LABELS[language] || ENGINE_LABELS.python}</span>
        </div>
      </div>

      <ErrorMessage message={error} onClose={() => setError('')} />

      {/* Main Responsive Grid Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
        {/* Left Panel: Problem Statement (5 cols on Desktop) */}
        <div className="lg:col-span-5 h-full overflow-hidden border-b lg:border-b-0 lg:border-r border-slate-800">
          <ProblemDescription problem={problem} sampleTestCases={sampleTestCases} />
        </div>

        {/* Right Panel: Code Editor & Result Panel (7 cols on Desktop) */}
        <div className="lg:col-span-7 h-full flex flex-col overflow-hidden p-3 gap-3 bg-slate-950">
          {/* Top: Monaco Code Editor */}
          <div className="flex-1 min-h-[200px] overflow-hidden">
            <CodeEditor
              code={code}
              language={language}
              onChange={setCode}
              onSubmit={handleSubmit}
              onRun={handleRun}
              loading={submitting}
              running={running}
            />
          </div>

          {/* Bottom: Run / Submission Result Panel */}
          <div className="shrink-0 max-h-[45vh] overflow-y-auto pr-1">
            {lastAction === 'run' ? (
              <RunResultPanel
                result={runResult}
                loading={running}
                problemId={Number(id)}
                language={language}
                sourceCode={ranCode}
              />
            ) : (
              <TestResultPanel result={submissionResult} loading={submitting} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CodingWorkspace;
