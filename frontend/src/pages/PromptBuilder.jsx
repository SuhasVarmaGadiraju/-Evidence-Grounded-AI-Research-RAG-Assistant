import React, { useState } from 'react';
import {
  Loader2,
  AlertCircle,
  Copy,
  Check,
  Sparkles,
  FileCode2,
  Hash
} from 'lucide-react';
import api from '../services/api';
import CustomSelect from '../components/ui/CustomSelect';
import { PROMPT_TEMPLATE_OPTIONS } from '../constants/promptTemplates';

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
        <h1 className="text-xl font-bold tracking-tight text-main">Prompt Builder</h1>
        <p className="text-xs text-sub mt-1">
          Simulate context injection, prompt minification, token budget estimation, and SHA-256 template hashing.
        </p>
      </div>

      <div className="p-5 rounded-xl border border-theme bg-card">
        <form onSubmit={handleBuildPrompt} className="space-y-4">
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-muted-custom font-mono mb-1.5">
              User Query String
            </label>
            <textarea
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter user research query string..."
              className="w-full p-3 rounded-lg border border-theme bg-input text-main placeholder-slate-400 text-xs sm:text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-sub mb-1">Max Evidence Chunks (Top-K):</label>
              <CustomSelect
                value={topK}
                onChange={(e) => setTopK(e.target.value)}
                size="compact"
                className="w-full"
                options={[
                  { value: 3, label: '3 Chunks' },
                  { value: 5, label: '5 Chunks' },
                  { value: 10, label: '10 Chunks' },
                ]}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-sub mb-1">Prompt Template Version:</label>
              <CustomSelect
                value={templateVersion}
                onChange={(e) => setTemplateVersion(e.target.value)}
                size="compact"
                className="w-full"
                options={PROMPT_TEMPLATE_OPTIONS}
              />
            </div>
          </div>

          <div className="flex justify-end pt-1">
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-medium text-xs shadow-xs transition-all disabled:opacity-50 flex items-center gap-2 cursor-pointer"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5 text-indigo-400" />}
              Build & Minify Prompt
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          {/* Metadata Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
            <div className="p-3.5 rounded-xl border border-theme bg-card">
              <div className="text-sub text-[11px]">Total Characters</div>
              <div className="text-base font-bold text-main">{result.character_count || result.metadata?.char_count || result.prompt?.length || 0}</div>
            </div>

            <div className="p-3.5 rounded-xl border border-theme bg-card">
              <div className="text-sub text-[11px]">Est. Token Budget</div>
              <div className="text-base font-bold font-mono text-main">~{result.estimated_tokens || result.metadata?.estimated_tokens || 0} tks</div>
            </div>

            <div className="p-3.5 rounded-xl border border-theme bg-card">
              <div className="text-sub text-[11px]">Included Chunks</div>
              <div className="text-base font-bold text-emerald-600 dark:text-emerald-400">{result.context_chunk_count ?? result.metadata?.chunk_count ?? 0}</div>
            </div>

            <div className="p-3.5 rounded-xl border border-theme bg-card">
              <div className="text-sub text-[11px]">Template Version</div>
              <div className="text-xs font-bold font-mono text-indigo-600 dark:text-indigo-400 truncate mt-0.5" title={result.template_version}>
                {result.template_version || templateVersion}
              </div>
            </div>

            <div className="col-span-2 sm:col-span-1 p-3.5 rounded-xl border border-theme bg-card">
              <div className="text-sub text-[11px]">SHA-256 Hash</div>
              <div className="text-xs font-bold font-mono text-muted-custom truncate mt-0.5" title={result.prompt_hash}>
                {result.prompt_hash ? result.prompt_hash.substring(0, 10) + '...' : 'N/A'}
              </div>
            </div>
          </div>

          {/* Rendered Output */}
          <div className="p-5 rounded-xl border border-theme bg-card">
            <div className="flex justify-between items-center mb-2.5">
              <span className="text-[11px] font-bold font-mono uppercase tracking-wider text-muted-custom flex items-center gap-1.5">
                <FileCode2 className="w-3.5 h-3.5 text-indigo-500" />
                Final Rendered Prompt Output ({result.template_version || templateVersion})
              </span>
              <button
                onClick={handleCopy}
                className="px-2.5 py-1 rounded-md border border-theme bg-muted hover:bg-card-hover text-xs font-medium text-main flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied' : 'Copy Prompt'}
              </button>
            </div>

            <pre className="p-3.5 rounded-lg font-mono text-xs overflow-x-auto whitespace-pre-wrap leading-relaxed border border-theme bg-muted/60 text-main select-all">
              {result.prompt}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
