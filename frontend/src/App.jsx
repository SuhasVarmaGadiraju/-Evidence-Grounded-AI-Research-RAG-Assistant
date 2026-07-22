import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Loader2 } from 'lucide-react';

// Layout & Route Guard
import AppLayout from './components/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';

// Lazy Loaded Page Components for optimal bundle performance
const LandingPage = lazy(() => import('./pages/LandingPage'));
const Login = lazy(() => import('./pages/Login'));
const SignUp = lazy(() => import('./pages/SignUp'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));

const Home = lazy(() => import('./pages/Home'));
const Chat = lazy(() => import('./pages/Chat'));
const Upload = lazy(() => import('./pages/Upload'));
const Documents = lazy(() => import('./pages/Documents'));
const SemanticSearch = lazy(() => import('./pages/SemanticSearch'));
const BM25Search = lazy(() => import('./pages/BM25Search'));
const HybridSearch = lazy(() => import('./pages/HybridSearch'));
const RerankSearch = lazy(() => import('./pages/RerankSearch'));
const PromptBuilder = lazy(() => import('./pages/PromptBuilder'));
const Evaluation = lazy(() => import('./pages/Evaluation'));
const Settings = lazy(() => import('./pages/Settings'));

// Loading Fallback Skeleton Component
function PageSkeleton() {
  return (
    <div className="py-20 flex flex-col items-center justify-center space-y-3">
      <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      <p className="text-xs font-mono text-muted-custom">Loading workspace component...</p>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<PageSkeleton />}>
            <Routes>
              {/* 1. Public Unauthenticated Routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<SignUp />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />

              {/* 2. Authenticated Protected SaaS Routes */}
              <Route
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              >
                <Route path="/dashboard" element={<Home />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/documents" element={<Documents />} />

                {/* Search Diagnostics */}
                <Route path="/search/hybrid" element={<HybridSearch />} />
                <Route path="/search/rerank" element={<RerankSearch />} />
                <Route path="/search/semantic" element={<SemanticSearch />} />
                <Route path="/search/bm25" element={<BM25Search />} />

                {/* Legacy search route aliases */}
                <Route path="/hybrid-search" element={<Navigate to="/search/hybrid" replace />} />
                <Route path="/rerank-search" element={<Navigate to="/search/rerank" replace />} />
                <Route path="/semantic-search" element={<Navigate to="/search/semantic" replace />} />
                <Route path="/bm25-search" element={<Navigate to="/search/bm25" replace />} />

                {/* Intelligence Studio & Audit */}
                <Route path="/prompt-builder" element={<PromptBuilder />} />
                <Route path="/evaluation" element={<Evaluation />} />
                <Route path="/settings" element={<Settings />} />
              </Route>

              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
