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

  const fetchSessions = async () => {
    try {
      const res = await api.get('/chat/sessions');
      if (res.success) {
        setSessions(res.sessions || []);
        if (!sessionId && res.sessions && res.sessions.length > 0) {
          loadSessionHistory(res.sessions[0].session_id);
        }
      }
    } catch (err) {
      console.error('Error fetching sessions:', err);
    }
  };

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
      setSessionId(null);
      setMessages([]);
      setQuery('');
    }
  };

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

  const executeQuery = async (searchQuery) => {
    if (!searchQuery.trim() || loading) return;

    const currentQuery = searchQuery.trim();
    setLoading(true);
    setError(null);
    setQuery('');

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
      {/* Sessions Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-0 hidden md:flex md:w-12'
        } transition-all duration-300 rounded-2xl p-3 flex flex-col justify-between border border-theme bg-surface shrink-0`}
      >
        <div className="space-y-3 overflow-hidden flex-1 flex flex-col">
          <div className="flex items-center justify-between px-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-custom flex items-center gap-1.5 font-mono">
              <MessageSquare className="w-3.5 h-3.5 text-brand-500" />
              Sessions
            </span>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-muted-custom hover:text-main p-1 rounded transition-colors"
              title="Toggle Sidebar"
            >
              {sidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
            </button>
          </div>

          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>

          {/* Session List */}
          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {sessions.map((s) => (
              <div
                key={s.session_id}
                onClick={() => loadSessionHistory(s.session_id)}
                className={`group flex items-center justify-between p-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                  sessionId === s.session_id
                    ? 'bg-brand-500/10 text-brand-500 font-semibold border border-brand-500/20'
                    : 'text-sub hover:bg-muted hover:text-main'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0 text-muted-custom" />
                  <span className="truncate">{s.title || 'New Conversation'}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteSession(s.session_id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-muted-custom hover:text-red-500 transition-opacity"
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
      <div className="flex-1 flex flex-col rounded-2xl border border-theme bg-card overflow-hidden">
        {/* Top Chat Bar */}
        <div className="p-4 border-b border-theme bg-muted flex items-center justify-between">
          <div className="flex items-center gap-2">
            {!sidebarOpen && (
              <button onClick={() => setSidebarOpen(true)} className="text-muted-custom hover:text-main p-1">
                <PanelLeftOpen className="w-4 h-4" />
              </button>
            )}
            <h2 className="text-xs font-bold uppercase tracking-wider flex items-center gap-2 text-main font-mono">
              <Sparkles className="w-4 h-4 text-brand-500" />
              AI Chat (RAG)
            </h2>
          </div>

          {sessionId && (
            <span className="font-mono text-[10px] text-brand-500 bg-brand-500/10 px-2.5 py-1 rounded-full border border-brand-500/20">
              Session: {sessionId.substring(0, 8)}...
            </span>
          )}
        </div>

        {/* Message Thread Area */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.length === 0 && !loading && (
            <div className="text-center space-y-3 py-20 text-muted-custom">
              <div className="w-12 h-12 rounded-2xl bg-brand-500/10 text-brand-500 border border-brand-500/20 flex items-center justify-center mx-auto">
                <Bot className="w-6 h-6" />
              </div>
              <p className="font-semibold text-sm text-main">
                Ask any research question to start the evidence-grounded session.
              </p>
              <p className="text-xs text-sub max-w-sm mx-auto">
                Example: "What is Retrieval Augmented Generation and how does hybrid search improve accuracy?"
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-xl bg-brand-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className={`max-w-3xl space-y-3 ${
                msg.role === 'user'
                  ? 'bg-brand-600 text-white p-4 rounded-2xl shadow-sm'
                  : 'bg-muted border border-theme p-5 rounded-2xl text-main'
              }`}>
                {msg.role === 'user' ? (
                  <p className="text-xs leading-relaxed font-medium">{msg.content}</p>
                ) : (
                  <div>
                    <div className="prose prose-invert max-w-none">
                      {renderSimpleMarkdown(msg.content)}
                    </div>

                    {/* Inline Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-theme space-y-2">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-brand-500 flex items-center gap-1.5 font-mono">
                          <BookOpen className="w-3.5 h-3.5" />
                          Source Citations ({msg.citations.length})
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {msg.citations.map((cite, cIdx) => (
                            <div
                              key={cIdx}
                              className="p-2.5 rounded-xl border border-theme bg-card text-[11px] space-y-1"
                            >
                              <div className="font-semibold text-brand-500 truncate">
                                {cite.document_name} (Page {cite.page_number})
                              </div>
                              <p className="text-[10px] text-sub line-clamp-2 italic">
                                "{cite.text}"
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Developer Pipeline Latency Breakdown */}
                    {msg.timing_breakdown && (
                      <div className="mt-3 pt-2">
                        <button
                          onClick={() => toggleDevTiming(idx)}
                          className="text-[10px] font-mono text-muted-custom hover:text-brand-500 flex items-center gap-1"
                        >
                          <Clock className="w-3 h-3" />
                          {showDevTiming[idx] ? 'Hide Timing Profile' : `Latency: ${msg.latency}s (LLM: ${msg.llm_latency}s)`}
                        </button>
                        {showDevTiming[idx] && (
                          <div className="mt-2 p-3 rounded-xl bg-card font-mono text-[10px] text-sub border border-theme space-y-1">
                            <div>Total Latency: {msg.latency}s</div>
                            <div>LLM Generation: {msg.llm_latency}s</div>
                            {msg.timing_breakdown.ms && (
                              <pre className="text-[9px] text-emerald-500 pt-1">
                                {JSON.stringify(msg.timing_breakdown.ms, null, 2)}
                              </pre>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Copy Button */}
                    <div className="mt-3 flex justify-end">
                      <button
                        onClick={() => handleCopy(msg.content, idx)}
                        className="text-[10px] text-muted-custom hover:text-main flex items-center gap-1"
                      >
                        {copiedIndex === idx ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                        {copiedIndex === idx ? 'Copied' : 'Copy'}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-xl bg-muted border border-theme text-main flex items-center justify-center shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {/* Loading Skeleton */}
          {loading && (
            <div className="flex gap-4 justify-start">
              <div className="w-8 h-8 rounded-xl bg-brand-600 text-white flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 animate-pulse" />
              </div>
              <div className="p-4 rounded-2xl border border-theme bg-muted space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-brand-500 font-mono">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {stage || 'Processing query pipeline...'}
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-theme bg-muted">
          {error && (
            <div className="mb-3 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-xs flex items-center gap-2">
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
              className="flex-1 px-4 py-3 rounded-xl border border-theme bg-input text-main placeholder-slate-400 text-xs sm:text-sm font-medium focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-5 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs shadow-sm transition-all disabled:opacity-50 flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              <span>Submit</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
