import React, { useState, useEffect, useRef } from 'react';
import {
  FileText,
  Loader2,
  Database,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  MoreVertical,
  Edit2,
  Info,
  Download,
  Copy,
  Trash2,
  X,
  Check,
  Calendar,
  Layers,
  Cpu,
  CheckCircle2
} from 'lucide-react';
import api from '../services/api';

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [indexStats, setIndexStats] = useState(null);

  // Expand / Chunk preview state
  const [expandedDocId, setExpandedDocId] = useState(null);
  const [previewChunks, setPreviewChunks] = useState([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState(null);

  // Action Menu state
  const [activeMenuDocId, setActiveMenuDocId] = useState(null);

  // Modals state
  const [renameModalDoc, setRenameModalDoc] = useState(null);
  const [newFilename, setNewFilename] = useState('');
  const [renaming, setRenaming] = useState(false);

  const [detailsModalDoc, setDetailsModalDoc] = useState(null);

  const [deleteModalDoc, setDeleteModalDoc] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Toast notification state
  const [toast, setToast] = useState(null);

  const menuRef = useRef(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  // Close actions menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setActiveMenuDocId(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

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

  const handleToggleExpand = async (docId, e) => {
    if (e) e.stopPropagation();
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

  // Actions handlers
  const handleOpenRename = (doc) => {
    setActiveMenuDocId(null);
    setRenameModalDoc(doc);
    setNewFilename(doc.filename || doc.original_filename || '');
  };

  const handleSaveRename = async (e) => {
    e.preventDefault();
    if (!renameModalDoc || !newFilename.trim()) return;

    setRenaming(true);
    try {
      const res = await api.patch(`/documents/${renameModalDoc.document_id}`, {
        filename: newFilename.trim()
      });
      if (res.success) {
        showToast('success', `Document renamed to "${newFilename.trim()}"`);
        setRenameModalDoc(null);
        fetchDocuments();
      } else {
        showToast('error', res.message || 'Failed to rename document.');
      }
    } catch (err) {
      showToast('error', err.message || 'Error executing rename request.');
    } finally {
      setRenaming(false);
    }
  };

  const handleCopyId = (docId) => {
    setActiveMenuDocId(null);
    navigator.clipboard.writeText(docId);
    showToast('success', 'Document ID copied to clipboard!');
  };

  const handleDownload = (doc) => {
    setActiveMenuDocId(null);
    window.open(`/api/documents/${doc.document_id}/download`, '_blank');
    showToast('success', `Downloading ${doc.filename}...`);
  };

  const handleOpenDetails = (doc) => {
    setActiveMenuDocId(null);
    setDetailsModalDoc(doc);
  };

  const handleOpenDelete = (doc) => {
    setActiveMenuDocId(null);
    setDeleteModalDoc(doc);
  };

  const handleConfirmDelete = async () => {
    if (!deleteModalDoc) return;
    setDeleting(true);
    try {
      const res = await api.delete(`/documents/${deleteModalDoc.document_id}`);
      if (res.success) {
        showToast('success', `Successfully deleted "${deleteModalDoc.filename}" and updated vector index.`);
        setDeleteModalDoc(null);
        fetchDocuments();
      } else {
        showToast('error', res.message || 'Failed to delete document.');
      }
    } catch (err) {
      showToast('error', err.message || 'Error performing document deletion.');
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  };

  const formatStrategy = (doc) => {
    if (!doc.chunking_strategy) return 'Fixed-size';
    const strat = doc.chunking_strategy;
    if (typeof strat === 'string') return strat;
    return `${strat.name || 'Fixed'} (${strat.chunk_size || 500}c)`;
  };

  return (
    <div className="space-y-6 animate-fade-in relative">
      {/* Toast Notification Banner */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 animate-fade-in">
          <div className={`px-4 py-3 rounded-2xl shadow-xl border flex items-center gap-3 text-xs font-semibold ${
            toast.type === 'success'
              ? 'bg-emerald-500 text-white border-emerald-600'
              : 'bg-red-500 text-white border-red-600'
          }`}>
            {toast.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            <span>{toast.message}</span>
            <button onClick={() => setToast(null)} className="ml-2 hover:opacity-80">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-main">Documents</h1>
          <p className="text-xs text-sub mt-1">
            Explore ingested literature, chunk metadata, vector dimensions, and manage document library records.
          </p>
        </div>
        <button
          onClick={fetchDocuments}
          disabled={loading}
          className="self-start sm:self-auto px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-sm transition-all flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Refresh Library'}
        </button>
      </div>

      {/* Index Stats Bar */}
      {indexStats && (
        <div className="p-5 rounded-2xl border border-theme bg-card">
          <div className="flex items-center gap-2 mb-3">
            <Database className="w-4 h-4 text-brand-500" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-custom font-mono">
              Vector & Lexical Storage Index
            </h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <div className="text-sub">Total Documents</div>
              <div className="text-lg font-bold text-main">{indexStats.total_documents || docs.length}</div>
            </div>
            <div>
              <div className="text-sub">FAISS Vector Count</div>
              <div className="text-lg font-bold text-main">{indexStats.faiss_vector_count || indexStats.total_vectors || 0}</div>
            </div>
            <div>
              <div className="text-sub">BM25 Chunks</div>
              <div className="text-lg font-bold text-main">{indexStats.bm25_chunk_count || 0}</div>
            </div>
            <div>
              <div className="text-sub">Embedding Dimension</div>
              <div className="text-lg font-bold font-mono text-main">{indexStats.embedding_dimension || 384}d</div>
            </div>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-500 text-xs flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <div>
            <p className="font-semibold">Library Error</p>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="py-12 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
          <p className="text-xs font-medium text-sub">Loading document index...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && docs.length === 0 && (
        <div className="p-12 rounded-3xl border border-theme bg-card text-center">
          <div className="w-12 h-12 rounded-2xl bg-brand-500/10 text-brand-500 border border-brand-500/20 flex items-center justify-center mx-auto mb-3">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-main">No Documents Found</h3>
          <p className="text-xs text-sub mt-1 max-w-sm mx-auto">
            Upload PDF papers to generate 384-d embeddings and BM25 index terms.
          </p>
        </div>
      )}

      {/* Documents Table */}
      {!loading && !error && docs.length > 0 && (
        <div className="rounded-2xl border border-theme bg-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-theme bg-muted text-[10px] uppercase font-mono tracking-wider text-muted-custom">
                  <th className="px-4 py-3.5 w-10"></th>
                  <th className="px-5 py-3.5">Document Name</th>
                  <th className="px-4 py-3.5">Pages</th>
                  <th className="px-4 py-3.5">Strategy</th>
                  <th className="px-4 py-3.5">Chunks</th>
                  <th className="px-4 py-3.5">Embedding</th>
                  <th className="px-4 py-3.5">Upload Date</th>
                  <th className="px-4 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-theme text-xs">
                {docs.map((doc) => {
                  const isExpanded = expandedDocId === doc.document_id;
                  const isMenuOpen = activeMenuDocId === doc.document_id;

                  return (
                    <React.Fragment key={doc.document_id}>
                      <tr
                        className={`transition-colors ${
                          isExpanded ? 'bg-brand-500/10' : 'hover:bg-muted'
                        }`}
                      >
                        <td className="px-4 py-4">
                          <button
                            onClick={(e) => handleToggleExpand(doc.document_id, e)}
                            className="text-muted-custom hover:text-main"
                          >
                            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </td>
                        <td className="px-5 py-4 font-bold text-main flex items-center gap-2">
                          <FileText className="w-4 h-4 text-brand-500 shrink-0" />
                          <span className="truncate max-w-xs">{doc.filename}</span>
                        </td>
                        <td className="px-4 py-4 text-sub">{doc.pages || doc.total_pages} p</td>
                        <td className="px-4 py-4 text-indigo-500 font-medium">
                          {formatStrategy(doc)}
                        </td>
                        <td className="px-4 py-4 font-semibold text-emerald-500">
                          {doc.total_chunks || 0} chunks
                        </td>
                        <td className="px-4 py-4">
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-blue-500/10 text-blue-500 border border-blue-500/20">
                            {doc.embedding_status || 'completed'} ({doc.embedding_dimension || 384}d)
                          </span>
                        </td>
                        <td className="px-4 py-4 text-muted-custom">
                          {formatDate(doc.upload_timestamp)}
                        </td>

                        {/* Three-dot Actions Column */}
                        <td className="px-4 py-4 text-right relative">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveMenuDocId(isMenuOpen ? null : doc.document_id);
                            }}
                            className="p-1.5 rounded-lg text-muted-custom hover:text-main hover:bg-muted transition-colors"
                            title="Document Actions"
                          >
                            <MoreVertical className="w-4 h-4" />
                          </button>

                          {/* Dropdown Menu Popup */}
                          {isMenuOpen && (
                            <div
                              ref={menuRef}
                              className="absolute right-4 top-12 w-48 rounded-2xl border border-theme bg-surface shadow-2xl p-1.5 z-50 animate-fade-in text-left"
                            >
                              <button
                                onClick={() => handleOpenRename(doc)}
                                className="w-full text-left px-3 py-2 rounded-xl text-xs font-medium flex items-center gap-2 text-sub hover:bg-muted hover:text-main transition-colors"
                              >
                                <Edit2 className="w-3.5 h-3.5 text-brand-500" />
                                Rename Document
                              </button>

                              <button
                                onClick={() => handleOpenDetails(doc)}
                                className="w-full text-left px-3 py-2 rounded-xl text-xs font-medium flex items-center gap-2 text-sub hover:bg-muted hover:text-main transition-colors"
                              >
                                <Info className="w-3.5 h-3.5 text-indigo-500" />
                                View Details
                              </button>

                              <button
                                onClick={() => handleDownload(doc)}
                                className="w-full text-left px-3 py-2 rounded-xl text-xs font-medium flex items-center gap-2 text-sub hover:bg-muted hover:text-main transition-colors"
                              >
                                <Download className="w-3.5 h-3.5 text-emerald-500" />
                                Download PDF
                              </button>

                              <button
                                onClick={() => handleCopyId(doc.document_id)}
                                className="w-full text-left px-3 py-2 rounded-xl text-xs font-medium flex items-center gap-2 text-sub hover:bg-muted hover:text-main transition-colors"
                              >
                                <Copy className="w-3.5 h-3.5 text-amber-500" />
                                Copy Document ID
                              </button>

                              <div className="border-t border-theme my-1"></div>

                              <button
                                onClick={() => handleOpenDelete(doc)}
                                className="w-full text-left px-3 py-2 rounded-xl text-xs font-medium flex items-center gap-2 text-red-500 hover:bg-red-500/10 transition-colors"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                                Delete Document
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>

                      {/* Chunk Preview Drawer */}
                      {isExpanded && (
                        <tr className="bg-muted">
                          <td colSpan="8" className="px-6 py-4 border-b border-theme">
                            <div className="space-y-3">
                              <div className="text-[11px] font-bold uppercase tracking-wider text-muted-custom font-mono">
                                Chunk Preview (First 3 Chunks)
                              </div>

                              {previewLoading && (
                                <div className="flex items-center gap-2 text-xs text-sub py-2">
                                  <Loader2 className="w-4 h-4 animate-spin text-brand-500" />
                                  Loading chunk data...
                                </div>
                              )}

                              {previewError && <div className="text-xs text-red-500">{previewError}</div>}

                              {!previewLoading && !previewError && previewChunks.length > 0 && (
                                <div className="grid md:grid-cols-3 gap-3">
                                  {previewChunks.map((chunk) => (
                                    <div
                                      key={chunk.chunk_id}
                                      className="p-3 rounded-xl border border-theme bg-card space-y-1.5"
                                    >
                                      <div className="flex justify-between items-center text-[10px] font-mono text-muted-custom">
                                        <span>Page {chunk.page_number}</span>
                                        <span>{chunk.char_count} chars</span>
                                      </div>
                                      <p className="text-xs text-sub line-clamp-3 italic">
                                        "{chunk.text}"
                                      </p>
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

      {/* 1. Rename Modal */}
      {renameModalDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md p-6 rounded-3xl border border-theme bg-surface shadow-2xl space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-bold text-base text-main flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-brand-500" />
                Rename Document
              </h3>
              <button onClick={() => setRenameModalDoc(null)} className="text-muted-custom hover:text-main">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveRename} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-sub mb-1.5">Document Filename</label>
                <input
                  type="text"
                  required
                  value={newFilename}
                  onChange={(e) => setNewFilename(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-theme bg-input text-main text-xs font-medium focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setRenameModalDoc(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold border border-theme text-sub hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={renaming || !newFilename.trim()}
                  className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-sm flex items-center gap-2 disabled:opacity-50"
                >
                  {renaming ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                  Save Filename
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 2. View Details Modal */}
      {detailsModalDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg p-6 rounded-3xl border border-theme bg-surface shadow-2xl space-y-5">
            <div className="flex justify-between items-center border-b border-theme pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-brand-500" />
                <h3 className="font-bold text-base text-main truncate max-w-xs">{detailsModalDoc.filename}</h3>
              </div>
              <button onClick={() => setDetailsModalDoc(null)} className="text-muted-custom hover:text-main">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3.5 rounded-2xl bg-muted border border-theme">
                <div>
                  <span className="text-muted-custom block text-[10px] uppercase font-mono">Document ID</span>
                  <span className="font-mono text-main select-all">{detailsModalDoc.document_id}</span>
                </div>
                <div>
                  <span className="text-muted-custom block text-[10px] uppercase font-mono">Upload Date</span>
                  <span className="text-main">{formatDate(detailsModalDoc.upload_timestamp)}</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-xl border border-theme bg-card">
                  <span className="text-muted-custom block text-[10px] uppercase font-mono">Total Pages</span>
                  <span className="font-bold text-main">{detailsModalDoc.pages || detailsModalDoc.total_pages}</span>
                </div>
                <div className="p-3 rounded-xl border border-theme bg-card">
                  <span className="text-muted-custom block text-[10px] uppercase font-mono">Text Chunks</span>
                  <span className="font-bold text-emerald-500">{detailsModalDoc.total_chunks || 0}</span>
                </div>
                <div className="p-3 rounded-xl border border-theme bg-card">
                  <span className="text-muted-custom block text-[10px] uppercase font-mono">Vector Dimension</span>
                  <span className="font-bold font-mono text-brand-500">{detailsModalDoc.embedding_dimension || 384}d</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl border border-theme bg-card space-y-1.5">
                <div className="text-muted-custom text-[10px] uppercase font-mono">Pipeline Configurations</div>
                <div className="flex justify-between">
                  <span className="text-sub">Chunking Strategy:</span>
                  <span className="font-semibold text-indigo-500">{formatStrategy(detailsModalDoc)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sub">Embedding Model:</span>
                  <span className="font-mono text-main">{detailsModalDoc.embedding_model || 'all-MiniLM-L6-v2'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sub">Vector Store:</span>
                  <span className="font-mono text-main">FAISS IndexFlatIP</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setDetailsModalDoc(null)}
                className="px-5 py-2 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white shadow-sm"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. Delete Confirmation Modal */}
      {deleteModalDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md p-6 rounded-3xl border border-theme bg-surface shadow-2xl space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2.5 rounded-xl bg-red-500/10 text-red-500 border border-red-500/20 shrink-0">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold text-base text-main">Delete Document Record?</h3>
                <p className="text-xs text-sub mt-1">
                  Are you sure you want to permanently purge <span className="font-bold text-main">"{deleteModalDoc.filename}"</span>?
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-500 text-xs leading-relaxed">
              <span className="font-bold">Warning:</span> Deleting this document will purge its raw PDF file, text chunks, and 384-d FAISS embeddings, and automatically rebuild the vector index.
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                disabled={deleting}
                onClick={() => setDeleteModalDoc(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold border border-theme text-sub hover:bg-muted"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deleting}
                onClick={handleConfirmDelete}
                className="px-5 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-semibold shadow-sm flex items-center gap-2 disabled:opacity-50"
              >
                {deleting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                Delete Document
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
