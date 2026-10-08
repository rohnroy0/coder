import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Code2, LogOut, User as UserIcon } from 'lucide-react';

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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-3">
            <Link to={homePath} className="flex items-center space-x-2.5 text-indigo-600 font-bold text-xl hover:text-indigo-700 transition-colors">
              <div className="p-2 bg-indigo-50 rounded-lg">
                <Code2 className="w-6 h-6 text-indigo-600" />
              </div>
              <span className="tracking-tight text-slate-900">Coder</span>
            </Link>
          </div>

          {user && (
            <div className="flex items-center space-x-4">
              <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${
                isTeacher ? 'bg-purple-100 text-purple-700 border border-purple-200' : 'bg-blue-100 text-blue-700 border border-blue-200'
              }`}>
                {user.role}
              </span>

              <div className="flex items-center space-x-2 text-sm text-slate-700">
                <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600">
                  <UserIcon className="w-4 h-4" />
                </div>
                <div className="hidden sm:block text-left">
                  <div className="font-medium leading-none text-slate-900">{user.name}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{user.email}</div>
                </div>
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center space-x-1.5 px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-100"
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
