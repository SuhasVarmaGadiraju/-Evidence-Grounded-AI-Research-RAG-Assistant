import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, Layers, Loader2, AlertCircle } from 'lucide-react';
import api from '../services/api';
import CustomSelect from '../components/ui/CustomSelect';

export default function HybridSearch() {
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initialQuery = searchParams.get('q');
    if (initialQuery) {
      setQuery(initialQuery);
      executeSearch(initialQuery, 5);
    }
  }, [searchParams]);

  const executeSearch = async (searchQuery, kVal) => {
    if (!searchQuery.trim()) {
      setError("Please enter a search query.");
      setResults(null);
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    const parsedTopK = typeof kVal === 'object' ? parseInt(kVal?.target?.value || 5, 10) : parseInt(kVal || 5, 10);

    try {
      const response = await api.post('/retrieval/hybrid', {
        query: searchQuery.trim(),
        top_k: parsedTopK || 5
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

  const handleSubmit = (e) => {
    e.preventDefault();
    executeSearch(query, topK);
  };

  const handleTopKChange = (e) => {
    const val = e?.target?.value !== undefined ? e.target.value : e;
    setTopK(val);
  };

  const getSourceBadge = (source) => {
    switch (source) {
      case 'both':
        return (
          <span className="bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded font-mono text-[10px]">
            Both FAISS & BM25
          </span>
        );
      case 'bm25':
        return (
          <span className="bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded font-mono text-[10px]">
            BM25 Lexical
          </span>
        );
      case 'semantic':
      default:
        return (
          <span className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded font-mono text-[10px]">
            FAISS Semantic
          </span>
        );
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Title Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-main">
          Hybrid Search
        </h1>
        <p className="text-xs text-sub mt-1">
          Combines dense semantic FAISS vectors with sparse BM25 keyword matching via Reciprocal Rank Fusion (RRF).
        </p>
      </div>

      {/* Query Form Card */}
      <div className="p-5 rounded-xl border border-theme bg-card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-muted-custom font-mono mb-1.5">
              Hybrid Search Query
            </label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-custom" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Query technical concepts, e.g. RAG architecture, vector embeddings..."
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-theme bg-input text-main placeholder-slate-400 text-xs sm:text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
              />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center gap-2.5">
              <label className="text-xs font-medium text-sub">Top-K Matches:</label>
              <CustomSelect
                value={topK}
                onChange={handleTopKChange}
                options={[
                  { value: 3, label: '3 Matches' },
                  { value: 5, label: '5 Matches' },
                  { value: 10, label: '10 Matches' },
                ]}
                size="sm"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="w-full sm:w-auto px-4 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-medium text-xs shadow-xs transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Merging RRF...
                </>
              ) : (
                <>
                  <Layers className="w-3.5 h-3.5" />
                  Execute Hybrid Search
                </>
              )}
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

      {/* Results View */}
      {results && (
        <div className="space-y-3">
          <div className="flex justify-between items-center text-xs font-mono text-muted-custom px-1">
            <span>Retrieved {results.chunks.length} candidate passages</span>
            <span>RRF Latency: {(results.latency * 1000).toFixed(1)} ms</span>
          </div>

          <div className="space-y-3">
            {results.chunks.map((chunk, idx) => {
              const rrfVal = chunk.rrf_score || 0;
              const barWidth = Math.min(100, Math.max(10, rrfVal * 2500));
              return (
                <div
                  key={chunk.chunk_id || idx}
                  className="p-4.5 rounded-xl border border-theme bg-card space-y-2.5"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-theme pb-2">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded bg-muted text-main text-xs font-bold flex items-center justify-center font-mono border border-theme">
                        #{idx + 1}
                      </span>
                      <span className="font-semibold text-xs text-main">{chunk.document_name}</span>
                      <span className="text-[10px] text-muted-custom font-mono">Page {chunk.page_number}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {getSourceBadge(chunk.match_source)}
                      <span className="text-[10px] font-mono text-main bg-muted px-2 py-0.5 rounded border border-theme">
                        RRF Score: {rrfVal.toFixed(4)}
                      </span>
                    </div>
                  </div>

                  {/* RRF Visual Score Bar */}
                  <div className="space-y-1">
                    <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-zinc-900 dark:bg-zinc-100 rounded-full transition-all duration-500"
                        style={{ width: `${barWidth}%` }}
                      ></div>
                    </div>
                  </div>

                  <p className="text-xs text-sub italic leading-relaxed font-mono">"{chunk.text}"</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
