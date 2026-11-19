import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import ErrorMessage from '../../components/common/ErrorMessage';
import { GraduationCap, LogIn, Loader2 } from 'lucide-react';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isExpired = new URLSearchParams(location.search).get('expired');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) return;

    setLoading(true);
    setError('');

    try {
      const user = await login(email.trim(), password);
      if (user.role === 'TEACHER') {
        navigate('/teacher');
      } else {
        navigate('/student');
      }
    } catch (err) {
      console.error('Login failed:', err);
      const detail = err.response?.data?.detail || 'Invalid email or password. Please try again.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link to="/" className="inline-flex items-center gap-2.5">
          <div className="w-11 h-11 rounded-xl bg-indigo-700 flex items-center justify-center shadow-md ring-1 ring-indigo-900/40">
            <GraduationCap className="w-6 h-6 text-gold-400" />
          </div>
          <span className="font-display font-semibold text-3xl text-slate-900">Coder</span>
        </Link>
        <h2 className="mt-7 text-3xl font-semibold tracking-tight text-slate-900">Welcome back</h2>
        <div className="mx-auto mt-4 h-px w-16 bg-gold-500/70" />
        <p className="mt-4 text-sm text-slate-500">
          New here?{' '}
          <Link to="/register" className="font-semibold text-indigo-700 hover:text-indigo-600 underline underline-offset-2 decoration-gold-500/50">
            Create an account
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-xl border border-slate-200 sm:rounded-2xl sm:px-10">
          {isExpired && (
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-xs">
              Session expired. Please log in again to continue.
            </div>
          )}

          <ErrorMessage message={error} onClose={() => setError('')} />

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700">
                Email Address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900 placeholder:text-slate-400"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900 placeholder:text-slate-400"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center items-center space-x-2 py-2.5 px-4 border border-transparent rounded-xl shadow-xs text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <LogIn className="w-4 h-4" />
                    <span>Sign In</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
