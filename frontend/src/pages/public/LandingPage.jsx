import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Sparkles,
  ArrowRight,
  UserCheck,
  GraduationCap,
  Trophy,
  Bot,
  Container,
} from 'lucide-react';

const FEATURES = [
  {
    icon: Container,
    title: 'Sandboxed Judging',
    text: 'Every submission runs in an isolated container with hidden test cases — Python, C, and C++.',
  },
  {
    icon: Bot,
    title: 'Socratic AI Tutor',
    text: 'Progressive hints that teach the idea without ever handing over the solution.',
  },
  {
    icon: Sparkles,
    title: 'AI Problem Generator',
    text: 'Teachers generate original, auto-verified problem sets for any topic in seconds.',
  },
  {
    icon: Trophy,
    title: 'Points & Leaderboards',
    text: 'Per-classroom scoring, streaks, and badges keep every cohort motivated.',
  },
];

export const LandingPage = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-slate-50/80 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-indigo-700 flex items-center justify-center shadow-sm ring-1 ring-indigo-900/40">
              <GraduationCap className="w-5 h-5 text-gold-400" />
            </div>
            <span className="font-display font-semibold text-2xl text-slate-900">Coder</span>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/login"
              className="px-4 py-2 text-sm font-semibold text-slate-700 hover:text-indigo-700 transition-colors"
            >
              Log In
            </Link>
            <Link
              to="/register"
              className="px-4 py-2 text-sm font-semibold text-white bg-indigo-700 hover:bg-indigo-800 rounded-lg transition-colors shadow-sm"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero — deep ink with gold rule */}
      <section className="relative bg-slate-900 text-white overflow-hidden">
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              'radial-gradient(circle at 20% 20%, #c9a227 0, transparent 35%), radial-gradient(circle at 80% 70%, #3f6c9f 0, transparent 40%)',
          }}
        />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-28 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-gold-500/40 bg-gold-500/10 text-gold-300 text-xs font-semibold tracking-wide uppercase mb-8">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>The Coding Classroom, Elevated</span>
          </div>

          <h1 className="font-display text-4xl sm:text-6xl font-semibold tracking-tight leading-[1.08] max-w-4xl mx-auto">
            Where Rigorous Code Meets
            <span className="block text-gold-400 italic">Thoughtful Teaching</span>
          </h1>

          <div className="mx-auto mt-8 h-px w-24 bg-gold-500/60" />

          <p className="mt-8 text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Classroom management meets HackerRank-style assessment. Teachers curate
            problem sets with hidden tests; students solve them against a real,
            containerized judge — with an AI tutor that guides, never spoils.
          </p>

          <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/register?role=TEACHER"
              className="group w-full sm:w-auto px-7 py-3.5 text-base font-semibold text-white bg-purple-600 hover:bg-purple-700 rounded-xl transition-all shadow-lg shadow-purple-950/40 flex items-center justify-center gap-2.5 ring-1 ring-purple-400/20"
            >
              <GraduationCap className="w-5 h-5" />
              <span>I'm a Teacher</span>
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
            </Link>

            <Link
              to="/register?role=STUDENT"
              className="group w-full sm:w-auto px-7 py-3.5 text-base font-semibold text-slate-900 bg-white hover:bg-slate-100 rounded-xl transition-all shadow-lg shadow-black/20 flex items-center justify-center gap-2.5"
            >
              <UserCheck className="w-5 h-5 text-indigo-700" />
              <span>I'm a Student</span>
              <ArrowRight className="w-4 h-4 text-slate-400 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 w-full">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl font-semibold text-slate-900">Built for the Modern CS Classroom</h2>
          <p className="mt-3 text-slate-600 max-w-xl mx-auto">
            Everything a course needs — assignments, automated judging, analytics,
            and AI assistance — in one quiet, focused place.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div
              key={title}
              className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition-all"
            >
              <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center mb-4">
                <Icon className="w-5 h-5 text-indigo-700" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-1.5">{title}</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-10 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 text-center space-y-3">
          <div className="flex items-center justify-center gap-2">
            <GraduationCap className="w-4 h-4 text-gold-500" />
            <span className="font-display text-lg text-slate-200">Coder</span>
          </div>
          <p className="text-xs">© 2026 Coder. A smarter coding platform for every student and teacher.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
