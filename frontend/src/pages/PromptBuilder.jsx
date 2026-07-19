import React, { useState } from 'react';
import {
  FileCode,
  Clock,
  Layers,
  Loader2,
  AlertCircle,
  Copy,
  Check,
  AlignLeft,
  Binary,
  Cpu,
  FileText,
  Sparkles,
  ShieldCheck,
  Hash,
  Tag
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
      console.error('Error during prompt building:', err);
      setError(err.message || 'Failed to execute prompt builder request.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyPrompt = () => {
    if (!result?.prompt) return;
    navigator.clipboard.writeText(result.prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <FileCode className="w-6 h-6 text-brand-500" />
          Prompt Builder
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-xs mt-1">
          Production-ready Prompt Builder module. Converts Hybrid Retrieval & Cross-Encoder reranked evidence into structured prompts for downstream LLM inference.
        </p>
      </div>

      {/* Control Form Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
        <form onSubmit={handleBuildPrompt} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div className="md:col-span-2 space-y-1.5">
              <label htmlFor="query" className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                User Query
              </label>
              <input
                id="query"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter a research question to build prompt context..."
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950 px-3 py-2 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:border-brand-500 focus:outline-none transition-colors"
                disabled={loading}
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="topK" className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                Max Chunks (Top-K)
              </label>
              <input
                id="topK"
                type="number"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(e.target.value)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950 px-3 py-2 text-sm text-slate-800 dark:text-slate-200 focus:border-brand-500 focus:outline-none transition-colors"
                disabled={loading}
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="templateVersion" className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                Template Version
              </label>
              <select
                id="templateVersion"
                value={templateVersion}
                onChange={(e) => setTemplateVersion(e.target.value)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950 px-3 py-2 text-sm text-slate-800 dark:text-slate-200 focus:border-brand-500 focus:outline-none transition-colors cursor-pointer"
                disabled={loading}
              >
                <option value="rag_prompt_v1">rag_prompt_v1 (Default)</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center justify-center gap-2 px-6 py-2.5 bg-brand-600 hover:bg-brand-700 disabled:bg-brand-400 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors cursor-pointer disabled:cursor-not-allowed h-[40px]"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Building Prompt...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Build Prompt
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-800 dark:bg-red-950/20 dark:border-red-900/50 dark:text-red-300 rounded-xl flex items-center gap-2 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Output Dashboard */}
      {result && (
        <div className="space-y-6">
          {/* Metadata Sub-Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 p-3 rounded-xl text-xs text-slate-600 dark:text-slate-400">
            <div className="flex flex-wrap items-center gap-4">
              <span className="flex items-center gap-1 font-mono">
                <Hash className="w-3.5 h-3.5 text-brand-500" />
                Prompt Hash: <strong className="text-slate-800 dark:text-slate-200" title={result.prompt_hash}>{result.prompt_hash ? `${result.prompt_hash.substring(0, 16)}...` : 'N/A'}</strong>
              </span>
              <span className="flex items-center gap-1">
                <Tag className="w-3.5 h-3.5 text-indigo-500" />
                Prompt Ver: <strong className="text-slate-800 dark:text-slate-200">{result.prompt_version || '1.0.0'}</strong>
              </span>
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                Pipeline Ver: <strong className="text-slate-800 dark:text-slate-200">{result.pipeline_version || '1.0.0'}</strong>
              </span>
            </div>

            {result.validation?.warnings && result.validation.warnings.length > 0 && (
              <span className="bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 px-2 py-1 rounded border border-amber-200 dark:border-amber-900/50 text-[11px]">
                ⚠️ {result.validation.warnings[0]}
              </span>
            )}
          </div>

          {/* Metrics Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3.5 rounded-xl space-y-1">
              <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500 text-[11px] font-semibold uppercase tracking-wider">
                <AlignLeft className="w-3.5 h-3.5 text-brand-500" />
                Lines
              </div>
              <p className="text-lg font-bold text-slate-800 dark:text-slate-100 font-mono">
                {result.prompt_length}
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3.5 rounded-xl space-y-1">
              <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500 text-[11px] font-semibold uppercase tracking-wider">
                <Binary className="w-3.5 h-3.5 text-indigo-500" />
                Characters
              </div>
              <p className="text-lg font-bold text-slate-800 dark:text-slate-100 font-mono">
                {result.character_count.toLocaleString()}
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3.5 rounded-xl space-y-1">
              <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500 text-[11px] font-semibold uppercase tracking-wider">
                <Layers className="w-3.5 h-3.5 text-purple-500" />
                Chunks
              </div>
              <p className="text-lg font-bold text-slate-800 dark:text-slate-100 font-mono">
                {result.context_chunk_count}
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3.5 rounded-xl space-y-1">
              <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500 text-[11px] font-semibold uppercase tracking-wider">
                <Cpu className="w-3.5 h-3.5 text-amber-500" />
                Est. Tokens
              </div>
              <p className="text-lg font-bold text-slate-800 dark:text-slate-100 font-mono">
                ~{result.estimated_tokens.toLocaleString()}
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3.5 rounded-xl space-y-1">
              <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500 text-[11px] font-semibold uppercase tracking-wider">
                <FileCode className="w-3.5 h-3.5 text-emerald-500" />
                Template
              </div>
              <p className="text-sm font-bold text-slate-800 dark:text-slate-100 truncate" title={result.template_version}>
                {result.template_version}
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3.5 rounded-xl space-y-1">
              <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500 text-[11px] font-semibold uppercase tracking-wider">
                <Clock className="w-3.5 h-3.5 text-rose-500" />
                Latency
              </div>
              <p className="text-lg font-bold text-slate-800 dark:text-slate-100 font-mono">
                {result.pipeline_time_seconds.toFixed(4)}s
              </p>
            </div>
          </div>

          {/* Generated Prompt Code Container */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden">
            <div className="flex items-center justify-between px-6 py-3.5 bg-slate-50/80 dark:bg-slate-950/60 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-brand-500" />
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide">
                  Generated Prompt Output
                </span>
                {result.truncated && (
                  <span className="bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 text-[10px] font-semibold px-2 py-0.5 rounded">
                    Truncated
                  </span>
                )}
              </div>

              <button
                onClick={handleCopyPrompt}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded-lg transition-colors cursor-pointer"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-500" />
                    <span className="text-emerald-600 dark:text-emerald-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Prompt</span>
                  </>
                )}
              </button>
            </div>

            <div className="p-6 overflow-x-auto bg-slate-950 text-slate-100 font-mono text-xs leading-relaxed max-h-[500px] overflow-y-auto">
              <pre className="whitespace-pre-wrap">{result.prompt}</pre>
            </div>
          </div>

          {/* Included Evidence Chunks Details */}
          {result.results && result.results.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                <Layers className="w-4 h-4 text-brand-500" />
                Evidence Chunks Included in Prompt ({result.results.length})
              </h3>

              <div className="grid grid-cols-1 gap-3">
                {result.results.map((chunk, idx) => (
                  <div
                    key={chunk.chunk_id || idx}
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 rounded-xl space-y-2 shadow-sm text-xs"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800/60 pb-2">
                      <div className="flex items-center gap-2 font-semibold text-slate-700 dark:text-slate-300">
                        <span className="bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400 px-2 py-0.5 rounded font-mono text-[11px]">
                          Chunk #{idx + 1}
                        </span>
                        <span className="truncate max-w-[250px]" title={chunk.document_name}>
                          {chunk.document_name}
                        </span>
                        <span className="text-slate-400 dark:text-slate-500 font-normal">
                          (Page {chunk.page_number})
                        </span>
                      </div>

                      <div className="font-mono text-[10px] text-slate-400">
                        ID: {chunk.chunk_id}
                      </div>
                    </div>

                    <p className="text-slate-600 dark:text-slate-300 italic bg-slate-50/50 dark:bg-slate-950/40 p-2.5 rounded border border-slate-100 dark:border-slate-900 whitespace-pre-wrap">
                      "{chunk.text}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
