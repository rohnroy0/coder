import React from 'react';
import DifficultyBadge from '../problems/DifficultyBadge';
import { FileCode, ShieldAlert, CheckCircle2 } from 'lucide-react';

const parseExamples = (raw) => {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const Section = ({ title, children }) => (
  <div>
    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">{title}</h3>
    {children}
  </div>
);

export const ProblemDescription = ({ problem, sampleTestCases = [] }) => {
  if (!problem) return null;

  const examples = parseExamples(problem.examples);
  const hasSampleTestCases = sampleTestCases.length > 0;

  return (
    <div className="h-full flex flex-col bg-white border-r border-slate-200 overflow-y-auto p-5">
      <div className="pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-2.5 mb-2">
          <DifficultyBadge difficulty={problem.difficulty} />
          <span className="text-xs text-slate-400">•</span>
          <span className="text-xs font-semibold text-slate-600 uppercase font-mono">
            {problem.language || 'python'}
          </span>
          <span className="text-xs text-slate-400">•</span>
          <span className="text-xs font-medium text-slate-500 flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-indigo-500" />
            <span>{problem.test_case_count ?? 0} Hidden Test Cases</span>
          </span>
        </div>
        <h1 className="text-xl font-bold text-slate-900 leading-tight">{problem.title}</h1>
      </div>

      <div className="mt-5 space-y-4 flex-1">
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Problem Description
          </h3>
          <div className="text-slate-700 text-sm whitespace-pre-line leading-relaxed bg-slate-50/50 p-4 rounded-xl border border-slate-100">
            {problem.description}
          </div>
        </div>

        {problem.input_format && (
          <Section title="Input Format">
            <p className="text-slate-700 text-sm whitespace-pre-line">{problem.input_format}</p>
          </Section>
        )}

        {problem.output_format && (
          <Section title="Output Format">
            <p className="text-slate-700 text-sm whitespace-pre-line">{problem.output_format}</p>
          </Section>
        )}

        {problem.constraints && (
          <Section title="Constraints">
            <pre className="text-slate-700 text-xs font-mono whitespace-pre-wrap bg-slate-50 p-3 rounded-lg border border-slate-100">
              {problem.constraints}
            </pre>
          </Section>
        )}

        {hasSampleTestCases && (
          <Section title={`Sample Test Case${sampleTestCases.length > 1 ? 's' : ''}`}>
            <div className="space-y-2">
              {sampleTestCases.map((tc, i) => (
                <div key={tc.id ?? i}>
                  <div className="text-[11px] font-semibold text-slate-500 mb-1">Test Case {i + 1}</div>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="bg-slate-900 text-slate-100 rounded-lg p-3">
                      <div className="text-slate-400 mb-1">Input</div>
                      <pre className="whitespace-pre-wrap">{tc.input}</pre>
                    </div>
                    <div className="bg-slate-900 text-slate-100 rounded-lg p-3">
                      <div className="text-slate-400 mb-1">Output</div>
                      <pre className="whitespace-pre-wrap">{tc.expected_output}</pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-slate-400 mt-2">
              Use the <strong>Run</strong> button to check your code against these before submitting.
            </p>
          </Section>
        )}

        {!hasSampleTestCases && examples.length > 0 && (
          <Section title={examples.length > 1 ? 'Examples' : 'Example'}>
            <div className="space-y-2">
              {examples.map((ex, i) => (
                <div key={i} className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="bg-slate-900 text-slate-100 rounded-lg p-3">
                    <div className="text-slate-400 mb-1">Input</div>
                    <pre className="whitespace-pre-wrap">{ex.input}</pre>
                  </div>
                  <div className="bg-slate-900 text-slate-100 rounded-lg p-3">
                    <div className="text-slate-400 mb-1">Output</div>
                    <pre className="whitespace-pre-wrap">{ex.output}</pre>
                  </div>
                </div>
              ))}
            </div>
          </Section>
        )}

        <div className="p-3.5 bg-amber-50/80 border border-amber-200/60 rounded-xl text-amber-800 text-xs flex items-start space-x-2.5">
          <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Evaluation Rule:</span> Your solution will be executed against hidden evaluation test cases in a secure, isolated container environment. Make sure to process `sys.stdin` or `input()` correctly.
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProblemDescription;
