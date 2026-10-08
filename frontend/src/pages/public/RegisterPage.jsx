import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import ErrorMessage from '../../components/common/ErrorMessage';
import { Code2, UserPlus, Loader2, GraduationCap, UserCheck } from 'lucide-react';

export const RegisterPage = () => {
  const [searchParams] = useSearchParams();
  const defaultRole = searchParams.get('role') === 'TEACHER' ? 'TEACHER' : 'STUDENT';

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState(defaultRole);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !password) return;

    setLoading(true);
    setError('');

    try {
      const user = await register(name.trim(), email.trim(), password, role);
      if (user.role === 'TEACHER') {
        navigate('/teacher');
      } else {
        navigate('/student');
      }
    } catch (err) {
      console.error('Registration failed:', err);
      const detail = err.response?.data?.detail || 'Registration failed. Please check your details.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link to="/" className="inline-flex items-center space-x-2 text-indigo-600 font-bold text-2xl">
          <div className="p-2.5 bg-indigo-50 rounded-xl">
            <Code2 className="w-8 h-8 text-indigo-600" />
          </div>
          <span className="text-slate-900 tracking-tight">Coder</span>
        </Link>
        <h2 className="mt-6 text-2xl font-bold tracking-tight text-slate-900">Create your account</h2>
        <p className="mt-2 text-xs text-slate-500">
          Already registered?{' '}
          <Link to="/login" className="font-semibold text-indigo-600 hover:text-indigo-500">
            Sign in to existing account
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-xl border border-slate-200 sm:rounded-2xl sm:px-10">
          <ErrorMessage message={error} onClose={() => setError('')} />

          <form className="space-y-5" onSubmit={handleSubmit}>
            {/* Role Selection Tabs */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Select Account Role</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setRole('STUDENT')}
                  className={`flex items-center justify-center space-x-2 p-3 rounded-xl border text-xs font-semibold transition-all ${
                    role === 'STUDENT'
                      ? 'bg-indigo-50 border-indigo-500 text-indigo-700 ring-2 ring-indigo-500/20'
                      : 'border-slate-200 bg-slate-50/50 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <UserCheck className="w-4 h-4" />
                  <span>Student</span>
                </button>

                <button
                  type="button"
                  onClick={() => setRole('TEACHER')}
                  className={`flex items-center justify-center space-x-2 p-3 rounded-xl border text-xs font-semibold transition-all ${
                    role === 'TEACHER'
                      ? 'bg-purple-50 border-purple-500 text-purple-700 ring-2 ring-purple-500/20'
                      : 'border-slate-200 bg-slate-50/50 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <GraduationCap className="w-4 h-4" />
                  <span>Teacher</span>
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="name" className="block text-sm font-medium text-slate-700">
                Full Name
              </label>
              <div className="mt-1">
                <input
                  id="name"
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm text-slate-900 placeholder:text-slate-400"
                />
              </div>
            </div>

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
                    <UserPlus className="w-4 h-4" />
                    <span>Create {role === 'TEACHER' ? 'Teacher' : 'Student'} Account</span>
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

export default RegisterPage;
