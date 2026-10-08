import React, { useState, useEffect } from 'react';
import { problemsApi } from '../../api/problems';
import ProblemCard from '../../components/problems/ProblemCard';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { Code2 } from 'lucide-react';

export const ProblemList = () => {
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterDifficulty, setFilterDifficulty] = useState('ALL');

  useEffect(() => {
    const fetchProblems = async () => {
      try {
        setLoading(true);
        const data = await problemsApi.getProblems();
        setProblems(data);
      } catch (err) {
        console.error('Failed to load problems:', err);
        setError('Unable to load coding problems.');
      } finally {
        setLoading(false);
      }
    };

    fetchProblems();
  }, []);

  const filteredProblems = filterDifficulty === 'ALL'
    ? problems
    : problems.filter((p) => p.difficulty === filterDifficulty);

  if (loading) return <LoadingSpinner message="Loading coding challenges..." />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Coding Challenges</h1>
          <p className="text-slate-600 text-sm mt-1">HackerRank-style problems with automated evaluation</p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1.5 bg-slate-200/60 p-1 rounded-xl w-fit">
          {['ALL', 'EASY', 'MEDIUM', 'HARD'].map((diff) => (
            <button
              key={diff}
              onClick={() => setFilterDifficulty(diff)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                filterDifficulty === diff
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {diff}
            </button>
          ))}
        </div>
      </div>

      <ErrorMessage message={error} />

      {filteredProblems.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center">
          <Code2 className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="font-semibold text-slate-800 text-base">No Problems Found</h3>
          <p className="text-xs text-slate-500 mt-1">There are no coding challenges matching the selected difficulty filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProblems.map((prob) => (
            <ProblemCard key={prob.id} problem={prob} isTeacher={false} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ProblemList;
