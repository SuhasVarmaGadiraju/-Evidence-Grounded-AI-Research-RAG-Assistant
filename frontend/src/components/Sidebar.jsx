import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, UploadCloud, FolderClosed, Settings, Terminal, Search, Sliders, Shuffle, ChevronsUp, FileCode, Award } from 'lucide-react';

export default function Sidebar() {
  const links = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'AI Chat', path: '/chat', icon: MessageSquare },
    { name: 'Upload', path: '/upload', icon: UploadCloud },
    { name: 'Documents', path: '/documents', icon: FolderClosed },
    { name: 'Query Test', path: '/query-test', icon: Terminal },
    { name: 'Semantic Search', path: '/semantic-search', icon: Search },
    { name: 'BM25 Search', path: '/bm25-search', icon: Sliders },
    { name: 'Hybrid Search', path: '/hybrid-search', icon: Shuffle },
    { name: 'Rerank Search', path: '/rerank-search', icon: ChevronsUp },
    { name: 'Prompt Builder', path: '/prompt-builder', icon: FileCode },
    { name: 'Evaluation', path: '/evaluation', icon: Award },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shrink-0 hidden md:block">
      <nav className="flex flex-col gap-1 p-4">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-colors cursor-pointer ${
                  isActive
                    ? 'bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-800 dark:hover:text-slate-200'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {link.name}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
