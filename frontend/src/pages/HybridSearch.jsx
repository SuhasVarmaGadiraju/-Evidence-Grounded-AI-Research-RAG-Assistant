import React, { useState } from 'react';
import { Search, Hash, Clock, FileText, Layers, Loader2, AlertCircle, Shuffle } from 'lucide-react';
import api from '../services/api';

export default function HybridSearch() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError("Please enter a search query.");
      setResults(null);
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await api.post('/retrieval/hybrid', {
        query: query.trim(),
        top_k: parseInt(topK, 10) || 5
      });

      if (response.success) {
        setResults({
          query: response.query,
          topK: response.top_k,
          latency: response.retrieval_time_seconds,
          chunks: response.results || []
        });
      } else {
        setError(response.message || "Hybrid retrieval search failed.");
      }
    } catch (err) {
      console.error("Error during hybrid search:", err);
      setError(err.message || "Failed to execute hybrid search request.");
    } finally {
      setLoading(false);
    }
  };

  const getSourceBadge = (source) => {
    switch (source) {
      case 'both':
        return (
          <span className="bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded font-semibold text-[10px] uppercase tracking-wider">
            Semantic & BM25
          </span>
        );
      case 'bm25':
        return (
          <span className="bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 px-2 py-0.5 rounded font-semibold text-[10px] uppercase tracking-wider">
            BM25 Sparse
          </span>
        );
      case 'semantic':
      default:
        return (
          <span className="bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded font-semibold text-[10px] uppercase tracking-wider">
            Semantic Dense
          </span>
        );
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <Shuffle className="w-6 h-6 text-brand-500" />
          Hybrid Retrieval Tester
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-xs">
          Developer testing view to evaluate Reciprocal Rank Fusion (RRF) hybrid search. Merges semantic vectors and sparse BM25 token matches.
        </p>
      </div>

      {/* Control Form Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
        <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div className="md:col-span-2 space-y-1.5">
            <label htmlFor="query" className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              Search Query
            </label>
            <input
              id="query"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Type your hybrid search query here..."
              className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950 px-3 py-2 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:border-brand-500 focus:outline-none transition-colors"
              disabled={loading}
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="topK" className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              Retrieve Top-K
            </label>
            <input
              id="topK"
              type="number"
              min="1"
              max="50"
              value={topK}
              onChange={(e) => setTopK(e.target.value)}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950 px-3 py-2 text-sm text-slate-800 dark:text-slate-200 focus:border-brand-500 focus:outline-none transition-colors"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:bg-brand-400 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors cursor-pointer disabled:cursor-not-allowed h-[38px] w-full"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Run Search
              </>
            )}
          </button>
        </form>
      </div>

      {/* Latency and Stats Info */}
      {results && (
        <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400 py-1 px-2 bg-slate-50 dark:bg-slate-800/20 border border-slate-200 dark:border-slate-800 rounded-lg">
          <span className="flex items-center gap-1 font-medium">
            <Clock className="w-3.5 h-3.5 text-indigo-500" />
            Hybrid latency: <strong className="text-slate-700 dark:text-slate-200 font-bold">{results.latency.toFixed(4)}s</strong>
          </span>
          <span className="text-slate-300 dark:text-slate-700">|</span>
          <span className="flex items-center gap-1 font-medium">
            <Hash className="w-3.5 h-3.5 text-indigo-500" />
            Retrieved: <strong className="text-slate-700 dark:text-slate-200 font-bold">{results.chunks.length} chunks</strong>
          </span>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-800 dark:bg-red-950/20 dark:border-red-900/50 dark:text-red-300 rounded-xl flex items-center gap-2 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search Chunks Output List */}
      {results && results.chunks.length === 0 && (
        <div className="text-center py-16 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl space-y-2">
          <Search className="w-12 h-12 text-slate-300 mx-auto" />
          <p className="font-semibold text-slate-700 dark:text-slate-300">No matches found</p>
          <p className="text-xs text-slate-400">The query returned no hybrid matches. Ensure you have ingested documents in your library.</p>
        </div>
      )}

      {results && results.chunks.length > 0 && (
        <div className="space-y-4">
          {results.chunks.map((chunk) => (
            <div
              key={chunk.chunk_id}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-3 hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
            >
              {/* Header Info */}
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800/60 pb-2.5">
                <div className="flex flex-wrap items-center gap-3 text-xs">
                  <span className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded font-bold">
                    Rank {chunk.rank}
                  </span>

                  {getSourceBadge(chunk.match_source)}
                  
                  <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
                    <FileText className="w-3.5 h-3.5 text-brand-500 shrink-0" />
                    <span className="max-w-[200px] truncate font-medium" title={chunk.document_name}>
                      {chunk.document_name}
                    </span>
                  </span>

                  <span className="flex items-center gap-0.5 text-slate-400 dark:text-slate-500">
                    <Layers className="w-3.5 h-3.5 shrink-0" />
                    Page {chunk.page_number}
                  </span>
                </div>

                {/* Score */}
                <div className="flex items-center gap-1.5 text-xs font-semibold">
                  <span className="text-slate-400 dark:text-slate-500">RRF Score:</span>
                  <span className="text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/40 px-2.5 py-0.5 rounded-full font-bold">
                    {chunk.score.toFixed(6)}
                  </span>
                </div>
              </div>

              {/* Text Preview */}
              <div className="bg-slate-50/50 dark:bg-slate-950/30 p-3 rounded-lg border border-slate-100 dark:border-slate-900">
                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed italic whitespace-pre-wrap">
                  "{chunk.text}"
                </p>
              </div>

              {/* Chunk ID */}
              <div className="text-[10px] text-slate-400 dark:text-slate-500 font-mono truncate">
                {chunk.chunk_id}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
