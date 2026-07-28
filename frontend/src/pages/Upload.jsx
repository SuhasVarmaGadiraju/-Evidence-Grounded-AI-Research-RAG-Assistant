import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, Settings, X, Database } from 'lucide-react';
import api from '../services/api';

export default function UploadPage() {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [statusText, setStatusText] = useState('Ingesting documents...');
  const [strategy, setStrategy] = useState('fixed');
  const [notification, setNotification] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (newFiles) => {
    const pdfs = newFiles.filter(f => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'));
    const nonPdfs = newFiles.filter(f => !f.type === 'application/pdf' && !f.name.toLowerCase().endsWith('.pdf'));
    
    if (nonPdfs.length > 0) {
      setNotification({
        type: 'error',
        message: 'Only PDF documents are supported for ingestion.'
      });
      setTimeout(() => setNotification(null), 5000);
    }

    if (pdfs.length === 0) return;

    const mapped = pdfs.map(file => ({
      rawFile: file,
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
      status: 'pending',
      info: null
    }));

    setFiles(prev => [...prev, ...mapped]);
  };

  const removeFile = (index) => {
    if (uploading) return;
    setFiles(prev => prev.filter((_, idx) => idx !== index));
  };

  const triggerUpload = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    if (pendingFiles.length === 0) return;

    setUploading(true);
    setUploadProgress(0);
    setStatusText('Uploading file(s)...');
    setNotification(null);

    const formData = new FormData();
    pendingFiles.forEach(file => {
      formData.append('files', file.rawFile);
    });
    formData.append('strategy', strategy);

    let cleaningTimer = null;

    try {
      cleaningTimer = setTimeout(() => {
        setStatusText('Cleaning and normalizing text...');
      }, 1500);

      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const total = progressEvent.total || (progressEvent.loaded * 1.1);
          const percent = Math.round((progressEvent.loaded * 100) / total);
          setUploadProgress(percent > 100 ? 100 : percent);
          if (percent >= 100) {
            setStatusText('Extracting text from PDF...');
          }
        }
      });

      const backendResults = response.results || [];
      
      setFiles(prev => prev.map(file => {
        const match = backendResults.find(r => r.original_filename === file.name);
        if (match) {
          return {
            ...file,
            status: match.success ? 'success' : 'failed',
            info: match.success ? match.metadata : { error: match.error }
          };
        }
        return file;
      }));

      setNotification({
        type: 'success',
        message: `Successfully processed ${backendResults.filter(r => r.success).length} document(s).`
      });

    } catch (error) {
      const errMsg = error.message || 'File upload failed. Please try again.';
      setNotification({
        type: 'error',
        message: errMsg
      });
      
      setFiles(prev => prev.map(file => {
        if (file.status === 'pending') {
          return {
            ...file,
            status: 'failed',
            info: { error: errMsg }
          };
        }
        return file;
      }));
    } finally {
      if (cleaningTimer) {
        clearTimeout(cleaningTimer);
      }
      setUploading(false);
    }
  };

  const clearCompleted = () => {
    setFiles(prev => prev.filter(f => f.status === 'pending'));
    setNotification(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Title Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-main">
          Upload Documents
        </h1>
        <p className="text-xs text-sub mt-1">
          Upload PDF research papers. Text is extracted, tokenized, and indexed into FAISS vector store and BM25 lexical engine.
        </p>
      </div>

      {/* Notification Banner */}
      {notification && (
        <div className={`p-3.5 rounded-xl flex items-start gap-3 border text-xs ${
          notification.type === 'success'
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400'
            : 'bg-rose-500/10 border-rose-500/20 text-rose-500'
        }`}>
          {notification.type === 'success' ? (
            <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          )}
          <div>
            <p className="font-semibold">{notification.type === 'success' ? 'Upload Completed' : 'Ingestion Error'}</p>
            <p className="text-xs opacity-90 mt-0.5">{notification.message}</p>
          </div>
        </div>
      )}

      {/* Strategy Selector */}
      <div className="p-4 rounded-xl border border-theme bg-card flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-muted text-main rounded-lg border border-theme shrink-0">
            <Settings className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-main">Chunking & Tokenizer Settings</h3>
            <p className="text-[11px] text-sub">
              Select paragraph boundary segmentation algorithm.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 bg-muted p-1 rounded-lg border border-theme">
          <button
            type="button"
            onClick={() => setStrategy('fixed')}
            className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
              strategy === 'fixed'
                ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 font-semibold shadow-xs'
                : 'text-sub hover:text-main'
            }`}
          >
            Fixed-Size (500 Chars)
          </button>
          <button
            type="button"
            onClick={() => setStrategy('recursive')}
            className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
              strategy === 'recursive'
                ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 font-semibold shadow-xs'
                : 'text-sub hover:text-main'
            }`}
          >
            Recursive Structure
          </button>
        </div>
      </div>

      {/* Drag & Drop Dropzone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed border-theme rounded-2xl p-8 sm:p-10 text-center transition-all bg-card ${
          dragActive ? 'border-indigo-500 bg-indigo-500/5' : 'hover:border-theme-hover'
        }`}
      >
        <input
          type="file"
          multiple
          accept=".pdf,application/pdf"
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={uploading}
        />
        <div className="w-11 h-11 rounded-xl bg-muted border border-theme text-main flex items-center justify-center mx-auto mb-3">
          <Upload className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-bold text-main mb-1">Drag and drop research PDF files here</h3>
        <p className="text-xs text-sub">
          Supports multi-page academic papers, textbooks, and documentation (PDF format).
        </p>
      </div>

      {/* Selected Files List & Queue */}
      {files.length > 0 && (
        <div className="p-5 rounded-xl border border-theme bg-card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-custom font-mono">
              Ingestion Queue ({files.length})
            </h3>
            {files.some(f => f.status === 'success') && (
              <button
                onClick={clearCompleted}
                className="text-xs font-medium text-sub hover:text-main hover:underline"
              >
                Clear Ingested
              </button>
            )}
          </div>

          <div className="space-y-2">
            {files.map((file, index) => (
              <div
                key={index}
                className="p-3 rounded-lg border border-theme bg-muted/60 flex items-center justify-between gap-4"
              >
                <div className="flex items-center gap-2.5 overflow-hidden">
                  <div className="p-1.5 rounded bg-surface border border-theme text-sub shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="truncate">
                    <div className="text-xs font-semibold text-main truncate">{file.name}</div>
                    <div className="text-[10px] text-muted-custom font-mono">{file.size}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2.5">
                  {file.status === 'pending' && (
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-muted text-sub border border-theme">
                      Pending
                    </span>
                  )}
                  {file.status === 'success' && (
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      Indexed ({file.info?.total_chunks || 0} chunks)
                    </span>
                  )}
                  {file.status === 'failed' && (
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-rose-500/10 text-rose-500 border border-rose-500/20">
                      Failed
                    </span>
                  )}

                  {!uploading && (
                    <button
                      onClick={() => removeFile(index)}
                      className="p-1 rounded text-muted-custom hover:text-rose-500 transition-colors"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={triggerUpload}
              disabled={uploading || files.every(f => f.status === 'success')}
              className="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-medium text-xs shadow-xs transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  {statusText} ({uploadProgress}%)
                </>
              ) : (
                <>
                  <Database className="w-3.5 h-3.5" />
                  Start Ingestion & Indexing
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
