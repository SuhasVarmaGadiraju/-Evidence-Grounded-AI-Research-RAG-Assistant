import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Search,
  Sun,
  Moon,
  Bell,
  LogOut,
  ChevronDown,
  Menu,
  Settings,
  Activity,
  Command,
  BrainCircuit
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

export default function Header({ toggleMobileSidebar }) {
  const { isDark, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [globalSearch, setGlobalSearch] = useState('');

  // Keyboard shortcut indicator for search bar Focus
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('global-search-input')?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const notifications = [
    { id: 1, title: 'Document Ingest Completed', desc: 'Research PDF processed into 52 FAISS vectors', time: '5m ago' },
    { id: 2, title: 'RAGAS Audit Complete', desc: 'Overall quality score evaluated at 92.4%', time: '45m ago' },
  ];

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (globalSearch.trim()) {
      navigate(`/search/hybrid?q=${encodeURIComponent(globalSearch)}`);
      setGlobalSearch('');
    }
  };

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-theme bg-surface/90 backdrop-blur-md text-main transition-colors duration-200 shrink-0">
      <div className="h-full px-4 sm:px-6 flex items-center justify-between gap-4">
        {/* Left Mobile Trigger & Global Search */}
        <div className="flex items-center gap-3 flex-1 max-w-lg">
          <button
            onClick={toggleMobileSidebar}
            className="lg:hidden p-2 rounded-lg hover:bg-muted text-sub transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>

          <Link
            to="/dashboard"
            className="lg:hidden flex items-center gap-2 group cursor-pointer shrink-0"
            title="Go to Dashboard"
          >
            <div className="w-7 h-7 rounded-lg bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center text-white dark:text-zinc-900 font-bold shadow-xs shrink-0 transition-transform group-hover:scale-105">
              <BrainCircuit className="w-3.5 h-3.5" />
            </div>
            <span className="font-bold text-xs tracking-tight text-main group-hover:opacity-80 transition-opacity hidden sm:inline">Evidence AI</span>
          </Link>

          <form onSubmit={handleSearchSubmit} className="relative w-full hidden sm:block">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-custom" />
            <input
              id="global-search-input"
              type="text"
              value={globalSearch}
              onChange={(e) => setGlobalSearch(e.target.value)}
              placeholder="Search literature with Hybrid Vector + BM25 Fusion..."
              className="w-full pl-10 pr-12 py-2 rounded-xl text-xs font-medium border border-theme bg-input text-main placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none hidden md:flex items-center gap-0.5 text-[10px] font-mono text-muted-custom bg-muted px-1.5 py-0.5 rounded border border-theme">
              <Command className="w-2.5 h-2.5" />K
            </div>
          </form>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-2.5">
          {/* Status Indicator */}
          <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded-md text-[11px] font-mono font-medium bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            NVIDIA NIM Online
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg border border-theme hover:bg-muted text-sub transition-colors"
            title="Toggle Light/Dark Theme"
          >
            {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-zinc-600" />}
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => {
                setShowNotifications(!showNotifications);
                setShowProfileMenu(false);
              }}
              className="p-2 rounded-lg border border-theme hover:bg-muted text-sub transition-colors relative"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 rounded-xl border border-theme bg-surface shadow-xl p-3 z-50 animate-fade-in">
                <div className="flex justify-between items-center mb-2 pb-2 border-b border-theme">
                  <span className="font-bold text-xs uppercase tracking-wider text-main font-mono">Notifications</span>
                  <span className="text-[10px] text-indigo-500 hover:underline font-semibold cursor-pointer">Mark all read</span>
                </div>
                <div className="space-y-2">
                  {notifications.map((n) => (
                    <div key={n.id} className="p-2.5 rounded-lg bg-muted/60 border border-theme text-xs space-y-0.5">
                      <div className="font-semibold text-main">{n.title}</div>
                      <div className="text-sub">{n.desc}</div>
                      <div className="text-[10px] text-muted-custom pt-0.5 font-mono">{n.time}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Profile Dropdown */}
          <div className="relative">
            <button
              onClick={() => {
                setShowProfileMenu(!showProfileMenu);
                setShowNotifications(false);
              }}
              className="flex items-center gap-2 p-1 pl-2 rounded-lg border border-theme hover:bg-muted transition-colors"
            >
              <img
                src={user?.avatarUrl || `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.name || 'Researcher')}&background=18181b&color=ffffff`}
                alt="Avatar"
                className="w-6 h-6 rounded-md object-cover"
              />
              <div className="text-left hidden sm:block">
                <div className="text-xs font-semibold leading-tight text-main">{user?.name || 'Researcher'}</div>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-muted-custom pr-0.5" />
            </button>

            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-52 rounded-xl border border-theme bg-surface shadow-xl p-1.5 z-50 animate-fade-in">
                <div className="px-2.5 py-1.5 border-b border-theme mb-1">
                  <div className="font-semibold text-xs text-main">{user?.name}</div>
                  <div className="text-[11px] text-muted-custom truncate">{user?.email}</div>
                </div>

                <button
                  onClick={() => {
                    navigate('/settings');
                    setShowProfileMenu(false);
                  }}
                  className="w-full text-left px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center gap-2 text-sub hover:bg-muted hover:text-main transition-colors"
                >
                  <Settings className="w-3.5 h-3.5 text-muted-custom" />
                  Workspace Settings
                </button>

                <button
                  onClick={() => {
                    logout();
                    navigate('/login');
                  }}
                  className="w-full text-left px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center gap-2 text-rose-500 hover:bg-rose-500/10 transition-colors mt-0.5"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
