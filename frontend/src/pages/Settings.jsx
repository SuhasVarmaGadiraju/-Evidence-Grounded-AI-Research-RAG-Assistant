import React, { useState } from 'react';
import { Sliders, Cpu, Save, CheckCircle2 } from 'lucide-react';

export default function Settings() {
  const [chunkSize, setChunkSize] = useState(500);
  const [chunkOverlap, setChunkOverlap] = useState(50);
  const [embeddingModel, setEmbeddingModel] = useState('all-MiniLM-L6-v2');
  const [crossEncoder, setCrossEncoder] = useState('ms-marco-MiniLM-L-6-v2');
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-main">Settings</h1>
        <p className="text-xs text-sub mt-1">
          Manage chunking parameters, SentenceTransformer models, and Cross-Encoder model definitions.
        </p>
      </div>

      {saved && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          Settings configuration saved successfully.
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Card 1: Chunking Params */}
        <div className="p-6 rounded-2xl border border-theme bg-card space-y-4">
          <h3 className="font-bold text-sm flex items-center gap-2 text-brand-500">
            <Sliders className="w-4 h-4" />
            Text Chunking Parameters
          </h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-sub">Chunk Size (characters)</label>
              <input
                type="number"
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
                className="w-full border border-theme bg-input text-main rounded-xl px-3 py-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-sub">Chunk Overlap (characters)</label>
              <input
                type="number"
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(Number(e.target.value))}
                className="w-full border border-theme bg-input text-main rounded-xl px-3 py-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>
        </div>

        {/* Card 2: AI Models */}
        <div className="p-6 rounded-2xl border border-theme bg-card space-y-4">
          <h3 className="font-bold text-sm flex items-center gap-2 text-indigo-500">
            <Cpu className="w-4 h-4" />
            Vector & Reranker Models
          </h3>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-sub">SentenceTransformer Embedding Model</label>
              <select
                value={embeddingModel}
                onChange={(e) => setEmbeddingModel(e.target.value)}
                className="w-full border border-theme bg-input text-main rounded-xl px-3 py-2 text-xs font-medium focus:outline-none"
              >
                <option value="all-MiniLM-L6-v2">all-MiniLM-L6-v2 (384-dim, Fast)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-sub">Cross-Encoder Reranker Model</label>
              <select
                value={crossEncoder}
                onChange={(e) => setCrossEncoder(e.target.value)}
                className="w-full border border-theme bg-input text-main rounded-xl px-3 py-2 text-xs font-medium focus:outline-none"
              >
                <option value="ms-marco-MiniLM-L-6-v2">cross-encoder/ms-marco-MiniLM-L-6-v2</option>
              </select>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            className="px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs shadow-sm transition-all flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
}
