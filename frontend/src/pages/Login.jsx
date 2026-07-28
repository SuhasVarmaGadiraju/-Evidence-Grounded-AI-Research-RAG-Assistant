import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  BrainCircuit,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  Layers,
  Target,
  BarChart3,
  LockKeyhole
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import CustomCheckbox from '../components/ui/CustomCheckbox';

export default function Login() {
  const { login, loginWithGoogle, loading, isAuthenticated } = useAuth();
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
      setError(err.message || 'Failed to authenticate. Please verify your credentials.');
    }
  };

  const handleGoogleClick = async () => {
    setError('');
    try {
      const res = await loginWithGoogle();
      if (res.success) {
        navigate(from, { replace: true });
      }
    } catch (err) {
      setError(err.message || 'Google authentication failed.');
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-[#FAFAF8] dark:bg-[#111315] text-[#111827] dark:text-[#F9FAFB] transition-colors duration-200 selection:bg-emerald-500/20">
      {/* Left Section (Branding) ~45% width */}
      <div className="w-full lg:w-[45%] p-8 lg:p-12 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-[#E5E7EB] dark:border-[#2A2C31] bg-[#FAFAF8] dark:bg-[#111315] relative">
        
        {/* Top Header Logo */}
        <div>
          <Link
            to={isAuthenticated ? "/dashboard" : "/"}
            className="inline-flex items-center gap-3 group cursor-pointer"
            title="Go to Dashboard"
          >
            <div className="w-9 h-9 rounded-xl bg-[#111827] dark:bg-[#F9FAFB] flex items-center justify-center text-white dark:text-[#111827] font-bold shadow-xs transition-transform group-hover:scale-105">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight block text-[#111827] dark:text-[#F9FAFB] group-hover:opacity-80 transition-opacity">
                Evidence AI
              </span>
              <span className="block text-xs text-[#6B7280] dark:text-zinc-400 font-medium leading-tight">
                Research Platform
              </span>
            </div>
          </Link>
        </div>

        {/* Middle Content Stack */}
        <div className="my-8 lg:my-auto max-w-lg space-y-6">
          {/* Enterprise Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-4 h-4 text-[#10B981] shrink-0" />
            Enterprise Evidence Research Platform
          </div>

          {/* Main Heading */}
          <h1 className="text-3xl lg:text-[40px] font-extrabold tracking-tight text-[#111827] dark:text-[#F9FAFB] leading-[1.15]">
            AI-Powered Research.<br />
            Grounded in Evidence.
          </h1>

          {/* Short Description */}
          <p className="text-[15px] text-[#6B7280] dark:text-zinc-400 leading-relaxed font-normal">
            Empowering enterprise researchers and scientists with verifiable, citation-backed AI intelligence.
          </p>

          {/* Three Premium Feature Cards */}
          <div className="space-y-3.5 pt-1">
            {/* Card 1: Hybrid Search */}
            <div className="p-4 rounded-xl border border-[#E5E7EB] dark:border-[#2A2C31] bg-white dark:bg-[#1A1B1F] shadow-xs hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center shrink-0 text-emerald-600 dark:text-emerald-400">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-[15px] font-bold text-[#111827] dark:text-[#F9FAFB]">Hybrid Search</h3>
                <p className="text-xs text-[#6B7280] dark:text-zinc-400 mt-0.5">
                  Dense FAISS + BM25 Fusion for comprehensive results.
                </p>
              </div>
            </div>

            {/* Card 2: Cross-Encoder Reranking */}
            <div className="p-4 rounded-xl border border-[#E5E7EB] dark:border-[#2A2C31] bg-white dark:bg-[#1A1B1F] shadow-xs hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center shrink-0 text-emerald-600 dark:text-emerald-400">
                <Target className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-[15px] font-bold text-[#111827] dark:text-[#F9FAFB]">Cross-Encoder Reranking</h3>
                <p className="text-xs text-[#6B7280] dark:text-zinc-400 mt-0.5">
                  Precise evidence ranking for high-precision retrieval.
                </p>
              </div>
            </div>

            {/* Card 3: RAGAS Evaluation */}
            <div className="p-4 rounded-xl border border-[#E5E7EB] dark:border-[#2A2C31] bg-white dark:bg-[#1A1B1F] shadow-xs hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center shrink-0 text-emerald-600 dark:text-emerald-400">
                <BarChart3 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-[15px] font-bold text-[#111827] dark:text-[#F9FAFB]">RAGAS Evaluation</h3>
                <p className="text-xs text-[#6B7280] dark:text-zinc-400 mt-0.5">
                  Automatic quality benchmarking for context precision & faithfulness.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Footer */}
        <div className="pt-6 border-t border-[#E5E7EB] dark:border-[#2A2C31] text-xs text-[#6B7280] dark:text-zinc-400 flex items-center gap-2 font-medium">
          <LockKeyhole className="w-4 h-4 text-[#10B981] shrink-0" />
          <span>Enterprise-grade Security • AES-256 Encryption • Private Research Workspace</span>
        </div>
      </div>

      {/* Right Section (Authentication) ~55% width */}
      <div className="w-full lg:w-[55%] flex items-center justify-center p-6 sm:p-12 lg:p-16 bg-[#FAFAF8] dark:bg-[#111315]">
        
        {/* Centered Authentication Card */}
        <div className="w-full max-w-[460px] bg-white dark:bg-[#1A1B1F] border border-[#E5E7EB] dark:border-[#2A2C31] rounded-2xl p-7 sm:p-9 shadow-sm sm:shadow-md space-y-6">
          
          {/* Welcome Header */}
          <div>
            <h2 className="text-2xl sm:text-[28px] font-bold tracking-tight text-[#111827] dark:text-[#F9FAFB]">
              Welcome Back
            </h2>
            <p className="text-sm text-[#6B7280] dark:text-zinc-400 mt-1">
              Sign in to access your research workspace.
            </p>
          </div>

          {/* Google Authentication Button */}
          <div>
            <button
              type="button"
              onClick={handleGoogleClick}
              disabled={loading}
              className="w-full h-11 px-4 rounded-xl border border-[#E5E7EB] dark:border-[#2A2C31] bg-white dark:bg-[#111315] text-[#111827] dark:text-[#F9FAFB] font-medium text-sm shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800/40 transition-all flex items-center justify-center gap-3 cursor-pointer"
            >
              <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span>Continue with Google</span>
            </button>
          </div>

          {/* OR Divider */}
          <div className="relative flex items-center justify-center my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#E5E7EB] dark:border-[#2A2C31]" />
            </div>
            <div className="relative px-3 text-xs font-semibold uppercase tracking-wider text-[#6B7280] dark:text-zinc-400 bg-white dark:bg-[#1A1B1F]">
              OR
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs flex items-center gap-2 animate-fade-in">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0"></span>
              {error}
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Field */}
            <div>
              <label className="block text-[13px] font-semibold text-[#111827] dark:text-[#F9FAFB] mb-1.5">
                Email address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#6B7280]">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="w-full h-11 pl-10 pr-4 rounded-xl border border-[#E5E7EB] dark:border-[#2A2C31] bg-white dark:bg-[#111315] text-[#111827] dark:text-[#F9FAFB] text-sm placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-[#10B981]/20 focus:border-[#10B981] transition-all"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-[13px] font-semibold text-[#111827] dark:text-[#F9FAFB]">
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs font-semibold text-[#10B981] hover:underline transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#6B7280]">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full h-11 pl-10 pr-10 rounded-xl border border-[#E5E7EB] dark:border-[#2A2C31] bg-white dark:bg-[#111315] text-[#111827] dark:text-[#F9FAFB] text-sm placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-[#10B981]/20 focus:border-[#10B981] transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-[#6B7280] hover:text-[#111827] dark:hover:text-[#F9FAFB] transition-colors cursor-pointer"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between pt-0.5">
              <CustomCheckbox
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                label="Remember me"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full h-11 px-4 rounded-xl font-semibold text-sm shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer bg-[#111827] hover:bg-zinc-800 text-white dark:bg-[#F9FAFB] dark:hover:bg-zinc-200 dark:text-[#111827] ${
                loading ? 'opacity-70 cursor-not-allowed' : ''
              }`}
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white dark:border-[#111827] border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>Sign in to Workspace</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Bottom Account Switch Link */}
          <div className="text-center text-xs text-[#6B7280] dark:text-zinc-400 pt-2">
            <span>Don't have an account? </span>
            <Link to="/signup" className="font-semibold text-[#10B981] hover:underline transition-colors">
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
