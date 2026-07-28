import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { BrainCircuit, Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

export default function ForgotPassword() {
  const { isDark } = useTheme();
  const { isAuthenticated, resetPassword } = useAuth();
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!email.trim()) return;

    try {
      await resetPassword(email.trim());
      setSubmitted(true);
    } catch (err) {
      setError(err.message || 'Failed to send password reset email.');
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center p-6 ${isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-faf9f6 text-zinc-900'}`}>
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <Link to={isAuthenticated ? "/dashboard" : "/"} className="inline-flex items-center gap-2 mb-4 group cursor-pointer" title="Go to Dashboard">
            <div className="w-8 h-8 rounded-lg bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center text-white dark:text-zinc-900 font-bold shadow-xs">
              <BrainCircuit className="w-4 h-4" />
            </div>
            <span className="font-bold text-base tracking-tight text-main">Evidence AI</span>
          </Link>
          <h1 className="text-xl font-bold tracking-tight text-main">Reset your Password</h1>
          <p className={`mt-1 text-xs ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
            Enter your academic or organization email address to receive reset instructions.
          </p>
        </div>

        <div className={`p-6 rounded-xl border ${isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'}`}>
          {submitted ? (
            <div className="text-center py-2 space-y-3">
              <div className="w-10 h-10 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <h2 className="text-sm font-bold text-main">Check your inbox</h2>
              <p className={`text-xs ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                We have sent password reset instructions to <span className="font-mono font-semibold text-main">{email}</span>.
              </p>
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-main hover:underline pt-2"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Back to Login
              </Link>
            </div>
          ) : (
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
                        ? 'bg-zinc-950 border-zinc-800 text-white placeholder-zinc-500'
                        : 'bg-white border-zinc-200 text-zinc-900 placeholder-zinc-400'
                    }`}
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-medium text-xs shadow-xs transition-all"
              >
                Send Password Reset Link
              </button>

              <div className="text-center pt-1">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 text-xs font-medium text-sub hover:text-main transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Back to Login
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
