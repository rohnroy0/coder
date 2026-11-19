import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  GraduationCap,
  Trophy,
  Bot,
  Container,
  ClipboardList,
  CheckCircle2,
} from 'lucide-react';

const FEATURES = [
  {
    icon: Container,
    title: 'Sandboxed judging',
    text: 'Python, C, and C++ submissions run in isolated containers against hidden test cases.',
  },
  {
    icon: Bot,
    title: 'A tutor that teaches',
    text: 'Progressive Socratic hints explain the idea — never the answer.',
  },
  {
    icon: ClipboardList,
    title: 'Courses, not chaos',
    text: 'Classrooms, assignments, deadlines, and AI-generated problem sets in one place.',
  },
  {
    icon: Trophy,
    title: 'Earned motivation',
    text: 'Per-classroom points, streaks, and badges — graded fairly, displayed beautifully.',
  },
];

export const LandingPage = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-slate-50/90 backdrop-blur">
        <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-indigo-700 flex items-center justify-center ring-1 ring-indigo-900/30">
              <GraduationCap className="w-5 h-5 text-gold-400" />
            </div>
            <span className="font-display font-semibold text-2xl text-slate-900">Coder</span>
          </div>

          <div className="flex items-center gap-6">
            <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
              Log in
            </Link>
            <Link
              to="/register"
              className="px-4.5 py-2 text-sm font-semibold text-white bg-indigo-700 hover:bg-indigo-800 rounded-full transition-colors"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-5 sm:px-6 pt-14 pb-10 sm:pt-28 text-center w-full">
        <div className="flex items-center justify-center gap-4 mb-8 sm:mb-10">
          <span className="hidden sm:block h-px w-10 bg-gold-500/60" />
          <span className="text-[10px] sm:text-[11px] font-semibold tracking-[0.18em] sm:tracking-[0.22em] uppercase text-slate-500">
            A coding classroom for modern campuses
          </span>
          <span className="hidden sm:block h-px w-10 bg-gold-500/60" />
        </div>

        <h1 className="font-display text-[2.6rem] sm:text-7xl font-semibold text-slate-900 tracking-tight leading-[1.06] sm:leading-[1.04] max-w-4xl mx-auto">
          Where rigorous code meets
          <span className="block italic text-purple-700">thoughtful teaching.</span>
        </h1>

        <p className="mt-8 text-lg text-slate-600 max-w-xl mx-auto leading-relaxed">
          Teachers set the problems. A containerized judge grades them honestly.
          An AI tutor guides students without ever giving the answer away.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            to="/register?role=STUDENT"
            className="group w-full sm:w-auto px-7 py-3 text-[15px] font-semibold text-white bg-indigo-700 hover:bg-indigo-800 rounded-full transition-colors flex items-center justify-center gap-2"
          >
            <span>Join as a student</span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link
            to="/register?role=TEACHER"
            className="w-full sm:w-auto px-7 py-3 text-[15px] font-semibold text-slate-700 hover:text-purple-700 border border-slate-300 hover:border-purple-300 bg-white rounded-full transition-colors flex items-center justify-center gap-2"
          >
            <GraduationCap className="w-4.5 h-4.5" />
            <span>I teach a class</span>
          </Link>
        </div>
      </section>

      {/* Product vignette — composed editor + verdict + standings */}
      <section className="max-w-5xl mx-auto px-6 pb-24 w-full">
        <div className="relative mx-auto max-w-3xl">
          {/* Editor card */}
          <div className="rounded-2xl bg-slate-900 shadow-2xl shadow-slate-900/20 ring-1 ring-slate-900/60 overflow-hidden text-left">
            <div className="flex items-center justify-between px-5 py-3 border-b border-white/5">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
                <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
                <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
              </div>
              <span className="text-[11px] font-mono text-slate-400">solution.py · Two Sum</span>
              <span className="text-[10px] font-semibold tracking-wider text-gold-400/90 uppercase">Hidden tests · 4</span>
            </div>
            <pre className="px-6 py-5 text-[13px] leading-6 font-mono overflow-x-auto">
              <code>
                <span className="text-slate-500">1  </span><span className="text-purple-300">def</span> <span className="text-sky-300">solve</span><span className="text-slate-300">(nums, target):</span>{'\n'}
                <span className="text-slate-500">2  </span><span className="text-slate-300">    seen = {'{}'}</span>{'\n'}
                <span className="text-slate-500">3  </span><span className="text-slate-300">    </span><span className="text-purple-300">for</span><span className="text-slate-300"> i, n </span><span className="text-purple-300">in</span><span className="text-slate-300"> </span><span className="text-sky-300">enumerate</span><span className="text-slate-300">(nums):</span>{'\n'}
                <span className="text-slate-500">4  </span><span className="text-slate-300">        </span><span className="text-purple-300">if</span><span className="text-slate-300"> target - n </span><span className="text-purple-300">in</span><span className="text-slate-300"> seen:</span>{'\n'}
                <span className="text-slate-500">5  </span><span className="text-slate-300">            </span><span className="text-purple-300">return</span><span className="text-slate-300"> seen[target - n], i</span>{'\n'}
                <span className="text-slate-500">6  </span><span className="text-slate-300">        seen[n] = i</span>
              </code>
            </pre>
          </div>

          {/* Verdict chip */}
          <div className="absolute -bottom-6 left-4 sm:left-10 flex items-center gap-2.5 bg-white rounded-xl shadow-lg shadow-slate-900/10 ring-1 ring-slate-200 px-4 py-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <div>
              <div className="text-[13px] font-semibold text-slate-900 leading-none">Accepted</div>
              <div className="text-[11px] text-slate-500 mt-1">4/4 tests · 0.067s · +130 pts</div>
            </div>
          </div>

          {/* Standings card */}
          <div className="absolute -bottom-10 right-4 sm:-right-8 w-52 bg-white rounded-xl shadow-lg shadow-slate-900/10 ring-1 ring-slate-200 px-4 py-3.5 text-left hidden sm:block">
            <div className="text-[10px] font-bold tracking-[0.14em] uppercase text-slate-400 mb-2">Class standings</div>
            {[
              ['1', 'A. Okafor', '460'],
              ['2', 'M. Chen', '415'],
              ['3', 'You', '390'],
            ].map(([rank, name, pts]) => (
              <div key={rank} className={`flex items-center justify-between py-1 text-[12px] ${name === 'You' ? 'font-semibold text-indigo-700' : 'text-slate-600'}`}>
                <span className="flex items-center gap-2">
                  <span className={`w-4 text-center font-display ${rank === '1' ? 'text-gold-600' : 'text-slate-400'}`}>{rank}</span>
                  {name}
                </span>
                <span className="font-mono">{pts}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features — hairline columns, no boxes */}
      <section className="border-t border-slate-200 bg-white/60">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-y-12 lg:gap-y-0 lg:divide-x lg:divide-slate-200">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <div key={title} className="lg:px-8 first:lg:pl-0 last:lg:pr-0">
                <Icon className="w-5 h-5 text-indigo-700 mb-4" strokeWidth={1.75} />
                <h3 className="font-semibold text-slate-900 text-[15px] mb-2">{title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <GraduationCap className="w-4 h-4 text-indigo-700" />
            <span className="font-display text-sm text-slate-700">Coder</span>
          </div>
          <p>© 2026 Coder — a smarter coding platform for every student and teacher.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
