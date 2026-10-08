import React, { useState } from 'react';
import ErrorMessage from '../common/ErrorMessage';
import { Loader2, Code2 } from 'lucide-react';

export const ProblemForm = ({ onSubmit, loading = false, error = '' }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [difficulty, setDifficulty] = useState('EASY');
  const [language, setLanguage] = useState('python');
  const [inputFormat, setInputFormat] = useState('');
  const [outputFormat, setOutputFormat] = useState('');
  const [constraints, setConstraints] = useState('');
  const [exampleInput, setExampleInput] = useState('');
  const [exampleOutput, setExampleOutput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;
    const payload = {
      title: title.trim(),
      description: description.trim(),
      difficulty,
      language,
      input_format: inputFormat.trim() || null,
      output_format: outputFormat.trim() || null,
      constraints: constraints.trim() || null,
    };
    // Same JSON shape AI-generated problems use: [{ input, output }]
    if (exampleInput.trim() && exampleOutput.trim()) {
      payload.examples = JSON.stringify([{ input: exampleInput.trim(), output: exampleOutput.trim() }]);
    }
    onSubmit(payload);
  };

  const fieldClass =
    'w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900 placeholder:text-slate-400';

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
      <div className="flex items-center space-x-3 pb-4 border-b border-slate-100">
        <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl">
          <Code2 className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900">Create Coding Problem</h2>
          <p className="text-xs text-slate-500">Define problem details and constraints for students</p>
        </div>
      </div>

      <ErrorMessage message={error} />

      <div>
        <label htmlFor="title" className="block text-sm font-medium text-slate-700 mb-1">
          Problem Title <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Two Sum"
          className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900 placeholder:text-slate-400"
          required
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="difficulty" className="block text-sm font-medium text-slate-700 mb-1">
            Difficulty Level <span className="text-red-500">*</span>
          </label>
          <select
            id="difficulty"
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
          <label htmlFor="language" className="block text-sm font-medium text-slate-700 mb-1">
            Programming Language <span className="text-red-500">*</span>
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900"
          >
            <option value="python">Python 3</option>
            <option value="c">C</option>
            <option value="cpp">C++</option>
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-slate-700 mb-1">
          Problem Statement & Description <span className="text-red-500">*</span>
        </label>
        <textarea
          id="description"
          rows={6}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Provide problem requirements, input/output format expectations, and sample test details..."
          className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900 placeholder:text-slate-400 font-sans"
          required
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="inputFormat" className="block text-sm font-medium text-slate-700 mb-1">
            Input Format
          </label>
          <textarea
            id="inputFormat"
            rows={2}
            value={inputFormat}
            onChange={(e) => setInputFormat(e.target.value)}
            placeholder="e.g. Two integers a and b on a single line, separated by a space"
            className={fieldClass}
          />
        </div>
        <div>
          <label htmlFor="outputFormat" className="block text-sm font-medium text-slate-700 mb-1">
            Output Format
          </label>
          <textarea
            id="outputFormat"
            rows={2}
            value={outputFormat}
            onChange={(e) => setOutputFormat(e.target.value)}
            placeholder="e.g. A single integer: a + b"
            className={fieldClass}
          />
        </div>
      </div>

      <div>
        <label htmlFor="constraints" className="block text-sm font-medium text-slate-700 mb-1">
          Constraints
        </label>
        <input
          type="text"
          id="constraints"
          value={constraints}
          onChange={(e) => setConstraints(e.target.value)}
          placeholder="e.g. -10^9 <= a, b <= 10^9"
          className={fieldClass}
        />
      </div>

      <div>
        <span className="block text-sm font-medium text-slate-700 mb-1">Sample Example (shown to students)</span>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <textarea
            id="exampleInput"
            aria-label="Example input"
            rows={3}
            value={exampleInput}
            onChange={(e) => setExampleInput(e.target.value)}
            placeholder="Example input, e.g. 5 10"
            className={`${fieldClass} font-mono`}
          />
          <textarea
            id="exampleOutput"
            aria-label="Example output"
            rows={3}
            value={exampleOutput}
            onChange={(e) => setExampleOutput(e.target.value)}
            placeholder="Example output, e.g. 15"
            className={`${fieldClass} font-mono`}
          />
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Hidden test cases are added on the next page. Keep the example consistent with them.
        </p>
      </div>

      <div className="pt-2 flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className="flex items-center space-x-2 px-6 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl transition-colors shadow-xs"
        >
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          <span>Create Problem</span>
        </button>
      </div>
    </form>
  );
};

export default ProblemForm;
