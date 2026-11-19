import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { GraduationCap, LogOut, User as UserIcon } from 'lucide-react';

export const Navbar = () => {
  const { user, logout, isTeacher } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const homePath = isTeacher ? '/teacher' : '/student';

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      {/* Role-colored hairline: burgundy for faculty, navy for students */}
      <div className={`h-0.5 w-full ${isTeacher ? 'bg-purple-600' : 'bg-indigo-700'}`} />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to={homePath} className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-lg bg-indigo-700 flex items-center justify-center shadow-sm ring-1 ring-indigo-900/40 group-hover:bg-indigo-800 transition-colors">
                <GraduationCap className="w-5 h-5 text-gold-400" />
              </div>
              <span className="font-display font-semibold text-2xl text-slate-900">Coder</span>
            </Link>
          </div>

          {user && (
            <div className="flex items-center gap-4">
              <span
                className={`px-2.5 py-1 text-[11px] font-bold tracking-wider rounded-full border ${
                  isTeacher
                    ? 'bg-purple-50 text-purple-700 border-purple-200'
                    : 'bg-indigo-50 text-indigo-700 border-indigo-200'
                }`}
              >
                {isTeacher ? 'FACULTY' : 'STUDENT'}
              </span>

              <div className="flex items-center gap-2.5 text-sm text-slate-700">
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold text-sm text-white shadow-sm ${
                    isTeacher ? 'bg-purple-600' : 'bg-indigo-700'
                  }`}
                >
                  {user.name ? user.name.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
                </div>
                <div className="hidden sm:block text-left">
                  <div className="font-semibold leading-none text-slate-900">{user.name}</div>
                  <div className="text-xs text-slate-500 mt-1">{user.email}</div>
                </div>
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-100"
                title="Log out"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
