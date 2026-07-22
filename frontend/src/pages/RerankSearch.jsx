import React, { useState } from 'react';
import { Search, Cpu, Loader2, AlertCircle } from 'lucide-react';
import api from '../services/api';

export default function RerankSearch() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await api.post('/retrieval/rerank', {
        query: query.trim(),
        top_k: parseInt(topK, 10) || 5
      });

      if (response.success) {
        setResults({
          query: response.query,
          topK: response.top_k,
          latency: response.rerank_time_seconds,
          chunks: response.results || []
        });
      } else {
        setError(response.message || "Cross-Encoder reranking failed.");
      }
    } catch (err) {
      console.error("Error during rerank search:", err);
      setError(err.message || "Failed to execute rerank search request.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-main">Rerank Search</h1>
        <p className="text-xs text-sub mt-1">
          Re-scores candidate evidence blocks using `cross-encoder/ms-marco-MiniLM-L-6-v2` for precise relevance ranking.
        </p>
      </div>

      <div className="p-6 rounded-2xl border border-theme bg-card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-custom font-mono mb-2">
              Cross-Encoder Query Input
            </label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-custom" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter query to evaluate Cross-Encoder candidate re-ranking..."
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-theme bg-input text-main placeholder-slate-400 text-xs sm:text-sm font-medium focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all"
              />
            </div>
          </div>

          <div className="flex justify-between items-center">
            <select
              value={topK}
              onChange={(e) => setTopK(e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-theme bg-input text-main text-xs font-medium focus:outline-none"
            >
              <option value={3}>Top 3 Reranked</option>
              <option value={5}>Top 5 Reranked</option>
              <option value={10}>Top 10 Reranked</option>
            </select>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs shadow-sm transition-all flex items-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Cpu className="w-4 h-4" />}
              Run Rerank Search
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

      {results && (
        <div className="space-y-3">
          <div className="flex justify-between items-center text-xs font-mono text-muted-custom px-1">
            <span>Reranked {results.chunks.length} top candidates</span>
            <span>Inference Latency: {(results.latency * 1000).toFixed(1)} ms</span>
          </div>

          {results.chunks.map((chunk, idx) => {
            const scoreVal = chunk.rerank_score || 0;
            const normScore = (scoreVal + 10) / 20; // Normalizing cross-encoder logits roughly to 0-1
            const barWidth = Math.min(100, Math.max(5, normScore * 100));
            return (
              <div key={idx} className="p-4 rounded-2xl border border-theme bg-card space-y-2">
                <div className="flex justify-between items-center border-b border-theme pb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded bg-purple-500/10 text-purple-500 text-xs font-bold flex items-center justify-center font-mono">
                      #{chunk.rank || idx + 1}
                    </span>
                    <span className="font-bold text-xs text-main">{chunk.document_name} (Page {chunk.page_number})</span>
                  </div>
                  <span className="text-[10px] font-mono text-purple-500 bg-muted px-2 py-0.5 rounded border border-theme">
                    Rerank Score: {scoreVal.toFixed(4)}
                  </span>
                </div>
                <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-purple-500 rounded-full transition-all duration-500" style={{ width: `${barWidth}%` }}></div>
                </div>
                <p className="text-xs text-sub italic">"{chunk.text}"</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
