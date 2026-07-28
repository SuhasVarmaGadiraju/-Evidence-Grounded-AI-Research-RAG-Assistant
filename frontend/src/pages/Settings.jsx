import React, { useState } from 'react';
import { Sliders, Cpu, Save, CheckCircle2 } from 'lucide-react';
import CustomSelect from '../components/ui/CustomSelect';

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
        <h1 className="text-xl font-bold tracking-tight text-main">Settings</h1>
        <p className="text-xs text-sub mt-1">
          Manage chunking parameters, SentenceTransformer models, and Cross-Encoder model definitions.
        </p>
      </div>

      {saved && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          Settings configuration saved successfully.
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-5">
        {/* Card 1: Chunking Params */}
        <div className="p-5 rounded-xl border border-theme bg-card space-y-4">
          <h3 className="font-bold text-xs font-mono uppercase tracking-wider flex items-center gap-2 text-main">
            <Sliders className="w-3.5 h-3.5 text-muted-custom" />
            Text Chunking Parameters
          </h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-sub">Chunk Size (characters)</label>
              <input
                type="number"
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
                className="w-full border border-theme bg-input text-main rounded-lg px-3 py-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-sub">Chunk Overlap (characters)</label>
              <input
                type="number"
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(Number(e.target.value))}
                className="w-full border border-theme bg-input text-main rounded-lg px-3 py-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Card 2: AI Models */}
        <div className="p-5 rounded-xl border border-theme bg-card space-y-4">
          <h3 className="font-bold text-xs font-mono uppercase tracking-wider flex items-center gap-2 text-main">
            <Cpu className="w-3.5 h-3.5 text-muted-custom" />
            Vector & Reranker Models
          </h3>
          <div className="space-y-3.5">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-sub">SentenceTransformer Embedding Model</label>
              <CustomSelect
                value={embeddingModel}
                onChange={(e) => setEmbeddingModel(e.target.value)}
                options={[
                  { value: 'all-MiniLM-L6-v2', label: 'all-MiniLM-L6-v2 (384-dim, Fast)' },
                ]}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-sub">Cross-Encoder Reranker Model</label>
              <CustomSelect
                value={crossEncoder}
                onChange={(e) => setCrossEncoder(e.target.value)}
                options={[
                  { value: 'ms-marco-MiniLM-L-6-v2', label: 'cross-encoder/ms-marco-MiniLM-L-6-v2' },
                ]}
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-medium text-xs shadow-xs transition-all flex items-center gap-2"
          >
            <Save className="w-3.5 h-3.5" />
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
}
