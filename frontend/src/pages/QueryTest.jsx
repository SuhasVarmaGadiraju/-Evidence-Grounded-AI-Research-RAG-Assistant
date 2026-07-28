import React, { useState } from 'react';
import { Terminal, Cpu, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import api from '../services/api';

export default function QueryTest() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleGenerateEmbedding = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError("Please enter a query to embed.");
      setResult(null);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.post('/query/embed', { query: query.trim() });
      if (response.success) {
        setResult({
          queryLength: response.query_length,
          dimension: response.embedding_dimension,
          processingTime: response.processing_time_seconds,
          message: response.message
        });
      } else {
        setError(response.message || "Failed to generate query embedding.");
      }
    } catch (err) {
      console.error("Error generating query embedding:", err);
      setError(err.message || "Failed to generate query embedding.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-main">
          Query Embedding Test Panel
        </h1>
        <p className="text-xs text-sub mt-1">
          Developer testing utility to validate the Query Embedding Service. Generates and normalizes vector query inputs.
        </p>
      </div>

      {/* Test Card */}
      <div className="p-5 rounded-xl border border-theme bg-card space-y-4">
        <form onSubmit={handleGenerateEmbedding} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="query" className="block text-[11px] font-bold uppercase tracking-wider text-muted-custom font-mono">
              User Search Query
            </label>
            <textarea
              id="query"
              rows="3"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search query or paragraph here (e.g. What is the impact of semantic chunking on search recall?)..."
              className="w-full rounded-lg border border-theme bg-input p-3 text-xs sm:text-sm text-main placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all resize-y min-h-[80px]"
              disabled={loading}
            />
          </div>

          <div className="flex justify-between items-center text-[10px] text-muted-custom font-mono">
            <span>Max character limit: 1000</span>
            <span>Current length: {query.length} chars</span>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 text-xs font-medium rounded-lg shadow-xs transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Generating Vector...
              </>
            ) : (
              'Generate Query Embedding'
            )}
          </button>
        </form>
      </div>

      {/* Success Result Display */}
      {result && (
        <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 space-y-3">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-xs font-bold font-mono">
            <CheckCircle className="w-4 h-4 shrink-0" />
            <span>Embedding Generated Successfully</span>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="bg-card border border-theme p-3 rounded-lg flex items-center gap-2.5">
              <Terminal className="w-4 h-4 text-muted-custom shrink-0" />
              <div>
                <span className="text-[10px] text-muted-custom block font-mono uppercase">Query Length</span>
                <span className="font-bold text-main font-mono">{result.queryLength} chars</span>
              </div>
            </div>

            <div className="bg-card border border-theme p-3 rounded-lg flex items-center gap-2.5">
              <Cpu className="w-4 h-4 text-muted-custom shrink-0" />
              <div>
                <span className="text-[10px] text-muted-custom block font-mono uppercase">Dimensions</span>
                <span className="font-bold text-main font-mono">{result.dimension}d</span>
              </div>
            </div>

            <div className="bg-card border border-theme p-3 rounded-lg flex items-center gap-2.5">
              <Clock className="w-4 h-4 text-muted-custom shrink-0" />
              <div>
                <span className="text-[10px] text-muted-custom block font-mono uppercase">Processing Time</span>
                <span className="font-bold text-main font-mono">{result.processingTime.toFixed(4)}s</span>
              </div>
            </div>
          </div>
          <p className="text-[10px] text-muted-custom italic font-mono">
            * Note: For privacy and performance, raw vector arrays are kept on the server and are not sent to the browser interface.
          </p>
        </div>
      )}

      {/* Error Result Display */}
      {error && (
        <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 text-rose-500 rounded-xl flex items-center gap-2 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
