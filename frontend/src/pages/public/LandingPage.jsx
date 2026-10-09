import React from 'react';
import { Link } from 'react-router-dom';
import {
  Code2,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  UserCheck,
  GraduationCap
} from 'lucide-react';

export const LandingPage = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header / Nav */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <Code2 className="w-6 h-6" />
            </div>
            <span className="font-bold text-xl text-slate-900 tracking-tight">Coder</span>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              to="/login"
              className="px-4 py-2 text-sm font-semibold text-slate-700 hover:text-indigo-600 transition-colors"
            >
              Log In
            </Link>
            <Link
              to="/register"
              className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors shadow-xs"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center flex-1 flex flex-col justify-center">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold mb-6 self-center">
          <Sparkles className="w-4 h-4 text-indigo-500" />
          <span>Next-Generation Coding Assessment Platform</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight max-w-4xl mx-auto">
          A Smarter Coding Platform for <span className="text-indigo-600">Every Student and Teacher</span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Combining Google Classroom management with HackerRank-style coding assessments. Teachers build problem sets and hidden test cases; students solve challenges with automated containerized execution.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/register?role=TEACHER"
            className="w-full sm:w-auto px-6 py-3.5 text-base font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors shadow-md flex items-center justify-center space-x-2"
          >
            <GraduationCap className="w-5 h-5" />
            <span>Join as Teacher</span>
            <ArrowRight className="w-4 h-4" />
          </Link>

          <Link
            to="/register?role=STUDENT"
            className="w-full sm:w-auto px-6 py-3.5 text-base font-semibold text-slate-800 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl transition-colors shadow-xs flex items-center justify-center space-x-2"
          >
            <UserCheck className="w-5 h-5 text-indigo-600" />
            <span>Join as Student</span>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white text-slate-500 py-8 text-center text-xs border-t border-slate-200">
        <p>© 2026 Coder. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default LandingPage;
