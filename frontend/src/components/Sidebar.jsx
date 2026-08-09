import React, { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  BrainCircuit,
  LayoutDashboard,
  Upload,
  FileText,
  MessageSquare,
  Search,
  Layers,
  Sparkles,
  BarChart3,
  Settings,
  Cpu,
  ChevronLeft,
  ChevronRight,
  X
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export default function Sidebar({ mobileOpen, setMobileOpen, collapsed, setCollapsed }) {
  const { isDark } = useTheme();

  const navigationGroups = [
    {
      title: 'Command Center',
      items: [
        { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
        { name: 'AI Chat', path: '/chat', icon: MessageSquare, badge: 'Grounded' },
      ],
    },
    {
      title: 'Document Ingestion',
      items: [
        { name: 'Upload Documents', path: '/upload', icon: Upload },
        { name: 'Documents', path: '/documents', icon: FileText },
      ],
    },
    {
      title: 'Research & Retrieval',
      items: [
        { name: 'Hybrid Search', path: '/search/hybrid', icon: Layers },
        { name: 'Rerank Search', path: '/search/rerank', icon: Cpu },
        { name: 'Semantic Search', path: '/search/semantic', icon: Search },
        { name: 'BM25 Search', path: '/search/bm25', icon: Search },
      ],
    },
    {
      title: 'Intelligence & Audit',
      items: [
        { name: 'Prompt Builder', path: '/prompt-builder', icon: Sparkles },
        { name: 'Evaluation', path: '/evaluation', icon: BarChart3, badge: 'Audit' },
        { name: 'Settings', path: '/settings', icon: Settings },
      ],
    },
  ];

  const content = (
    <div className="flex flex-col h-full bg-sidebar text-main transition-colors duration-200">
      {/* Brand Header */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-theme">
        <Link
          to="/dashboard"
          onClick={() => setMobileOpen(false)}
          className="flex items-center gap-3 overflow-hidden group cursor-pointer select-none"
          title="Go to Dashboard"
        >
          <div className="w-8 h-8 rounded-lg bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center text-white dark:text-zinc-900 font-bold shadow-sm shrink-0 transition-transform group-hover:scale-105">
            <BrainCircuit className="w-4 h-4" />
          </div>
          {(!collapsed || mobileOpen) && (
            <div className="truncate">
              <span className="font-bold text-xs tracking-tight text-main block group-hover:opacity-80 transition-opacity">Evidence AI</span>
              <span className="block text-[10px] text-muted-custom font-mono leading-tight">Research Platform</span>
            </div>
          )}
        </Link>

        {/* Mobile Close Button */}
        {mobileOpen && (
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-sub hover:text-main hover:bg-muted transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {navigationGroups.map((group, idx) => (
          <div key={idx}>
            {(!collapsed || mobileOpen) && (
              <div className="px-2 mb-1.5 text-[10px] font-bold uppercase tracking-wider text-muted-custom font-mono">
                {group.title}
              </div>
            )}

            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  title={collapsed && !mobileOpen ? item.name : undefined}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center ${collapsed && !mobileOpen ? 'justify-center px-0 py-2' : 'justify-between px-2.5 py-2'} rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 font-semibold shadow-xs'
                        : 'text-sub hover:text-main hover:bg-card-hover'
                    }`
                  }
                >
                  <div className="flex items-center gap-2.5">
                    <item.icon className="w-4 h-4 shrink-0" />
                    {(!collapsed || mobileOpen) && <span>{item.name}</span>}
                  </div>

                  {(!collapsed || mobileOpen) && item.badge && (
                    <span className="px-1.5 py-0.5 text-[10px] rounded font-mono bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Footer Info / Collapse Toggle */}
      <div className="p-3 border-t border-theme flex items-center justify-between">
        {(!collapsed || mobileOpen) && (
          <div className="flex items-center gap-2 text-[11px] text-muted-custom font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            NVIDIA Llama 3.1 8B
          </div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden lg:flex p-1.5 rounded-lg text-sub hover:text-main hover:bg-muted transition-colors mx-auto"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent / Collapsible Fixed Sidebar */}
      <aside className={`hidden lg:flex flex-col h-full ${collapsed ? 'w-16' : 'w-64'} border-r border-theme bg-sidebar transition-all duration-300 shrink-0 z-20`}>
        {content}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          ></div>
          <div className="relative w-64 h-full bg-sidebar border-r border-theme shadow-2xl flex-1 z-50">
            {content}
          </div>
        </div>
      )}
    </>
  );
}
