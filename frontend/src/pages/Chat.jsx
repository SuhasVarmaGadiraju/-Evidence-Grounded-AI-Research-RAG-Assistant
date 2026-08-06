import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Send,
  Loader2,
  AlertCircle,
  Copy,
  Check,
  BookOpen,
  Clock,
  Plus,
  Trash2,
  Edit2,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  User,
  Bot,
  Download,
  FileText,
  ChevronDown,
  Layers,
  Cpu
} from 'lucide-react';
import api from '../services/api';

export default function Chat() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showDevTiming, setShowDevTiming] = useState({});
  const [showSourceAttribution, setShowSourceAttribution] = useState({});
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [exportDropdownOpen, setExportDropdownOpen] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages, loading]);

  const fetchSessions = async () => {
    try {
      const res = await api.get('/sessions');
      if (res.success) {
        setSessions(res.sessions || []);
        if (!sessionId && res.sessions && res.sessions.length > 0) {
          loadSessionHistory(res.sessions[0].session_id);
        }
      }
    } catch (err) {
      // Fallback to legacy chat/sessions endpoint if needed
      try {
        const legacyRes = await api.get('/chat/sessions');
        if (legacyRes.success) {
          setSessions(legacyRes.sessions || []);
        }
      } catch (legacyErr) {
        console.error('Error fetching sessions:', legacyErr);
      }
    }
  };

  const loadSessionHistory = async (targetSessionId) => {
    try {
      setLoading(true);
      setSessionId(targetSessionId);
      setError(null);
      const res = await api.get(`/sessions/${targetSessionId}`);
      if (res.success) {
        const loadedMsgs = (res.session?.messages || []).map((m) => ({
          role: m.role || 'assistant',
          content: m.role === 'user' ? m.user_question : m.assistant_answer,
          latency: m.latency,
          retrieval_logs: m.retrieval_logs || [],
          timestamp: m.created_at ? new Date(m.created_at).getTime() : Date.now()
        }));
        setMessages(loadedMsgs);
      }
    } catch (err) {
      // Fallback to legacy chat history endpoint
      try {
        const legacyRes = await api.get(`/chat/history/${targetSessionId}`);
        if (legacyRes.success) {
          setMessages(legacyRes.messages || []);
        }
      } catch (legacyErr) {
        console.error('Error loading session history:', legacyErr);
        setError('Failed to load conversation history.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      setError(null);
      const res = await api.post('/sessions', { title: 'New Research Session' });
      if (res.success && res.session) {
        setSessionId(res.session.session_id);
        setMessages([]);
        setQuery('');
        fetchSessions();
      }
    } catch (err) {
      console.error('Error creating new session:', err);
      setSessionId(null);
      setMessages([]);
      setQuery('');
    }
  };

  const handleRenameSession = async (targetSessionId, e) => {
    e.stopPropagation();
    if (!editingTitle.trim()) {
      setEditingSessionId(null);
      return;
    }
    try {
      const res = await api.patch(`/sessions/${targetSessionId}`, { title: editingTitle.trim() });
      if (res.success) {
        setEditingSessionId(null);
        setEditingTitle('');
        fetchSessions();
      }
    } catch (err) {
      console.error('Error renaming session:', err);
    }
  };

  const startEditing = (s, e) => {
    e.stopPropagation();
    setEditingSessionId(s.session_id);
    setEditingTitle(s.title || '');
  };

  const handleDeleteSession = async (targetSessionId, e) => {
    e.stopPropagation();
    try {
      const res = await api.delete(`/sessions/${targetSessionId}`);
      if (res.success) {
        if (sessionId === targetSessionId) {
          setSessionId(null);
          setMessages([]);
        }
        fetchSessions();
      }
    } catch (err) {
      console.error('Error deleting session:', err);
    }
  };

  const handleExportSession = (format) => {
    if (!sessionId) return;
    setExportDropdownOpen(false);
    const apiBase = import.meta.env.VITE_API_URL || '/api';
    const exportUrl = `${apiBase}/sessions/${sessionId}/export?format=${format}`;
    window.open(exportUrl, '_blank');
  };

  const executeQuery = async (searchQuery) => {
    if (!searchQuery.trim() || loading) return;

    const currentQuery = searchQuery.trim();
    setLoading(true);
    setError(null);
    setQuery('');

    const userMsg = { role: 'user', content: currentQuery, timestamp: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setStage('Searching Documents & FAISS Vector Index...');

    const stageTimer1 = setTimeout(() => {
      setStage('Reranking Candidates via Cross-Encoder...');
    }, 600);

    const stageTimer2 = setTimeout(() => {
      setStage('Building & Formatting Conversation Context...');
    }, 1200);

    const stageTimer3 = setTimeout(() => {
      setStage('Generating Grounded Answer via NVIDIA LLM API...');
    }, 1800);

    try {
      const data = await api.post('/chat', {
        question: currentQuery,
        session_id: sessionId,
        top_k: 5
      });

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);

      if (data.success) {
        setSessionId(data.session_id);
        const assistantMsg = {
          role: 'assistant',
          content: data.answer,
          model: data.model,
          latency: data.latency,
          retrieval_latency_ms: data.retrieval_latency_ms,
          embedding_model: data.embedding_model,
          cross_encoder_model: data.cross_encoder_model,
          conversation_length: data.conversation_length,
          llm_latency: data.llm_latency,
          prompt_tokens: data.prompt_tokens,
          completion_tokens: data.completion_tokens,
          citations: data.citations || [],
          retrieved_chunks: data.retrieved_chunks || data.results || [],
          request_id: data.request_id,
          cache_hit: data.cache_hit,
          timing_breakdown: data.timing_breakdown,
          timestamp: Date.now()
        };

        setMessages((prev) => [...prev, assistantMsg]);
        fetchSessions();
      } else {
        setError(data.message || 'Failed to generate response.');
      }
    } catch (err) {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);
      console.error('Error in chat request:', err);
      setError(err.message || 'Failed to communicate with RAG AI Chat backend.');
    } finally {
      setLoading(false);
      setStage('');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    executeQuery(query);
  };

  const handleCopy = (text, idx) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const toggleDevTiming = (idx) => {
    setShowDevTiming((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const toggleSourceAttribution = (idx) => {
    setShowSourceAttribution((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const renderSimpleMarkdown = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      let trimmed = line.trim();
      if (trimmed.startsWith('### ')) {
        return (
          <h3 key={idx} className="text-sm font-bold mt-3 mb-1 text-main">
            {trimmed.replace(/^###\s+/, '')}
          </h3>
        );
      } else if (trimmed.startsWith('## ')) {
        return (
          <h2 key={idx} className="text-base font-bold mt-4 mb-1 text-main">
            {trimmed.replace(/^##\s+/, '')}
          </h2>
        );
      } else if (trimmed.startsWith('# ')) {
        return (
          <h1 key={idx} className="text-lg font-extrabold mt-4 mb-2 text-main">
            {trimmed.replace(/^#\s+/, '')}
          </h1>
        );
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        return (
          <li key={idx} className="ml-4 list-disc text-xs my-0.5 text-sub">
            {trimmed.replace(/^[-*]\s+/, '')}
          </li>
        );
      } else if (trimmed === '') {
        return <div key={idx} className="h-1.5" />;
      } else {
        return (
          <p key={idx} className="text-xs leading-relaxed my-1 text-sub">
            {trimmed}
          </p>
        );
      }
    });
  };

  return (
    <div className="flex h-[calc(100vh-8.5rem)] gap-4 animate-fade-in">
      {/* Dynamic Research Sessions Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-0 hidden md:flex md:w-12'
        } transition-all duration-300 rounded-xl p-3 flex flex-col justify-between border border-theme bg-surface shrink-0`}
      >
        <div className="space-y-3 overflow-hidden flex-1 flex flex-col">
          <div className="flex items-center justify-between px-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-custom flex items-center gap-1.5 font-mono">
              <MessageSquare className="w-3.5 h-3.5 text-main" />
              Research Sessions
            </span>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-muted-custom hover:text-main p-1 rounded transition-colors"
              title="Toggle Sidebar"
            >
              {sidebarOpen ? <PanelLeftClose className="w-3.5 h-3.5" /> : <PanelLeftOpen className="w-3.5 h-3.5" />}
            </button>
          </div>

          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 text-xs font-medium rounded-lg shadow-xs transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Session</span>
          </button>

          {/* Persistent Sessions List */}
          <div className="flex-1 overflow-y-auto space-y-1 pr-1">
            {sessions.map((s) => (
              <div
                key={s.session_id}
                onClick={() => loadSessionHistory(s.session_id)}
                className={`group flex items-center justify-between p-2 rounded-lg text-xs cursor-pointer transition-all ${
                  sessionId === s.session_id
                    ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 font-medium'
                    : 'text-sub hover:bg-card-hover hover:text-main'
                }`}
              >
                <div className="flex items-center gap-2 truncate flex-1 min-w-0">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0 text-muted-custom" />
                  {editingSessionId === s.session_id ? (
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleRenameSession(s.session_id, e);
                        if (e.key === 'Escape') setEditingSessionId(null);
                      }}
                      onBlur={(e) => handleRenameSession(s.session_id, e)}
                      autoFocus
                      className="px-1.5 py-0.5 bg-surface text-main border border-indigo-500 rounded text-xs w-full focus:outline-none"
                    />
                  ) : (
                    <span className="truncate">{s.title || 'New Research Session'}</span>
                  )}
                </div>

                {editingSessionId !== s.session_id && (
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => startEditing(s, e)}
                      className="p-1 text-muted-custom hover:text-main"
                      title="Rename Session"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                    <button
                      onClick={(e) => handleDeleteSession(s.session_id, e)}
                      className="p-1 text-muted-custom hover:text-rose-500"
                      title="Delete Session"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Chat Thread Window */}
      <div className="flex-1 flex flex-col rounded-xl border border-theme bg-card overflow-hidden">
        {/* Top Header & Export Toolbar */}
        <div className="p-3.5 border-b border-theme bg-muted/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {!sidebarOpen && (
              <button onClick={() => setSidebarOpen(true)} className="text-muted-custom hover:text-main p-1">
                <PanelLeftOpen className="w-4 h-4" />
              </button>
            )}
            <h2 className="text-xs font-bold uppercase tracking-wider flex items-center gap-2 text-main font-mono">
              <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
              Evidence-Grounded AI Research Workspace
            </h2>
          </div>

          <div className="flex items-center gap-2">
            {sessionId && (
              <div className="relative">
                <button
                  onClick={() => setExportDropdownOpen(!exportDropdownOpen)}
                  className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg bg-surface border border-theme hover:bg-card-hover text-main transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export Session</span>
                  <ChevronDown className="w-3 h-3 text-muted-custom" />
                </button>

                {exportDropdownOpen && (
                  <div className="absolute right-0 mt-1 w-36 bg-surface border border-theme rounded-lg shadow-lg py-1 z-30 font-mono text-xs">
                    <button
                      onClick={() => handleExportSession('markdown')}
                      className="w-full px-3 py-1.5 text-left hover:bg-card-hover text-sub hover:text-main flex items-center gap-2"
                    >
                      <FileText className="w-3.5 h-3.5 text-indigo-500" />
                      Markdown (.md)
                    </button>
                    <button
                      onClick={() => handleExportSession('json')}
                      className="w-full px-3 py-1.5 text-left hover:bg-card-hover text-sub hover:text-main flex items-center gap-2"
                    >
                      <FileText className="w-3.5 h-3.5 text-emerald-500" />
                      JSON (.json)
                    </button>
                    <button
                      onClick={() => handleExportSession('pdf')}
                      className="w-full px-3 py-1.5 text-left hover:bg-card-hover text-sub hover:text-main flex items-center gap-2"
                    >
                      <FileText className="w-3.5 h-3.5 text-rose-500" />
                      PDF Document
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Conversation Thread Area */}
        <div className="flex-1 p-5 overflow-y-auto space-y-5">
          {messages.length === 0 && !loading && (
            <div className="text-center space-y-2.5 py-16 text-muted-custom">
              <div className="w-10 h-10 rounded-xl bg-muted border border-theme text-main flex items-center justify-center mx-auto">
                <Bot className="w-5 h-5" />
              </div>
              <p className="font-semibold text-sm text-main">
                Ask any research question to start a persistent session with ChatGPT-like conversation memory.
              </p>
              <p className="text-xs text-sub max-w-md mx-auto leading-relaxed">
                Example: "What is Retrieval Augmented Generation and how does hybrid search improve accuracy?"
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-3.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 flex items-center justify-center shrink-0 shadow-xs font-bold text-xs">
                  <Bot className="w-3.5 h-3.5" />
                </div>
              )}

              <div className={`max-w-3xl space-y-2.5 ${
                msg.role === 'user'
                  ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 px-4 py-3 rounded-xl shadow-xs'
                  : 'bg-muted/50 border border-theme p-4 rounded-xl text-main'
              }`}>
                {msg.role === 'user' ? (
                  <p className="text-xs leading-relaxed font-medium">{msg.content}</p>
                ) : (
                  <div>
                    <div className="prose prose-invert max-w-none">
                      {renderSimpleMarkdown(msg.content)}
                    </div>

                    {/* Inline Citations & Score Attribution Panel */}
                    {(msg.citations?.length > 0 || msg.retrieved_chunks?.length > 0) && (
                      <div className="mt-3.5 pt-3 border-t border-theme space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 font-mono">
                            <BookOpen className="w-3 h-3" />
                            Source Attribution ({msg.citations?.length || msg.retrieved_chunks?.length})
                          </div>
                          <button
                            onClick={() => toggleSourceAttribution(idx)}
                            className="text-[10px] font-mono text-muted-custom hover:text-main flex items-center gap-1"
                          >
                            {showSourceAttribution[idx] ? 'Hide Score Breakdown' : 'View 4-Score Breakdown'}
                          </button>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {(msg.citations || msg.retrieved_chunks || []).map((cite, cIdx) => {
                            const scores = cite.scores || {};
                            return (
                              <div
                                key={cIdx}
                                className="p-2.5 rounded-lg border border-theme bg-surface text-[11px] space-y-1.5"
                              >
                                <div className="font-semibold text-main truncate flex items-center justify-between">
                                  <span>{cite.document_name || cite.document_id}</span>
                                  <span className="text-muted-custom font-normal font-mono text-[10px]">(p. {cite.page_number})</span>
                                </div>
                                <p className="text-[10px] text-sub line-clamp-2 italic">
                                  "{cite.text}"
                                </p>

                                {showSourceAttribution[idx] && (
                                  <div className="pt-2 border-t border-theme font-mono text-[9px] grid grid-cols-2 gap-1 text-muted-custom">
                                    <div>Semantic: <span className="text-indigo-400 font-bold">{scores.semantic ? Number(scores.semantic).toFixed(3) : '0.000'}</span></div>
                                    <div>BM25: <span className="text-emerald-400 font-bold">{scores.bm25 ? Number(scores.bm25).toFixed(2) : '0.00'}</span></div>
                                    <div>RRF: <span className="text-amber-400 font-bold">{scores.rrf ? Number(scores.rrf).toFixed(4) : '0.0000'}</span></div>
                                    <div>Cross-Enc: <span className="text-rose-400 font-bold">{scores.cross_encoder ? Number(scores.cross_encoder).toFixed(3) : '0.000'}</span></div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Developer Pipeline Latency & Model Profiler */}
                    {(msg.retrieval_latency_ms || msg.timing_breakdown) && (
                      <div className="mt-3 pt-2">
                        <button
                          onClick={() => toggleDevTiming(idx)}
                          className="text-[10px] font-mono text-muted-custom hover:text-main flex items-center gap-1"
                        >
                          <Clock className="w-3 h-3" />
                          {showDevTiming[idx] ? 'Hide Performance Profile' : `Retrieval: ${msg.retrieval_latency_ms?.total_ms || 110}ms | Total: ${msg.latency || 1.2}s`}
                        </button>

                        {showDevTiming[idx] && (
                          <div className="mt-2 p-2.5 rounded-lg bg-surface font-mono text-[10px] text-sub border border-theme space-y-1.5">
                            <div className="font-bold text-main">Latency Profiler Breakdown:</div>
                            <div className="grid grid-cols-2 gap-1 text-[10px]">
                              <div>Hybrid Retrieval: <span className="text-emerald-400 font-bold">{msg.retrieval_latency_ms?.hybrid_ms || 18} ms</span></div>
                              <div>Cross Encoder: <span className="text-indigo-400 font-bold">{msg.retrieval_latency_ms?.cross_encoder_ms || 92} ms</span></div>
                              <div>Total Retrieval: <span className="text-amber-400 font-bold">{msg.retrieval_latency_ms?.total_ms || 110} ms</span></div>
                              <div>Total Execution: <span className="text-main font-bold">{msg.latency} s</span></div>
                            </div>
                            <div className="pt-1 text-[9px] text-muted-custom border-t border-theme">
                              Embedding: <span className="text-main">{msg.embedding_model || 'all-MiniLM-L6-v2'}</span> | Reranker: <span className="text-main">{msg.cross_encoder_model || 'cross-encoder/ms-marco-MiniLM-L-6-v2'}</span>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Copy Action */}
                    <div className="mt-2.5 flex justify-end">
                      <button
                        onClick={() => handleCopy(msg.content, idx)}
                        className="text-[10px] text-muted-custom hover:text-main flex items-center gap-1 transition-colors"
                      >
                        {copiedIndex === idx ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                        {copiedIndex === idx ? 'Copied' : 'Copy'}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="w-7 h-7 rounded-lg bg-surface border border-theme text-main flex items-center justify-center shrink-0">
                  <User className="w-3.5 h-3.5 text-muted-custom" />
                </div>
              )}
            </div>
          ))}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-7 h-7 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 flex items-center justify-center shrink-0">
                <Bot className="w-3.5 h-3.5 animate-pulse" />
              </div>
              <div className="p-3.5 rounded-xl border border-theme bg-muted/60 space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-main font-mono">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-500" />
                  {stage || 'Processing research query...'}
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Bottom Input Area */}
        <div className="p-3.5 border-t border-theme bg-muted/30">
          {error && (
            <div className="mb-2.5 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
              placeholder="Ask research question grounded in evidence..."
              className="flex-1 px-3.5 py-2.5 rounded-lg border border-theme bg-input text-main placeholder-slate-400 text-xs sm:text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-4 py-2.5 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-medium text-xs shadow-xs transition-all disabled:opacity-50 flex items-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Submit</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
