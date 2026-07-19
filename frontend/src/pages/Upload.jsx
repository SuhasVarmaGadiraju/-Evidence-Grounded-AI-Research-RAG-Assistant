import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, Settings } from 'lucide-react';
import api from '../services/api';

export default function UploadPage() {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [statusText, setStatusText] = useState('Ingesting documents...');
  const [strategy, setStrategy] = useState('fixed'); // 'fixed' | 'recursive'
  const [notification, setNotification] = useState(null); // { type: 'success' | 'error', message: string }

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
    // Only accept PDF files
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

    // Convert file objects into our state representation
    const mapped = pdfs.map(file => ({
      rawFile: file,
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
      status: 'pending', // 'pending' | 'success' | 'failed'
      info: null // stores metadata or error details after upload
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
    
    // Add chunking strategy to multipart form body
    formData.append('strategy', strategy);

    let cleaningTimer = null;

    try {
      // Set up timer to transition text to "Cleaning..." after upload finishes
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

      // Parse output results mapping back to our files state
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
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
          Upload Research Documents
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-xs">
          Upload PDF documents. The system will validate structural signatures and parse layout page text page-by-page.
        </p>
      </div>

      {/* Notification banner */}
      {notification && (
        <div className={`p-4 rounded-lg flex items-start gap-3 border text-sm ${
          notification.type === 'success'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/20 dark:border-emerald-900/50 dark:text-emerald-300'
            : 'bg-red-50 border-red-200 text-red-800 dark:bg-red-950/20 dark:border-red-900/50 dark:text-red-300'
        }`}>
          {notification.type === 'success' ? (
            <CheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          )}
          <div>
            <p className="font-semibold">{notification.type === 'success' ? 'Upload Completed' : 'Ingestion Error'}</p>
            <p className="text-xs opacity-90 mt-0.5">{notification.message}</p>
          </div>
        </div>
      )}

      {/* Chunking strategy configuration panel */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-500 dark:text-indigo-400 rounded-lg shrink-0">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
              Chunking Configuration
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Select the partition method for indexing document text pages.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Strategy:</label>
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            disabled={uploading}
            className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-brand-500 cursor-pointer"
          >
            <option value="fixed">Fixed Character (sliding-window offsets)</option>
            <option value="recursive">Recursive (split by paragraphs/sentences/words)</option>
            <option value="semantic">Semantic (split by sentence similarity embeddings)</option>
          </select>
        </div>
      </div>

      {/* Upload Drag Box */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center flex flex-col items-center justify-center transition-all ${
          dragActive
            ? 'border-brand-500 bg-brand-50/50 dark:bg-brand-950/20'
            : 'border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-400 dark:hover:border-slate-700'
        } ${uploading ? 'pointer-events-none opacity-60' : ''}`}
      >
        <Upload className="w-12 h-12 text-slate-400 mb-4" />
        <p className="text-sm text-slate-600 dark:text-slate-300 font-medium">
          Drag and drop PDF files here
        </p>
        <p className="text-xs text-slate-400 mt-1">
          Supported formats: PDF (Max size: 10MB)
        </p>
        
        <label className="mt-4 px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-lg text-xs font-semibold cursor-pointer transition-colors">
          Browse Files
          <input
            type="file"
            multiple
            accept=".pdf"
            onChange={handleFileInput}
            className="hidden"
            disabled={uploading}
          />
        </label>
      </div>

      {/* Upload Progress Bar */}
      {uploading && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex justify-between text-xs font-medium">
            <span className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-500" />
              {statusText}
            </span>
            <span className="text-slate-800 dark:text-slate-200">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className="bg-brand-600 h-full transition-all duration-300 ease-out"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Files List */}
      {files.length > 0 && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="font-bold text-sm text-slate-800 dark:text-slate-200">
              Queue / History ({files.length})
            </h3>
            <button
              onClick={clearCompleted}
              disabled={uploading || !files.some(f => f.status !== 'pending')}
              className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors disabled:opacity-50 cursor-pointer"
            >
              Clear Finished
            </button>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {files.map((file, idx) => (
              <div key={idx} className="py-3 flex flex-col gap-2">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-brand-500 shrink-0" />
                    <span className="font-semibold text-slate-700 dark:text-slate-300 truncate max-w-[250px] md:max-w-md">
                      {file.name}
                    </span>
                    <span className="text-slate-400">({file.size})</span>
                  </div>

                  <div className="flex items-center gap-3">
                    {file.status === 'pending' && (
                      <span className="text-slate-500 font-semibold">Pending</span>
                    )}
                    {file.status === 'success' && (
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                        <CheckCircle className="w-3.5 h-3.5" />
                        Ingested
                      </span>
                    )}
                    {file.status === 'failed' && (
                      <span className="text-red-600 dark:text-red-400 font-semibold flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" />
                        Failed
                      </span>
                    )}

                    <button
                      onClick={() => removeFile(idx)}
                      disabled={uploading}
                      className="text-slate-400 hover:text-red-500 transition-colors disabled:opacity-30 cursor-pointer"
                      title="Remove file"
                    >
                      &times;
                    </button>
                  </div>
                </div>

                {/* Display page stats or errors */}
                {file.status === 'success' && file.info && (
                  <div className="pl-6 text-[11px] text-slate-500 flex gap-4">
                    <span><strong>Pages:</strong> {file.info.total_pages}</span>
                    <span><strong>Chunks:</strong> {file.info.total_chunks} ({file.info.chunking_strategy === 'recursive' ? 'Recursive' : 'Fixed'})</span>
                    <span><strong>File ID:</strong> <code className="bg-slate-50 dark:bg-slate-800 px-1 rounded">{file.info.document_id}</code></span>
                  </div>
                )}

                {file.status === 'failed' && file.info && (
                  <div className="pl-6 text-[11px] text-red-500 font-medium">
                    {file.info.error}
                  </div>
                )}
              </div>
            ))}
          </div>

          {files.some(f => f.status === 'pending') && (
            <div className="flex justify-end pt-2">
              <button
                onClick={triggerUpload}
                disabled={uploading}
                className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-lg text-xs cursor-pointer transition-colors shadow-sm disabled:opacity-50"
              >
                {uploading ? 'Processing...' : 'Process & Ingest'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
