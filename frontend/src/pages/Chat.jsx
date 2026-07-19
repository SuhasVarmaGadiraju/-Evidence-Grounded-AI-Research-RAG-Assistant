import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Send,
  Loader2,
  AlertCircle,
  Copy,
  Check,
  RotateCcw,
  BookOpen,
  FileText,
  Clock,
  Cpu,
  Hash,
  Layers,
  Zap,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import api from '../services/api';

export default function Chat() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState('');
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [showDevTiming, setShowDevTiming] = useState(false);

  const answerRef = useRef(null);

  useEffect(() => {
    if (response && answerRef.current) {
      answerRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [response]);

  const executeQuery = async (searchQuery) => {
    if (!searchQuery.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResponse(null);
    setStage('Searching Documents & Vector Index...');

    // Simulate progress stage milestones for smooth UX
    const stageTimer1 = setTimeout(() => {
      setStage('Reranking Candidates via Cross-Encoder...');
    }, 600);

    const stageTimer2 = setTimeout(() => {
      setStage('Building & Minifying Prompt...');
    }, 1200);

    const stageTimer3 = setTimeout(() => {
      setStage('Generating Evidence-Grounded Answer via LLM...');
    }, 1800);

    try {
      const data = await api.post('/chat', {
        query: searchQuery.trim(),
        top_k: 5
      });

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);

      if (data.success) {
        setResponse(data);
      } else {
        setError(data.message || 'Failed to generate response.');
      }
    } catch (err) {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);
      console.error('Error in chat request:', err);
      setError(err.message || 'Failed to communicate with RAG AI Chat backend.');
    } finally {
      setLoading(false);
      setStage('');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    executeQuery(query);
  };

  const handleRetry = () => {
    if (query) {
      executeQuery(query);
    }
  };

  const handleCopy = () => {
    if (!response?.answer) return;
    navigator.clipboard.writeText(response.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderSimpleMarkdown = (text) => {
    if (!text) return null;

    const lines = text.split('\n');
    return lines.map((line, idx) => {
      let trimmed = line.trim();
      if (trimmed.startsWith('### ')) {
        return (
          <h3 key={idx} className="text-base font-bold text-slate-800 dark:text-slate-100 mt-3 mb-1">
            {trimmed.replace(/^###\s+/, '')}
          </h3>
        );
      } else if (trimmed.startsWith('## ')) {
        return (
          <h2 key={idx} className="text-lg font-bold text-slate-800 dark:text-slate-100 mt-4 mb-1">
            {trimmed.replace(/^##\s+/, '')}
          </h2>
        );
      } else if (trimmed.startsWith('# ')) {
        return (
          <h1 key={idx} className="text-xl font-extrabold text-slate-800 dark:text-slate-100 mt-4 mb-2">
            {trimmed.replace(/^#\s+/, '')}
          </h1>
        );
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        return (
          <li key={idx} className="ml-4 list-disc text-slate-700 dark:text-slate-300 text-sm my-0.5">
            {trimmed.replace(/^[-*]\s+/, '')}
          </li>
        );
      } else if (trimmed === '') {
        return <div key={idx} className="h-2" />;
      } else {
        return (
          <p key={idx} className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed my-1">
            {trimmed}
          </p>
        );
      }
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-brand-500" />
          Evidence-Grounded AI Research Assistant
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-xs mt-1">
          Production-hardened RAG Generation Layer with Hybrid Retrieval, Cross-Encoder Reranking, and LLM Response Caching.
        </p>
      </div>

      {/* Query Form Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask any research question about your uploaded documents..."
            className="flex-1 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:border-brand-500 focus:outline-none transition-colors"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="flex items-center gap-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 disabled:bg-brand-400 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors cursor-pointer disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Thinking...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Send Query
              </>
            )}
          </button>
        </form>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-800 dark:bg-red-950/20 dark:border-red-900/50 dark:text-red-300 rounded-xl flex items-center gap-2 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading Progress State & Skeleton */}
      {loading && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 space-y-6 shadow-sm">
          <div className="text-center space-y-3">
            <Loader2 className="w-8 h-8 text-brand-500 animate-spin mx-auto" />
            <div className="space-y-1">
              <p className="font-semibold text-slate-800 dark:text-slate-200 text-sm">
                Generating Evidence-Grounded Answer...
              </p>
              <p className="text-xs text-brand-600 dark:text-brand-400 font-medium">
                {stage || 'Processing pipeline stages...'}
              </p>
            </div>
          </div>

          {/* Skeleton Pulse Rows */}
          <div className="space-y-2.5 pt-2">
            <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded animate-pulse w-5/6 mx-auto" />
            <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded animate-pulse w-4/6 mx-auto" />
            <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded animate-pulse w-3/4 mx-auto" />
          </div>
        </div>
      )}

      {/* Output Response Section */}
      {response && (
        <div ref={answerRef} className="space-y-6">
          {/* Metadata Metrics Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 p-3.5 rounded-xl text-xs text-slate-600 dark:text-slate-400">
            <div className="flex flex-wrap items-center gap-3">
              {/* Cache Status Badge */}
              {response.cache_hit ? (
                <span className="flex items-center gap-1 bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-semibold px-2 py-0.5 rounded text-[11px] border border-emerald-200 dark:border-emerald-800">
                  <Zap className="w-3 h-3 text-emerald-600" />
                  Cached Response
                </span>
              ) : (
                <span className="flex items-center gap-1 bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-semibold px-2 py-0.5 rounded text-[11px] border border-blue-200 dark:border-blue-800">
                  <Sparkles className="w-3 h-3 text-blue-500" />
                  Live Response
                </span>
              )}

              <span className="flex items-center gap-1 font-mono text-[11px]">
                <Layers className="w-3.5 h-3.5 text-brand-500" />
                ReqID: <strong className="text-slate-700 dark:text-slate-200" title={response.request_id}>{response.request_id ? `${response.request_id.substring(0, 10)}...` : 'N/A'}</strong>
              </span>

              <span className="flex items-center gap-1 font-medium">
                <Cpu className="w-3.5 h-3.5 text-indigo-500" />
                Model: <strong className="text-slate-700 dark:text-slate-200">{response.model}</strong>
              </span>

              <span className="flex items-center gap-1 font-medium">
                <Clock className="w-3.5 h-3.5 text-emerald-500" />
                Latency: <strong className="text-slate-700 dark:text-slate-200">{response.latency.toFixed(2)}s</strong>
              </span>

              <span className="flex items-center gap-1 font-mono text-[11px]">
                <Hash className="w-3.5 h-3.5 text-purple-500" />
                Tokens: <strong className="text-slate-700 dark:text-slate-200">{response.estimated_tokens} ({response.prompt_tokens || 0} in / {response.completion_tokens || 0} out)</strong>
              </span>
            </div>

            <div className="flex items-center gap-2">
              {response.timing_breakdown && (
                <button
                  onClick={() => setShowDevTiming(!showDevTiming)}
                  className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded transition-colors cursor-pointer"
                >
                  <span>Dev Timing</span>
                  {showDevTiming ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
              )}

              <button
                onClick={handleCopy}
                className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded transition-colors cursor-pointer"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-500" />
                    <span className="text-emerald-600 dark:text-emerald-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>Copy Answer</span>
                  </>
                )}
              </button>

              <button
                onClick={handleRetry}
                disabled={loading}
                className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded transition-colors cursor-pointer disabled:opacity-50"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Retry</span>
              </button>
            </div>
          </div>

          {/* Developer Timing Breakdown Drawer */}
          {showDevTiming && response.timing_breakdown && (
            <div className="bg-slate-900 text-slate-200 border border-slate-800 p-4 rounded-xl text-xs space-y-2 font-mono shadow-sm">
              <p className="font-bold text-brand-400 uppercase tracking-wide">Developer Latency Breakdown (seconds)</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] pt-1">
                {Object.entries(response.timing_breakdown).map(([k, v]) => (
                  <div key={k} className="bg-slate-950 p-2 rounded border border-slate-800 flex justify-between">
                    <span className="text-slate-400">{k}:</span>
                    <span className="font-bold text-slate-100">{typeof v === 'number' ? v.toFixed(4) : v}s</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Answer Card */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-brand-500" />
                Grounded AI Answer
              </span>
            </div>

            <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed">
              {renderSimpleMarkdown(response.answer)}
            </div>
          </div>

          {/* Citations & Evidence Drawer */}
          {response.citations && response.citations.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-brand-500" />
                Retrieved Source Citations ({response.citations.length})
              </h3>

              <div className="grid grid-cols-1 gap-3">
                {response.citations.map((cite, idx) => (
                  <div
                    key={cite.chunk_id || idx}
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 rounded-xl space-y-2 shadow-sm text-xs"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800/60 pb-2">
                      <div className="flex items-center gap-2 font-semibold text-slate-700 dark:text-slate-300">
                        <span className="bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400 px-2 py-0.5 rounded font-mono text-[11px]">
                          Citation #{idx + 1}
                        </span>
                        <span className="flex items-center gap-1">
                          <FileText className="w-3.5 h-3.5 text-brand-500" />
                          {cite.document_name}
                        </span>
                        <span className="text-slate-400 dark:text-slate-500 font-normal">
                          (Page {cite.page_number})
                        </span>
                      </div>

                      <div className="font-mono text-[10px] text-slate-400">
                        Chunk ID: {cite.chunk_id}
                      </div>
                    </div>

                    <p className="text-slate-600 dark:text-slate-300 italic bg-slate-50/50 dark:bg-slate-950/40 p-2.5 rounded border border-slate-100 dark:border-slate-900 whitespace-pre-wrap">
                      "{cite.text}"
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
