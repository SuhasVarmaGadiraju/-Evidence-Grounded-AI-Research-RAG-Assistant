import React, { useState } from 'react';
import {
  Loader2,
  AlertCircle,
  Copy,
  Check,
  Sparkles
} from 'lucide-react';
import api from '../services/api';

export default function PromptBuilder() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [templateVersion, setTemplateVersion] = useState('rag_prompt_v1');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleBuildPrompt = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a query to build a prompt.');
      setResult(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/prompt/build', {
        query: query.trim(),
        top_k: parseInt(topK, 10) || 5,
        template_version: templateVersion
      });

      if (response.success) {
        setResult(response);
      } else {
        setError(response.message || 'Failed to build prompt.');
      }
    } catch (err) {
      console.error('Error building prompt:', err);
      setError(err.message || 'Failed to communicate with Prompt Builder endpoint.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!result?.prompt) return;
    navigator.clipboard.writeText(result.prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-main">Prompt Builder</h1>
        <p className="text-xs text-sub mt-1">
          Simulate context injection, prompt minification, token budget estimation, and SHA-256 template hashing.
        </p>
      </div>

      <div className="p-6 rounded-2xl border border-theme bg-card">
        <form onSubmit={handleBuildPrompt} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-custom font-mono mb-2">
              User Query String
            </label>
            <textarea
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter user research query string..."
              className="w-full p-3 rounded-xl border border-theme bg-input text-main placeholder-slate-400 text-xs sm:text-sm font-medium focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-sub mb-1">Max Evidence Chunks (Top-K):</label>
              <select
                value={topK}
                onChange={(e) => setTopK(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-theme bg-input text-main text-xs font-medium focus:outline-none"
              >
                <option value={3}>3 Chunks</option>
                <option value={5}>5 Chunks</option>
                <option value={10}>10 Chunks</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-sub mb-1">Prompt Template Version:</label>
              <select
                value={templateVersion}
                onChange={(e) => setTemplateVersion(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-theme bg-input text-main text-xs font-medium focus:outline-none"
              >
                <option value="rag_prompt_v1">RAG Prompt v1.0 (Grounded Citations)</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs shadow-sm transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              Build & Minify Prompt
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-500 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {/* Metadata Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="p-4 rounded-2xl border border-theme bg-card">
              <div className="text-sub">Total Characters</div>
              <div className="text-lg font-bold text-main">{result.metadata?.char_count || result.prompt?.length || 0}</div>
            </div>

            <div className="p-4 rounded-2xl border border-theme bg-card">
              <div className="text-sub">Est. Token Budget</div>
              <div className="text-lg font-bold font-mono text-brand-500">~{result.metadata?.estimated_tokens || 0} tks</div>
            </div>

            <div className="p-4 rounded-2xl border border-theme bg-card">
              <div className="text-sub">Included Chunks</div>
              <div className="text-lg font-bold text-emerald-500">{result.metadata?.chunk_count || 0}</div>
            </div>

            <div className="p-4 rounded-2xl border border-theme bg-card">
              <div className="text-sub">Build Latency</div>
              <div className="text-lg font-bold font-mono text-amber-500">
                {((result.metadata?.build_time_seconds || 0) * 1000).toFixed(1)} ms
              </div>
            </div>
          </div>

          {/* Rendered Output */}
          <div className="p-6 rounded-2xl border border-theme bg-card">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs font-bold font-mono uppercase tracking-wider text-muted-custom">
                Final Rendered Prompt Output
              </span>
              <button
                onClick={handleCopy}
                className="px-3 py-1.5 rounded-lg border border-theme bg-muted hover:bg-card text-xs font-semibold text-main flex items-center gap-1.5 transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied' : 'Copy Prompt'}
              </button>
            </div>

            <pre className="p-4 rounded-xl font-mono text-xs overflow-x-auto whitespace-pre-wrap leading-relaxed border border-theme bg-input text-main">
              {result.prompt}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
