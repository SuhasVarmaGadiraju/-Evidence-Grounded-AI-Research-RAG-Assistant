import React, { useState, useEffect } from 'react';
import { FileText, Calendar, Loader2, Database, AlertTriangle, ChevronDown, ChevronUp, Layers, List } from 'lucide-react';
import api from '../services/api';

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [indexStats, setIndexStats] = useState(null);

  // Preview state for accordion
  const [expandedDocId, setExpandedDocId] = useState(null);
  const [previewChunks, setPreviewChunks] = useState([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    setExpandedDocId(null);
    try {
      const response = await api.get('/documents');
      setDocs(response.documents || []);
      setIndexStats(response.index_stats || null);
    } catch (err) {
      console.error('Error fetching library documents:', err);
      setError(err.message || 'Failed to retrieve document library list');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleExpand = async (docId) => {
    if (expandedDocId === docId) {
      setExpandedDocId(null);
      setPreviewChunks([]);
      return;
    }

    setExpandedDocId(docId);
    setPreviewChunks([]);
    setPreviewLoading(true);
    setPreviewError(null);

    try {
      const response = await api.get(`/documents/${docId}/chunks?limit=3`);
      setPreviewChunks(response.chunks || []);
    } catch (err) {
      console.error('Failed to load chunks preview:', err);
      setPreviewError(err.message || 'Failed to load chunks preview.');
    } finally {
      setPreviewLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (isoString) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (e) {
      return isoString;
    }
  };

  const formatStrategy = (doc) => {
    if (!doc.chunking_strategy) return 'N/A';
    if (doc.chunking_strategy === 'fixed_character') {
      return `Fixed (${doc.chunk_size || 500}/${doc.chunk_overlap || 100})`;
    }
    if (doc.chunking_strategy === 'semantic') {
      return `Semantic (${doc.chunk_size || 500}/${doc.chunk_overlap || 100}/${doc.semantic_threshold || 0.6})`;
    }
    return doc.chunking_strategy;
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Title */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Database className="w-6 h-6 text-brand-500" />
            Document Library
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-xs">
            Manage your uploaded files, review chunk statistics, and browse indexed text contents.
          </p>
        </div>
        <button
          onClick={fetchDocuments}
          disabled={loading}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold rounded-lg transition-colors cursor-pointer disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Global Index Stats Card */}
      {indexStats && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl p-4 text-xs shadow-sm">
          <div className="space-y-1">
            <span className="text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Index Status</span>
            <div className="flex items-center gap-1.5 font-bold text-slate-700 dark:text-slate-200">
              <span className={`w-2 h-2 rounded-full ${indexStats.status === 'active' ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`}></span>
              {indexStats.status === 'active' ? 'Active / Synchronized' : 'Empty / Ready'}
            </div>
          </div>
          <div className="space-y-1">
            <span className="text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Index Version</span>
            <div className="font-bold text-slate-700 dark:text-slate-200">{indexStats.version || '1.0'}</div>
          </div>
          <div className="space-y-1">
            <span className="text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Indexed Vectors</span>
            <div className="font-bold text-slate-700 dark:text-slate-200">{indexStats.vector_count || 0} Chunks</div>
          </div>
        </div>
      )}

      {/* States */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-16 space-y-4">
          <Loader2 className="w-10 h-10 animate-spin text-brand-500" />
          <p className="text-slate-500 text-sm">Scanning system metadata...</p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-800 dark:bg-red-950/20 dark:border-red-900/50 dark:text-red-300 rounded-lg flex items-center gap-2 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && docs.length === 0 && (
        <div className="text-center py-16 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl space-y-2">
          <FileText className="w-12 h-12 text-slate-300 mx-auto" />
          <p className="font-semibold text-slate-700 dark:text-slate-300">No documents ingested</p>
          <p className="text-xs text-slate-400">Navigate to the Upload tab to add PDF files to your library.</p>
        </div>
      )}

      {/* Docs Table */}
      {!loading && !error && docs.length > 0 && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                  <th className="px-6 py-4 w-[10px]"></th>
                  <th className="px-6 py-4">Document Name</th>
                  <th className="px-6 py-4">Size</th>
                  <th className="px-6 py-4">Strategy</th>
                  <th className="px-6 py-4">Chunks</th>
                  <th className="px-6 py-4">Embedding</th>
                  <th className="px-6 py-4">Uploaded</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {docs.map((doc) => {
                  const isExpanded = expandedDocId === doc.document_id;
                  return (
                    <React.Fragment key={doc.document_id}>
                      {/* Main Document Row */}
                      <tr className="hover:bg-slate-50/50 dark:hover:bg-slate-800/20 text-slate-700 dark:text-slate-300 border-b border-slate-100 dark:border-slate-800/60">
                        <td className="px-4 py-4 text-center">
                          <button
                            onClick={() => handleToggleExpand(doc.document_id)}
                            className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors cursor-pointer"
                            title="Preview Chunks"
                          >
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4 text-slate-500" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-slate-500" />
                            )}
                          </button>
                        </td>
                        <td className="px-6 py-4 font-medium flex items-center gap-2 border-none">
                          <FileText className="w-4 h-4 text-brand-500 shrink-0" />
                          <span className="truncate max-w-[200px] sm:max-w-[320px]" title={doc.original_filename}>
                            {doc.original_filename}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-500">
                          {formatBytes(doc.file_size_bytes)}
                        </td>
                        <td className="px-6 py-4 text-xs font-semibold text-indigo-600 dark:text-indigo-400 flex items-center gap-1 mt-1 border-none">
                          <Layers className="w-3.5 h-3.5 shrink-0" />
                          {formatStrategy(doc)}
                        </td>
                        <td className="px-6 py-4">
                          <span className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 text-xs px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1 w-max">
                            <List className="w-3 h-3 shrink-0" />
                            {doc.total_chunks || 0} Chunks
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs">
                          {doc.embedding_status === 'completed' ? (
                            <div className="flex flex-col gap-0.5">
                              <span className="bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 px-2 py-0.5 rounded-full font-semibold text-[10px] w-max">
                                Completed
                              </span>
                              <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                                {doc.embedding_model} ({doc.embedding_dimension}d)
                              </div>
                            </div>
                          ) : doc.embedding_status === 'failed' ? (
                            <span className="bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300 px-2 py-0.5 rounded-full font-semibold text-[10px] w-max">
                              Failed
                            </span>
                          ) : (
                            <span className="bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 px-2 py-0.5 rounded-full font-semibold text-[10px] w-max">
                              None / Pending
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-500">
                          {formatDate(doc.upload_timestamp)}
                        </td>
                      </tr>

                      {/* Accordion Chunks Preview Row */}
                      {isExpanded && (
                        <tr className="bg-slate-50/50 dark:bg-slate-900/40">
                          <td colSpan="7" className="px-8 py-4 border-b border-slate-200 dark:border-slate-800">
                            <div className="space-y-3">
                              <div className="flex justify-between items-center">
                                <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                                  Ingested Chunk Preview (Showing first 3 chunks)
                                </span>
                              </div>

                              {previewLoading && (
                                <div className="flex items-center gap-2 text-xs text-slate-500 py-3">
                                  <Loader2 className="w-4 h-4 animate-spin text-brand-500" />
                                  Loading chunk data from server...
                                </div>
                              )}

                              {previewError && (
                                <div className="text-xs text-red-500 py-2">
                                  {previewError}
                                </div>
                              )}

                              {!previewLoading && !previewError && previewChunks.length === 0 && (
                                <div className="text-xs text-slate-400 py-2">
                                  No chunks available for this document.
                                </div>
                              )}

                              {!previewLoading && !previewError && previewChunks.length > 0 && (
                                <div className="grid md:grid-cols-3 gap-4">
                                  {previewChunks.map((chunk, cIdx) => (
                                    <div
                                      key={chunk.chunk_id}
                                      className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg p-3 space-y-2 shadow-sm"
                                    >
                                      <div className="flex justify-between items-center text-[10px] font-semibold text-slate-400">
                                        <span>Page {chunk.page_number} (Index {chunk.chunk_index})</span>
                                        <span>{chunk.char_count} chars</span>
                                      </div>
                                      <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed line-clamp-4 italic">
                                        "{chunk.text}"
                                      </p>
                                      <div className="pt-1 text-[9px] font-mono text-slate-400 truncate">
                                        {chunk.chunk_id}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
