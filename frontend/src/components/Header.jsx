import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Command
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
    <header className="sticky top-0 z-30 h-16 border-b border-theme bg-surface/90 backdrop-blur-md text-main transition-colors duration-200">
      <div className="h-full px-4 sm:px-6 flex items-center justify-between gap-4">
        {/* Left Mobile Trigger & Global Search */}
        <div className="flex items-center gap-3 flex-1 max-w-lg">
          <button
            onClick={toggleMobileSidebar}
            className="lg:hidden p-2 rounded-lg hover:bg-muted text-sub transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>

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
        <div className="flex items-center gap-3">
          {/* Status Indicator */}
          <div className="hidden xl:flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 border border-emerald-500/20 text-emerald-500">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            NVIDIA Llama-3.1 Active
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl border border-theme hover:bg-muted text-sub transition-colors"
            title="Toggle Light/Dark Theme"
          >
            {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => {
                setShowNotifications(!showNotifications);
                setShowProfileMenu(false);
              }}
              className="p-2 rounded-xl border border-theme hover:bg-muted text-sub transition-colors relative"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-500"></span>
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 rounded-2xl border border-theme bg-surface shadow-2xl p-4 z-50 animate-fade-in">
                <div className="flex justify-between items-center mb-3 pb-2 border-b border-theme">
                  <span className="font-bold text-xs uppercase tracking-wider text-main font-mono">Notifications</span>
                  <span className="text-[10px] text-brand-500 font-semibold cursor-pointer">Mark all read</span>
                </div>
                <div className="space-y-2.5">
                  {notifications.map((n) => (
                    <div key={n.id} className="p-2.5 rounded-xl bg-muted border border-theme text-xs space-y-0.5">
                      <div className="font-semibold text-brand-500">{n.title}</div>
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
              className="flex items-center gap-2.5 p-1.5 pl-2.5 rounded-xl border border-theme hover:bg-muted transition-colors"
            >
              <img
                src={user?.avatarUrl || `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.name || 'Researcher')}`}
                alt="Avatar"
                className="w-7 h-7 rounded-lg object-cover"
              />
              <div className="text-left hidden sm:block">
                <div className="text-xs font-bold leading-tight text-main">{user?.name || 'Researcher'}</div>
                <div className="text-[10px] text-muted-custom leading-tight">{user?.role || 'Principal Researcher'}</div>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-muted-custom" />
            </button>

            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-theme bg-surface shadow-2xl p-2 z-50 animate-fade-in">
                <div className="px-3 py-2 border-b border-theme mb-1">
                  <div className="font-bold text-xs text-main">{user?.name}</div>
                  <div className="text-[11px] text-muted-custom">{user?.email}</div>
                </div>

                <button
                  onClick={() => {
                    navigate('/settings');
                    setShowProfileMenu(false);
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-2 text-sub hover:bg-muted hover:text-main transition-colors"
                >
                  <Settings className="w-4 h-4 text-brand-500" />
                  Workspace Settings
                </button>

                <button
                  onClick={() => {
                    logout();
                    navigate('/login');
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-2 text-red-500 hover:bg-red-500/10 transition-colors mt-1"
                >
                  <LogOut className="w-4 h-4" />
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
