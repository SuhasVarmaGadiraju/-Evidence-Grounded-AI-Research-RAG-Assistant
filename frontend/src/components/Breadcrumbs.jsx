import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

const pathNameMap = {
  dashboard: 'Dashboard',
  chat: 'AI Chat',
  upload: 'Upload Documents',
  documents: 'Documents',
  'search/hybrid': 'Hybrid Search',
  'search/rerank': 'Rerank Search',
  'search/semantic': 'Semantic Search',
  'search/bm25': 'BM25 Search',
  'prompt-builder': 'Prompt Builder',
  evaluation: 'Evaluation',
  settings: 'Settings',
};

export default function Breadcrumbs() {
  const location = useLocation();
  const currentPath = location.pathname.replace(/^\//, '');
  const pageTitle = pathNameMap[currentPath] || 'Dashboard';

  return (
    <div className="px-6 py-2.5 border-b border-theme bg-surface text-sub text-xs font-medium flex items-center gap-2 transition-colors duration-200">
      <Link to="/dashboard" className="hover:text-brand-500 flex items-center gap-1">
        <Home className="w-3.5 h-3.5" />
        Workspace
      </Link>
      <ChevronRight className="w-3.5 h-3.5 text-muted-custom" />
      <span className="font-semibold text-main">{pageTitle}</span>
    </div>
  );
}
