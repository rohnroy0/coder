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
  BookOpen
} from 'lucide-react';

export const Sidebar = () => {
  const { isTeacher } = useAuth();

  const teacherLinks = [
    { to: '/teacher', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/teacher/classrooms', label: 'My Classrooms', icon: School },
    { to: '/teacher/assignments', label: 'Assignments', icon: ClipboardList },
    { to: '/teacher/problems/create', label: 'Create Problem', icon: PlusCircle },
    { to: '/teacher/problems/ai-generate', label: 'AI Generator', icon: Sparkles },
  ];

  const studentLinks = [
    { to: '/student', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/student/classrooms', label: 'Joined Classrooms', icon: School },
    { to: '/student/assignments', label: 'Assignments', icon: ClipboardList },
    { to: '/student/join', label: 'Join Classroom', icon: UserPlus },
    { to: '/student/learn', label: 'Learning Paths', icon: BookOpen },
    { to: '/student/problems', label: 'Coding Problems', icon: Code2 },
    { to: '/student/submissions', label: 'Submission History', icon: History },
  ];

  const links = isTeacher ? teacherLinks : studentLinks;

  return (
    <aside className="w-64 bg-white border-r border-slate-200 min-h-[calc(100vh-4rem)] p-4 shrink-0">
      <div className="space-y-1">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/teacher' || link.to === '/student'}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700 font-semibold'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{link.label}</span>
            </NavLink>
          );
        })}
      </div>
    </aside>
  );
};

export default Sidebar;
