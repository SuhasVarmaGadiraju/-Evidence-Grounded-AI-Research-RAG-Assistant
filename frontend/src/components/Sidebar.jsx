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
    <div className="flex flex-col h-full bg-surface text-main transition-colors duration-200">
      {/* Brand Header */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-theme">
        <Link to="/dashboard" className="flex items-center gap-3 overflow-hidden">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center shadow-md text-white shrink-0">
            <BrainCircuit className="w-5 h-5" />
          </div>
          {(!collapsed || mobileOpen) && (
            <div className="truncate">
              <span className="font-bold text-sm tracking-tight text-main">Evidence AI</span>
              <span className="block text-[10px] text-brand-500 font-mono leading-tight">Research Lab</span>
            </div>
          )}
        </Link>

        {/* Mobile Close Button */}
        {mobileOpen && (
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-sub hover:text-main hover:bg-muted transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navigationGroups.map((group, idx) => (
          <div key={idx}>
            {(!collapsed || mobileOpen) && (
              <div className="px-2 mb-2 text-[10px] font-bold uppercase tracking-wider text-muted-custom font-mono">
                {group.title}
              </div>
            )}

            <div className="space-y-1">
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  title={collapsed && !mobileOpen ? item.name : undefined}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center ${collapsed && !mobileOpen ? 'justify-center px-0 py-2.5' : 'justify-between px-3 py-2.5'} rounded-xl text-xs font-semibold transition-all ${
                      isActive
                        ? 'bg-brand-600 text-white shadow-sm'
                        : 'text-sub hover:text-main hover:bg-muted'
                    }`
                  }
                >
                  <div className="flex items-center gap-3">
                    <item.icon className="w-4 h-4 shrink-0" />
                    {(!collapsed || mobileOpen) && <span>{item.name}</span>}
                  </div>

                  {(!collapsed || mobileOpen) && item.badge && (
                    <span className="px-2 py-0.5 text-[10px] rounded-md font-mono bg-brand-500/10 text-brand-500 border border-brand-500/20">
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
          <div className="text-[11px] text-muted-custom font-mono">
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
      {/* Desktop Persistent / Collapsible Sidebar */}
      <aside className={`hidden lg:block ${collapsed ? 'w-16' : 'w-64'} border-r border-theme bg-surface transition-all duration-300 flex-shrink-0`}>
        {content}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          ></div>
          <div className="relative w-64 bg-surface border-r border-theme shadow-2xl flex-1">
            {content}
          </div>
        </div>
      )}
    </>
  );
}
