import React, { useState } from 'react';
import ErrorMessage from '../common/ErrorMessage';
import { PlusCircle, Loader2 } from 'lucide-react';

export const TestCaseForm = ({ onAddTestCase, loading = false, error = '' }) => {
  const [input, setInput] = useState('');
  const [expectedOutput, setExpectedOutput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input || !expectedOutput) return;
    onAddTestCase({ input, expected_output: expectedOutput });
    setInput('');
    setExpectedOutput('');
  };

  return (
    <form onSubmit={handleSubmit} className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
      <h3 className="font-semibold text-slate-800 text-sm flex items-center space-x-2">
        <PlusCircle className="w-4 h-4 text-indigo-600" />
        <span>Add Hidden Test Case</span>
      </h3>

      <ErrorMessage message={error} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Standard Input (stdin)
          </label>
          <textarea
            rows={3}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. 5 10"
            className="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-xs font-mono focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-slate-900"
            required
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Expected Output (stdout)
          </label>
          <textarea
            rows={3}
            value={expectedOutput}
            onChange={(e) => setExpectedOutput(e.target.value)}
            placeholder="e.g. 15"
            className="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-xs font-mono focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-slate-900"
            required
          />
        </div>
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg transition-colors shadow-xs"
        >
          {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
          <span>Add Test Case</span>
        </button>
      </div>
    </form>
  );
};

export default TestCaseForm;
