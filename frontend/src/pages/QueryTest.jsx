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
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <Terminal className="w-6 h-6 text-brand-500" />
          Query Embedding Test Panel
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-xs">
          Developer testing utility to validate the Query Embedding Service. Generates and normalizes vector query inputs.
        </p>
      </div>

      {/* Test Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <form onSubmit={handleGenerateEmbedding} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="query" className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              User Search Query
            </label>
            <textarea
              id="query"
              rows="3"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search query or paragraph here (e.g. What is the impact of semantic chunking on search recall?)..."
              className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950 p-3 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:border-brand-500 focus:outline-none transition-colors resize-y min-h-[80px]"
              disabled={loading}
            />
          </div>

          <div className="flex justify-between items-center text-[10px] text-slate-400 font-medium">
            <span>Max character limit: 1000</span>
            <span>Current length: {query.length} chars</span>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:bg-brand-400 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors cursor-pointer disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
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
        <div className="bg-emerald-50/30 dark:bg-emerald-950/10 border border-emerald-200 dark:border-emerald-900/50 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 text-sm font-bold">
            <CheckCircle className="w-5 h-5 shrink-0" />
            <span>Embedding Generated Successfully</span>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="bg-white dark:bg-slate-950 border border-slate-100 dark:border-slate-900 p-3 rounded-lg flex items-center gap-3">
              <Terminal className="w-5 h-5 text-indigo-500 shrink-0" />
              <div>
                <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">Query Length</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">{result.queryLength} chars</span>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-950 border border-slate-100 dark:border-slate-900 p-3 rounded-lg flex items-center gap-3">
              <Cpu className="w-5 h-5 text-indigo-500 shrink-0" />
              <div>
                <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">Dimensions</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">{result.dimension}d</span>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-950 border border-slate-100 dark:border-slate-900 p-3 rounded-lg flex items-center gap-3">
              <Clock className="w-5 h-5 text-indigo-500 shrink-0" />
              <div>
                <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">Processing Time</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">{result.processingTime.toFixed(4)}s</span>
              </div>
            </div>
          </div>
          <p className="text-[10px] text-slate-500 italic mt-2">
            * Note: For privacy and performance, raw vector arrays are kept on the server and are not sent to the browser interface.
          </p>
        </div>
      )}

      {/* Error Result Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-800 dark:bg-red-950/20 dark:border-red-900/50 dark:text-red-300 rounded-xl flex items-center gap-2 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
