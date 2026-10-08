import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { problemsApi } from '../../api/problems';
import { submissionsApi } from '../../api/submissions';
import { classroomsApi } from '../../api/classrooms';
import ProblemDescription from '../../components/coding/ProblemDescription';
import CodeEditor from '../../components/coding/CodeEditor';
import TestResultPanel from '../../components/coding/TestResultPanel';
import RunResultPanel from '../../components/coding/RunResultPanel';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ChevronLeft, Terminal } from 'lucide-react';

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
  const [problem, setProblem] = useState(null);
  const [sampleTestCases, setSampleTestCases] = useState([]);
  const [code, setCode] = useState(STARTER_TEMPLATES.python);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [lastAction, setLastAction] = useState(null); // 'run' | 'submit' | null
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [disablePaste, setDisablePaste] = useState(false);

  const language = problem?.language || 'python';

  useEffect(() => {
    const fetchProblem = async () => {
      try {
        setLoading(true);
        const data = await problemsApi.getProblemDetail(id);
        setProblem(data);
        setCode(STARTER_TEMPLATES[data.language] || STARTER_TEMPLATES.python);

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

  useEffect(() => {
    // Anti-cheating: paste is blocked if ANY classroom this student belongs to
    // has it disabled - scoped to the student, not to how they reached this
    // problem (an assignment link, a direct link, Learning Paths, etc. all
    // count), so there's no "just open it a different way" bypass.
    classroomsApi.getStudentJoinedClassrooms()
      .then((joined) => setDisablePaste(joined.some((c) => c.disable_paste)))
      .catch((err) => console.error('Failed to load classroom paste settings:', err));
  }, []);

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
          <div className="flex-1 min-h-[350px] overflow-hidden">
            <CodeEditor
              code={code}
              language={language}
              onChange={setCode}
              onSubmit={handleSubmit}
              onRun={handleRun}
              loading={submitting}
              running={running}
              disablePaste={disablePaste}
            />
          </div>

          {/* Bottom: Run / Submission Result Panel */}
          <div className="shrink-0 max-h-[220px] overflow-y-auto">
            {lastAction === 'run' ? (
              <RunResultPanel result={runResult} loading={running} />
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
