import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';

export const TeacherLayout = () => {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar onMenuToggle={() => setMenuOpen((o) => !o)} />
      <div className="flex flex-1">
        <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
        <main className="flex-1 min-w-0 p-4 sm:p-6 overflow-y-auto max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default TeacherLayout;
