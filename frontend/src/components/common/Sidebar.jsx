import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  School,
  Code2,
  PlusCircle,
  Sparkles,
  UserPlus,
  History,
  ClipboardList,
  BookOpen,
  GraduationCap,
  X
} from 'lucide-react';

export const Sidebar = ({ open = false, onClose = () => {} }) => {
  const { isTeacher } = useAuth();

  const teacherSections = [
    {
      label: 'Teaching',
      links: [
        { to: '/teacher', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/teacher/classrooms', label: 'My Classrooms', icon: School },
        { to: '/teacher/assignments', label: 'Assignments', icon: ClipboardList },
      ],
    },
    {
      label: 'Problem Bank',
      links: [
        { to: '/teacher/problems/create', label: 'Create Problem', icon: PlusCircle },
        { to: '/teacher/problems/ai-generate', label: 'AI Generator', icon: Sparkles },
      ],
    },
  ];

  const studentSections = [
    {
      label: 'My Campus',
      links: [
        { to: '/student', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/student/classrooms', label: 'Joined Classrooms', icon: School },
        { to: '/student/assignments', label: 'Assignments', icon: ClipboardList },
        { to: '/student/join', label: 'Join Classroom', icon: UserPlus },
      ],
    },
    {
      label: 'Practice',
      links: [
        { to: '/student/learn', label: 'Learning Paths', icon: BookOpen },
        { to: '/student/problems', label: 'Coding Problems', icon: Code2 },
        { to: '/student/submissions', label: 'Submission History', icon: History },
      ],
    },
  ];

  const sections = isTeacher ? teacherSections : studentSections;
  const activeClasses = isTeacher
    ? 'bg-purple-50 text-purple-800'
    : 'bg-indigo-50 text-indigo-800';
  const barColor = isTeacher ? 'bg-purple-600' : 'bg-indigo-700';

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Drawer on mobile, static column on desktop */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-white border-r border-slate-200 px-3 py-5 overflow-y-auto
          transform transition-transform duration-200 ease-out
          ${open ? 'translate-x-0' : '-translate-x-full'}
          lg:static lg:z-auto lg:w-64 lg:translate-x-0 lg:min-h-[calc(100vh-4rem)] lg:shrink-0 lg:transition-none`}
      >
        {/* Mobile-only drawer header */}
        <div className="flex items-center justify-between px-2 mb-5 lg:hidden">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-700 flex items-center justify-center">
              <GraduationCap className="w-4.5 h-4.5 text-gold-400" />
            </div>
            <span className="font-display font-semibold text-xl text-slate-900">Coder</span>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {sections.map((section) => (
          <div key={section.label} className="mb-6">
            <div className="px-3.5 mb-2 text-[11px] font-bold tracking-[0.14em] uppercase text-slate-400">
              {section.label}
            </div>
            <div className="space-y-0.5">
              {section.links.map((link) => {
                const Icon = link.icon;
                return (
                  <NavLink
                    key={link.to}
                    to={link.to}
                    end={link.to === '/teacher' || link.to === '/student'}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `relative flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm transition-colors ${
                        isActive
                          ? `${activeClasses} font-semibold`
                          : 'text-slate-600 font-medium hover:bg-slate-100 hover:text-slate-900'
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <span className={`absolute left-0 top-2 bottom-2 w-1 rounded-full ${barColor}`} />
                        )}
                        <Icon className="w-4 h-4 shrink-0" />
                        <span>{link.label}</span>
                      </>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </aside>
    </>
  );
};

export default Sidebar;
