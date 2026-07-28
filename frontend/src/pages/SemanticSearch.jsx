import React, { useState } from 'react';
import { Search, Database, Loader2, AlertCircle } from 'lucide-react';
import api from '../services/api';
import CustomSelect from '../components/ui/CustomSelect';

export default function SemanticSearch() {
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
      const response = await api.post('/retrieval/search', {
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
        setError(response.message || "Semantic retrieval search failed.");
      }
    } catch (err) {
      console.error("Error during semantic search:", err);
      setError(err.message || "Failed to execute semantic search request.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-main">Semantic Search</h1>
        <p className="text-xs text-sub mt-1">
          Search vector similarity using 384-dimensional SentenceTransformer embeddings in FAISS IndexFlatIP store.
        </p>
      </div>

      <div className="p-5 rounded-xl border border-theme bg-card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-muted-custom font-mono mb-1.5">
              Semantic Vector Query
            </label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-custom" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter query for FAISS cosine similarity vector search..."
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-theme bg-input text-main placeholder-slate-400 text-xs sm:text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
              />
            </div>
          </div>

          <div className="flex justify-between items-center">
            <CustomSelect
              value={topK}
              onChange={(e) => setTopK(e.target.value)}
              options={[
                { value: 3, label: '3 Matches' },
                { value: 5, label: '5 Matches' },
                { value: 10, label: '10 Matches' },
              ]}
              size="sm"
            />

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-medium text-xs shadow-xs transition-all flex items-center gap-2"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Database className="w-3.5 h-3.5" />}
              Query FAISS Index
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

      {results && (
        <div className="space-y-3">
          <div className="flex justify-between items-center text-xs font-mono text-muted-custom px-1">
            <span>Retrieved {results.chunks.length} dense vector matches</span>
            <span>FAISS Latency: {(results.latency * 1000).toFixed(1)} ms</span>
          </div>

          {results.chunks.map((chunk, idx) => {
            const scoreVal = chunk.score || 0;
            const barWidth = Math.min(100, Math.max(5, scoreVal * 100));
            return (
              <div key={idx} className="p-4 rounded-xl border border-theme bg-card space-y-2">
                <div className="flex justify-between items-center border-b border-theme pb-2">
                  <span className="font-semibold text-xs text-main">{chunk.document_name} <span className="text-muted-custom font-normal font-mono">(Page {chunk.page_number})</span></span>
                  <span className="text-[10px] font-mono text-main bg-muted px-2 py-0.5 rounded border border-theme">
                    Cosine Similarity: {scoreVal.toFixed(4)}
                  </span>
                </div>
                <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-zinc-900 dark:bg-zinc-100 rounded-full transition-all duration-500" style={{ width: `${barWidth}%` }}></div>
                </div>
                <p className="text-xs text-sub italic leading-relaxed font-mono">"{chunk.text}"</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
