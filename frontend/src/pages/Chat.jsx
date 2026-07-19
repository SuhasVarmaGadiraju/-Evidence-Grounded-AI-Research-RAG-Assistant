import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Send,
  Loader2,
  AlertCircle,
  Copy,
  Check,
  RotateCcw,
  BookOpen,
  FileText,
  Clock,
  Cpu,
  Hash,
  Layers,
  Zap,
  ChevronDown,
  ChevronUp,
  Plus,
  Trash2,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  User,
  Bot
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

  // Fetch list of all active sessions
  const fetchSessions = async () => {
    try {
      const res = await api.get('/chat/sessions');
      if (res.success) {
        setSessions(res.sessions || []);
        // Select first active session if none selected
        if (!sessionId && res.sessions && res.sessions.length > 0) {
          loadSessionHistory(res.sessions[0].session_id);
        }
      }
    } catch (err) {
      console.error('Error fetching sessions:', err);
    }
  };

  // Load message history for selected session
  const loadSessionHistory = async (targetSessionId) => {
    try {
      setLoading(true);
      setSessionId(targetSessionId);
      setError(null);
      const res = await api.get(`/chat/history/${targetSessionId}`);
      if (res.success) {
        setMessages(res.messages || []);
      }
    } catch (err) {
      console.error('Error loading session history:', err);
      setError('Failed to load conversation history.');
    } finally {
      setLoading(false);
    }
  };

  // Create a new session
  const handleNewChat = async () => {
    try {
      setError(null);
      const res = await api.post('/chat/new', { title: 'New Conversation' });
      if (res.success) {
        setSessionId(res.session_id);
        setMessages([]);
        setQuery('');
        fetchSessions();
      }
    } catch (err) {
      console.error('Error creating new session:', err);
      // Local fallback
      setSessionId(null);
      setMessages([]);
      setQuery('');
    }
  };

  // Delete a session
  const handleDeleteSession = async (targetSessionId, e) => {
    e.stopPropagation();
    try {
      const res = await api.delete(`/chat/${targetSessionId}`);
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

  // Execute query turn
  const executeQuery = async (searchQuery) => {
    if (!searchQuery.trim() || loading) return;

    const currentQuery = searchQuery.trim();
    setLoading(true);
    setError(null);
    setQuery('');

    // Append user message immediately to local state for fast feedback
    const userMsg = { role: 'user', content: currentQuery, timestamp: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setStage('Searching Documents & Vector Index...');

    const stageTimer1 = setTimeout(() => {
      setStage('Reranking Candidates via Cross-Encoder...');
    }, 600);

    const stageTimer2 = setTimeout(() => {
      setStage('Building & Formatting Conversation Context...');
    }, 1200);

    const stageTimer3 = setTimeout(() => {
      setStage('Generating Grounded Answer via LLM...');
    }, 1800);

    try {
      const data = await api.post('/chat', {
        query: currentQuery,
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
          llm_latency: data.llm_latency,
          prompt_tokens: data.prompt_tokens,
          completion_tokens: data.completion_tokens,
          estimated_tokens: data.estimated_tokens,
          citations: data.citations || [],
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

  const renderSimpleMarkdown = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      let trimmed = line.trim();
      if (trimmed.startsWith('### ')) {
        return (
          <h3 key={idx} className="text-base font-bold text-slate-800 dark:text-slate-100 mt-3 mb-1">
            {trimmed.replace(/^###\s+/, '')}
          </h3>
        );
      } else if (trimmed.startsWith('## ')) {
        return (
          <h2 key={idx} className="text-lg font-bold text-slate-800 dark:text-slate-100 mt-4 mb-1">
            {trimmed.replace(/^##\s+/, '')}
          </h2>
        );
      } else if (trimmed.startsWith('# ')) {
        return (
          <h1 key={idx} className="text-xl font-extrabold text-slate-800 dark:text-slate-100 mt-4 mb-2">
            {trimmed.replace(/^#\s+/, '')}
          </h1>
        );
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        return (
          <li key={idx} className="ml-4 list-disc text-slate-700 dark:text-slate-300 text-sm my-0.5">
            {trimmed.replace(/^[-*]\s+/, '')}
          </li>
        );
      } else if (trimmed === '') {
        return <div key={idx} className="h-2" />;
      } else {
        return (
          <p key={idx} className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed my-1">
            {trimmed}
          </p>
        );
      }
    });
  };

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-4">
      {/* Sessions Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-0 hidden md:flex md:w-12'
        } transition-all duration-300 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3 flex flex-col justify-between shadow-sm shrink-0`}
      >
        <div className="space-y-3 overflow-hidden flex-1 flex flex-col">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <MessageSquare className="w-4 h-4 text-brand-500" />
              Conversations
            </span>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded"
              title="Toggle Sidebar"
            >
              {sidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
            </button>
          </div>

          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>

          {/* Session List */}
          <div className="flex-1 overflow-y-auto space-y-1 pr-1">
            {sessions.map((s) => (
              <div
                key={s.session_id}
                onClick={() => loadSessionHistory(s.session_id)}
                className={`group flex items-center justify-between p-2.5 rounded-lg text-xs cursor-pointer transition-colors ${
                  sessionId === s.session_id
                    ? 'bg-brand-50 dark:bg-brand-950/40 text-brand-700 dark:text-brand-300 font-semibold border border-brand-200 dark:border-brand-900'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                  <span className="truncate">{s.title || 'New Conversation'}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteSession(s.session_id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-500 transition-opacity"
                  title="Delete Session"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Chat Thread Window */}
      <div className="flex-1 flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden">
        {/* Header Bar */}
        <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded"
              >
                <PanelLeftOpen className="w-4 h-4" />
              </button>
            )}
            <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-500" />
              Multi-Turn Research Assistant
            </h2>
          </div>

          {sessionId && (
            <span className="font-mono text-[11px] text-slate-400 bg-slate-50 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
              Session: {sessionId.substring(0, 8)}...
            </span>
          )}
        </div>

        {/* Message Thread List */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.length === 0 && !loading && (
            <div className="text-center space-y-3 py-16 text-slate-400">
              <Sparkles className="w-10 h-10 text-brand-500/40 mx-auto" />
              <p className="font-semibold text-sm text-slate-700 dark:text-slate-300">
                Ask any research question to start the conversation.
              </p>
              <p className="text-xs">
                Supports multi-turn context memory with source citations & grounded answers.
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-3.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-full bg-brand-100 dark:bg-brand-950 flex items-center justify-center shrink-0 border border-brand-200 dark:border-brand-800 mt-1">
                  <Bot className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                </div>
              )}

              <div
                className={`max-w-3xl rounded-xl p-5 space-y-3 ${
                  msg.role === 'user'
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 shadow-sm'
                }`}
              >
                {/* User Message */}
                {msg.role === 'user' && <p className="text-sm font-medium leading-relaxed">{msg.content}</p>}

                {/* Assistant Message */}
                {msg.role === 'assistant' && (
                  <div className="space-y-4">
                    {/* Metadata Header Bar */}
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/60 dark:border-slate-800/80 pb-2 text-xs text-slate-500 dark:text-slate-400">
                      <div className="flex flex-wrap items-center gap-3">
                        {msg.cache_hit ? (
                          <span className="flex items-center gap-1 bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-semibold px-2 py-0.5 rounded text-[10px] border border-emerald-200 dark:border-emerald-800">
                            <Zap className="w-3 h-3 text-emerald-600" /> Cached
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-semibold px-2 py-0.5 rounded text-[10px] border border-blue-200 dark:border-blue-800">
                            <Sparkles className="w-3 h-3 text-blue-500" /> Live
                          </span>
                        )}

                        {msg.model && (
                          <span className="flex items-center gap-1 font-medium">
                            <Cpu className="w-3.5 h-3.5 text-indigo-500" /> {msg.model}
                          </span>
                        )}

                        {msg.latency && (
                          <span className="flex items-center gap-1 font-medium">
                            <Clock className="w-3.5 h-3.5 text-emerald-500" /> {msg.latency.toFixed(2)}s
                          </span>
                        )}

                        {msg.estimated_tokens && (
                          <span className="flex items-center gap-1 font-mono text-[10px]">
                            <Hash className="w-3.5 h-3.5 text-purple-500" /> Tokens: {msg.estimated_tokens}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        {msg.timing_breakdown && (
                          <button
                            onClick={() => toggleDevTiming(idx)}
                            className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded cursor-pointer"
                          >
                            <span>Timing</span>
                            {showDevTiming[idx] ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>
                        )}

                        <button
                          onClick={() => handleCopy(msg.content, idx)}
                          className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded cursor-pointer"
                        >
                          {copiedIndex === idx ? (
                            <Check className="w-3 h-3 text-emerald-500" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Developer Timing Breakdown Drawer */}
                    {showDevTiming[idx] && msg.timing_breakdown && (
                      <div className="bg-slate-900 text-slate-200 border border-slate-800 p-3 rounded-lg text-xs font-mono grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {Object.entries(msg.timing_breakdown).map(([k, v]) => (
                          <div key={k} className="bg-slate-950 p-1.5 rounded border border-slate-800 flex justify-between text-[10px]">
                            <span className="text-slate-400">{k}:</span>
                            <span className="font-bold text-slate-100">{typeof v === 'number' ? v.toFixed(4) : v}s</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Answer Markdown Body */}
                    <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed">
                      {renderSimpleMarkdown(msg.content)}
                    </div>

                    {/* Citations List */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="space-y-2 pt-2 border-t border-slate-200/60 dark:border-slate-800/80">
                        <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                          <BookOpen className="w-3.5 h-3.5 text-brand-500" /> Citations ({msg.citations.length})
                        </span>
                        <div className="grid grid-cols-1 gap-2">
                          {msg.citations.map((cite, cIdx) => (
                            <div
                              key={cIdx}
                              className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800 text-xs space-y-1 shadow-2xs"
                            >
                              <div className="flex justify-between items-center text-[11px] font-semibold text-slate-700 dark:text-slate-300">
                                <span>{cite.document_name} (Page {cite.page_number})</span>
                                <span className="font-mono text-[9px] text-slate-400">{cite.chunk_id}</span>
                              </div>
                              <p className="text-slate-500 dark:text-slate-400 italic text-[11px]">"{cite.text}"</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center shrink-0 border border-slate-300 dark:border-slate-700 mt-1">
                  <User className="w-4 h-4 text-slate-600 dark:text-slate-300" />
                </div>
              )}
            </div>
          ))}

          {/* Loading Indicator Progress */}
          {loading && (
            <div className="flex gap-3.5 justify-start">
              <div className="w-7 h-7 rounded-full bg-brand-100 dark:bg-brand-950 flex items-center justify-center shrink-0 border border-brand-200 dark:border-brand-800 mt-1">
                <Bot className="w-4 h-4 text-brand-600 dark:text-brand-400" />
              </div>

              <div className="bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 rounded-xl p-5 space-y-3 shadow-sm max-w-lg">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <Loader2 className="w-4 h-4 text-brand-500 animate-spin" />
                  <span>{stage || 'Processing multi-turn turn...'}</span>
                </div>
                <div className="space-y-2 pt-1">
                  <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded animate-pulse w-5/6" />
                  <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded animate-pulse w-4/6" />
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-800 dark:bg-red-950/20 dark:border-red-900/50 dark:text-red-300 rounded-xl flex items-center gap-2 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar Form */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a follow-up question or start a new topic..."
              className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:border-brand-500 focus:outline-none transition-colors"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="flex items-center gap-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 disabled:bg-brand-400 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors cursor-pointer disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Thinking...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Send Query
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
