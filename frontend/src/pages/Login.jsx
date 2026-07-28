import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { BrainCircuit, Mail, Lock, Eye, EyeOff, ArrowRight, ShieldCheck, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import CustomCheckbox from '../components/ui/CustomCheckbox';

export default function Login() {
  const { login, loading } = useAuth();
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim() || !password.trim()) {
      setError('Please enter both email address and password.');
      return;
    }

    try {
      const res = await login(email, password, remember);
      if (res.success) {
        navigate(from, { replace: true });
      }
    } catch (err) {
      setError('Failed to authenticate. Please verify your credentials.');
    }
  };

  return (
    <div className={`min-h-screen flex ${isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-faf9f6 text-zinc-900'}`}>
      {/* Left Visual Branding Panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-zinc-900 p-12 flex-col justify-between relative overflow-hidden text-white border-r border-zinc-800">
        <div>
          <Link to={isAuthenticated ? "/dashboard" : "/"} className="flex items-center gap-2.5 group cursor-pointer" title="Go to Dashboard">
            <div className="w-8 h-8 rounded-lg bg-zinc-100 flex items-center justify-center text-zinc-900 font-bold shadow-xs">
              <BrainCircuit className="w-4 h-4" />
            </div>
            <span className="font-bold text-base tracking-tight">Evidence AI</span>
          </Link>
        </div>

        <div className="max-w-md my-auto space-y-4">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded font-mono text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-3.5 h-3.5" />
            Enterprise Evidence Research Platform
          </div>

          <h2 className="text-2xl font-bold tracking-tight leading-snug">
            Ground your AI Research with Verifiable Citations
          </h2>

          <ul className="mt-6 space-y-3 text-xs text-zinc-300 font-mono">
            <li className="flex items-center gap-2.5">
              <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Dense FAISS Embeddings + BM25 Reciprocal Rank Fusion</span>
            </li>
            <li className="flex items-center gap-2.5">
              <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>HuggingFace Cross-Encoder Candidate Reranking</span>
            </li>
            <li className="flex items-center gap-2.5">
              <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Automated RAGAS Faithfulness & Precision Quality Audit</span>
            </li>
          </ul>
        </div>

        <div className="text-[11px] font-mono text-zinc-500 border-t border-zinc-800/80 pt-6">
          Protected by Enterprise-grade AES-256 Encryption & NVIDIA Llama 3.1 Pipeline
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12">
        <div className="max-w-md w-full">
          <div className="text-center lg:text-left mb-8">
            <Link to={isAuthenticated ? "/dashboard" : "/"} className="inline-flex items-center gap-2 lg:hidden mb-6 group cursor-pointer">
              <div className="w-7 h-7 rounded bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center text-white dark:text-zinc-900 font-bold">
                <BrainCircuit className="w-4 h-4" />
              </div>
              <span className="font-bold text-base">Evidence AI</span>
            </Link>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-main">Welcome Back</h1>
            <p className={`mt-1 text-xs ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Sign in to access your research workspace and RAG pipeline.
            </p>
          </div>

          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-muted-custom font-mono mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-muted-custom">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="researcher@lab.org"
                  className={`w-full pl-9 pr-4 py-2.5 rounded-lg border text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all ${
                    isDark
                      ? 'bg-zinc-900 border-zinc-800 text-white placeholder-zinc-500'
                      : 'bg-white border-zinc-200 text-zinc-900 placeholder-zinc-400'
                  }`}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-[11px] font-bold uppercase tracking-wider text-muted-custom font-mono">
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs font-medium text-sub hover:text-main transition-colors"
                >
                  Forgot Password?
                </Link>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-muted-custom">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className={`w-full pl-9 pr-10 py-2.5 rounded-lg border text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all ${
                    isDark
                      ? 'bg-zinc-900 border-zinc-800 text-white placeholder-zinc-500'
                      : 'bg-white border-zinc-200 text-zinc-900 placeholder-zinc-400'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-muted-custom hover:text-main"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <CustomCheckbox
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                label="Remember session"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-medium text-xs shadow-xs transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white dark:border-zinc-900 border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <>
                  Sign In to Workspace
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-xs">
            <span className={isDark ? 'text-zinc-400' : 'text-zinc-600'}>Don't have a research workspace? </span>
            <Link to="/signup" className="font-semibold text-main hover:underline transition-colors">
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
