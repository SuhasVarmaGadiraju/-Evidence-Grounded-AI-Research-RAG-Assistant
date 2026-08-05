import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  BrainCircuit,
  Search,
  Sparkles,
  ShieldCheck,
  Zap,
  BookOpen,
  Layers,
  BarChart3,
  CheckCircle2,
  ChevronDown,
  ArrowRight,
  FileText,
  Lock,
  Cpu,
  Globe2,
  Sun,
  Moon,
  Upload,
  FileCode,
  Split,
  Binary,
  Database,
  GitMerge,
  ArrowDownUp,
  Bot,
  Terminal,
  Server,
  Code2,
  Box,
  Key,
  Check,
  Workflow
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

export default function LandingPage() {
  const { isDark, toggleTheme } = useTheme();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [openFaq, setOpenFaq] = useState(null);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const pipelineSteps = [
    {
      step: '01',
      title: 'Upload PDF',
      icon: Upload,
      description: 'Ingest multi-page research papers and documentation.',
    },
    {
      step: '02',
      title: 'Document Parsing',
      icon: FileCode,
      description: 'Extract raw text, layout structure, and metadata.',
    },
    {
      step: '03',
      title: 'Semantic Chunking',
      icon: Split,
      description: 'Split text into overlapping chunks for context preservation.',
    },
    {
      step: '04',
      title: 'Embedding Generation',
      icon: Binary,
      description: 'Compute 384-dim dense vectors with SentenceTransformers.',
    },
    {
      step: '05',
      title: 'FAISS Vector Database',
      icon: Database,
      description: 'Index embeddings into high-performance FAISS vector store.',
    },
    {
      step: '06',
      title: 'Hybrid Retrieval',
      icon: GitMerge,
      description: 'Combine FAISS vector search + BM25 keyword matching via RRF.',
    },
    {
      step: '07',
      title: 'Cross-Encoder Reranking',
      icon: ArrowDownUp,
      description: 'Re-score top candidates using Hugging Face Cross-Encoder.',
    },
    {
      step: '08',
      title: 'LLM Response Gen',
      icon: Bot,
      description: 'Prompt NVIDIA Llama-3.1 8B with top reranked evidence.',
    },
    {
      step: '09',
      title: 'Source-Cited Answer',
      icon: ShieldCheck,
      description: 'Synthesize verifiable response with page-level citations.',
    },
  ];

  const techStack = [
    { name: 'Python', category: 'Backend Engine', icon: Terminal, color: 'text-amber-500 bg-amber-500/10 border-amber-500/20' },
    { name: 'Flask', category: 'REST API', icon: Server, color: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20' },
    { name: 'React', category: 'Frontend UI', icon: Code2, color: 'text-sky-500 bg-sky-500/10 border-sky-500/20' },
    { name: 'Tailwind CSS', category: 'Design System', icon: Sparkles, color: 'text-cyan-500 bg-cyan-500/10 border-cyan-500/20' },
    { name: 'FAISS', category: 'Vector Search', icon: Database, color: 'text-indigo-500 bg-indigo-500/10 border-indigo-500/20' },
    { name: 'BM25', category: 'Lexical Retrieval', icon: Search, color: 'text-violet-500 bg-violet-500/10 border-violet-500/20' },
    { name: 'Sentence Transformers', category: 'Dense Embeddings', icon: Binary, color: 'text-blue-500 bg-blue-500/10 border-blue-500/20' },
    { name: 'Hugging Face Cross-Encoder', category: 'Passage Reranker', icon: ArrowDownUp, color: 'text-orange-500 bg-orange-500/10 border-orange-500/20' },
    { name: 'NVIDIA NIM / Llama', category: 'LLM Inference', icon: Cpu, color: 'text-green-500 bg-green-500/10 border-green-500/20' },
    { name: 'Firebase Authentication', category: 'Identity Provider', icon: Key, color: 'text-amber-600 bg-amber-600/10 border-amber-600/20' },
    { name: 'Docker', category: 'Containerization', icon: Box, color: 'text-blue-600 bg-blue-600/10 border-blue-600/20' },
    { name: 'Render', category: 'Cloud Hosting', icon: Globe2, color: 'text-purple-500 bg-purple-500/10 border-purple-500/20' },
  ];

  const keyFeatures = [
    { title: 'Evidence-Grounded Answers', desc: 'Strict anti-hallucination system prompt constraints ensuring responses rely solely on retrieved evidence context.' },
    { title: 'Hybrid Retrieval', desc: 'Dual-stage retrieval fusing FAISS semantic vector search with BM25 sparse keyword matching using Reciprocal Rank Fusion (RRF).' },
    { title: 'Cross-Encoder Reranking', desc: 'Precision re-scoring of candidate passages with ms-marco-MiniLM-L-6-v2 for optimal context relevance.' },
    { title: 'PDF Document Chat', desc: 'Interactive chat interface to query multi-page PDF research papers, documentation, and technical literature.' },
    { title: 'Source Citations', desc: 'Every AI answer includes direct inline citations pinpointing exact source document names and page numbers.' },
    { title: 'Google Authentication', desc: 'Secure single sign-on powered by Firebase Authentication with Google Identity Provider integration.' },
    { title: 'Enterprise Dashboard', desc: 'Comprehensive control center to manage uploaded documents, inspect vector stores, and run search diagnostics.' },
    { title: 'RAG Evaluation Metrics', desc: 'Automated auditing framework measuring Faithfulness, Context Recall, Answer Relevancy, and Context Precision.' },
  ];

  const faqs = [
    {
      q: 'What is Evidence AI?',
      a: 'Evidence AI is an open-source, evidence-grounded Retrieval-Augmented Generation (RAG) research platform built to showcase advanced information retrieval, cross-encoder reranking, and LLM context synthesis.',
    },
    {
      q: 'How does the hybrid search engine work?',
      a: 'The system indexes documents into both a FAISS dense vector index (SentenceTransformers) and a BM25 sparse keyword index. Queries retrieve candidates from both indices, which are then merged using Reciprocal Rank Fusion (RRF).',
    },
    {
      q: 'How are hallucinations prevented?',
      a: 'Top retrieved passages undergo a second pass through a Cross-Encoder reranker. The LLM system prompt explicitly mandates citing source documents and page numbers, instructing the model to refuse answering if context is insufficient.',
    },
    {
      q: 'Can I test individual search components?',
      a: 'Yes! The application includes dedicated diagnostic pages for testing Semantic Search, BM25 Search, Hybrid Fusion, and Reranking independently.',
    },
  ];

  return (
    <div className={`min-h-screen ${isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-faf9f6 text-zinc-900'}`}>
      {/* 1. Public Top Navigation */}
      <header className={`sticky top-0 z-50 backdrop-blur-md border-b ${isDark ? 'bg-zinc-950/90 border-zinc-800' : 'bg-white/90 border-zinc-200'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to={isAuthenticated ? "/dashboard" : "/"} className="flex items-center gap-3 group cursor-pointer" title="Evidence AI">
            <div className="w-8 h-8 rounded-lg bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center text-white dark:text-zinc-900 font-bold shadow-xs">
              <BrainCircuit className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-sm tracking-tight text-main">Evidence AI</span>
              <span className="ml-2 text-[10px] font-mono px-2 py-0.5 rounded font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                RAG Architecture
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 text-xs font-medium">
            <a href="#pipeline" className="text-sub hover:text-main transition-colors">RAG Pipeline</a>
            <a href="#techstack" className="text-sub hover:text-main transition-colors">Tech Stack</a>
            <a href="#features" className="text-sub hover:text-main transition-colors">Key Features</a>
            <a href="#faq" className="text-sub hover:text-main transition-colors">FAQs</a>
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-lg border transition-colors ${
                isDark ? 'border-zinc-800 hover:bg-zinc-900 text-zinc-400' : 'border-zinc-200 hover:bg-zinc-100 text-zinc-600'
              }`}
              title="Toggle theme"
            >
              {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-zinc-600" />}
            </button>

            {isAuthenticated ? (
              <button
                onClick={() => navigate('/dashboard')}
                className="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-medium text-xs shadow-xs transition-all flex items-center gap-2"
              >
                Go to Dashboard
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <>
                <Link
                  to="/login"
                  className={`px-3.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                    isDark ? 'hover:bg-zinc-900 text-zinc-300' : 'hover:bg-zinc-100 text-zinc-700'
                  }`}
                >
                  Log In
                </Link>
                <Link
                  to="/login"
                  className="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 text-xs font-semibold shadow-xs transition-all"
                >
                  Explore Platform
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* 2. Hero Section */}
      <section className="relative overflow-hidden pt-16 pb-16 lg:pt-24 lg:pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-mono font-medium bg-zinc-100 dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300 border border-theme mb-6">
            <Sparkles className="w-3.5 h-3.5 text-emerald-500" />
            AI Engineering Portfolio • Enterprise RAG Assistant
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight max-w-4xl mx-auto leading-tight">
            AI-Powered Research. Grounded in Evidence.
          </h1>

          <p className={`mt-4 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
            Demonstrating enterprise-grade Retrieval-Augmented Generation using Hybrid Vector + Lexical Search, Cross-Encoder Reranking, and NVIDIA Llama-3.1 inference with verifiable page citations.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center items-center">
            <button
              onClick={() => navigate(isAuthenticated ? '/dashboard' : '/login')}
              className="w-full sm:w-auto px-6 py-3 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-semibold text-xs shadow-xs transition-all flex items-center justify-center gap-2"
            >
              Access RAG Workspace
              <ArrowRight className="w-4 h-4" />
            </button>
            <a
              href="#pipeline"
              className={`w-full sm:w-auto px-6 py-3 rounded-lg font-semibold text-xs border transition-all flex items-center justify-center gap-2 ${
                isDark ? 'border-zinc-800 hover:bg-zinc-900 text-zinc-300' : 'border-zinc-300 hover:bg-zinc-100 text-zinc-700'
              }`}
            >
              <Workflow className="w-4 h-4 text-emerald-500" />
              View RAG Pipeline
            </a>
          </div>

          {/* Interactive RAG Platform Preview Graphic */}
          <div className="mt-12 max-w-5xl mx-auto rounded-xl p-1.5 bg-muted/60 border border-theme shadow-xl overflow-hidden">
            <div className={`rounded-lg p-4 sm:p-5 ${isDark ? 'bg-zinc-900' : 'bg-white'}`}>
              <div className="flex items-center justify-between border-b pb-3 mb-3 border-theme">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-rose-500"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-500"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
                  <span className="ml-2 text-xs font-mono text-muted-custom">evidence-ai // RAG Architecture Console</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  Latency: 2.89s | Faithfulness: 98.4%
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-left">
                {/* Stage 1 */}
                <div className={`p-3.5 rounded-lg border ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'}`}>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-muted-custom font-mono mb-1">Stage 1: Hybrid Retrieval</div>
                  <div className="text-xs font-semibold text-main mb-1">FAISS (Dense) + BM25 (Sparse)</div>
                  <p className="text-xs text-sub leading-relaxed">Queried 52 vectors and tokenized terms. Merged via RRF in 92.4ms.</p>
                </div>
                {/* Stage 2 */}
                <div className={`p-3.5 rounded-lg border ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'}`}>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-muted-custom font-mono mb-1">Stage 2: Cross-Encoder Rerank</div>
                  <div className="text-xs font-semibold text-main mb-1">ms-marco-MiniLM-L-6-v2</div>
                  <p className="text-xs text-sub leading-relaxed">Re-scored top 20 candidates into top 5 evidence blocks in 243.8ms.</p>
                </div>
                {/* Stage 3 */}
                <div className={`p-3.5 rounded-lg border ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'}`}>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-muted-custom font-mono mb-1">Stage 3: Grounded Answer</div>
                  <div className="text-xs font-semibold text-main mb-1">NVIDIA Llama-3.1 8B</div>
                  <p className="text-xs text-sub leading-relaxed">Generated 384 tokens with inline [Doc, Page X] citations in 2.55s.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. System Architecture / RAG Pipeline Section */}
      <section id="pipeline" className={`py-16 border-t ${isDark ? 'border-zinc-900 bg-zinc-950' : 'border-zinc-200 bg-zinc-100/50'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded font-mono text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 mb-3">
              <Workflow className="w-3.5 h-3.5" />
              END-TO-END DATAFLOW
            </div>
            <h2 className="text-2xl sm:text-4xl font-bold tracking-tight">
              RAG Pipeline Architecture
            </h2>
            <p className={`mt-2 text-xs sm:text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              A modular 9-stage pipeline designed for precise context retrieval, re-ranking, and citation-backed LLM response generation.
            </p>
          </div>

          {/* Workflow Pipeline Display */}
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-3 gap-4">
            {pipelineSteps.map((stepItem, idx) => {
              const StepIcon = stepItem.icon;
              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border relative transition-all hover:scale-[1.01] ${
                    isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-9 h-9 rounded-lg bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 flex items-center justify-center">
                      <StepIcon className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-mono font-bold text-muted-custom px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800">
                      {stepItem.step}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold mb-1 text-main">{stepItem.title}</h3>
                  <p className={`text-xs leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                    {stepItem.description}
                  </p>

                  {idx < pipelineSteps.length - 1 && (
                    <div className="hidden lg:block absolute -right-2.5 top-1/2 -translate-y-1/2 z-10 text-muted-custom">
                      {/* Arrow indicator between steps if horizontal grid */}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 4. Technology Stack Section */}
      <section id="techstack" className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <span className="text-xs font-semibold text-muted-custom font-mono uppercase tracking-widest">Engineering Components</span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mt-1">
              Technology Stack
            </h2>
            <p className={`mt-2 text-xs sm:text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Built using industry-standard machine learning libraries, vector databases, and modern web frameworks.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {techStack.map((tech, idx) => {
              const TechIcon = tech.icon;
              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border flex items-center gap-3 transition-all hover:border-zinc-400 dark:hover:border-zinc-700 ${
                    isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg border flex items-center justify-center flex-shrink-0 ${tech.color}`}>
                    <TechIcon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-main">{tech.name}</h3>
                    <span className="text-[10px] text-muted-custom font-mono">{tech.category}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 5. Key Features Section */}
      <section id="features" className={`py-16 border-t ${isDark ? 'border-zinc-900 bg-zinc-950' : 'border-zinc-200 bg-zinc-100/50'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Key Capabilities
            </h2>
            <p className={`mt-2 text-xs sm:text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Core features designed for verifiable academic research and rigorous document analysis.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {keyFeatures.map((feat, idx) => (
              <div
                key={idx}
                className={`p-5 rounded-xl border flex flex-col justify-between ${
                  isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-5 h-5 rounded bg-emerald-500/10 text-emerald-500 flex items-center justify-center flex-shrink-0">
                      <Check className="w-3.5 h-3.5 stroke-[3]" />
                    </div>
                    <h3 className="text-xs font-bold text-main">{feat.title}</h3>
                  </div>
                  <p className={`text-xs leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                    {feat.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. FAQ Section */}
      <section id="faq" className="py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Frequently Asked Questions</h2>
          </div>

          <div className="space-y-3">
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                className={`rounded-lg border overflow-hidden ${
                  isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
                }`}
              >
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full p-4 text-left font-semibold text-xs sm:text-sm flex justify-between items-center"
                >
                  <span>{faq.q}</span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${openFaq === idx ? 'rotate-180' : ''}`} />
                </button>
                {openFaq === idx && (
                  <div className={`p-4 pt-0 text-xs leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 7. Public Footer */}
      <footer className={`border-t py-10 ${isDark ? 'border-zinc-900 bg-zinc-950 text-zinc-400' : 'border-zinc-200 bg-zinc-900 text-zinc-400'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-zinc-800 flex items-center justify-center text-white font-bold text-xs">
              <BrainCircuit className="w-4 h-4" />
            </div>
            <span className="font-bold text-xs text-white tracking-tight">Evidence AI • RAG Research Platform</span>
          </div>
          <p className="text-[11px] text-zinc-500 font-mono">
            © {new Date().getFullYear()} Evidence AI. Built with Flask, FAISS, SentenceTransformers & NVIDIA Llama 3.1.
          </p>
        </div>
      </footer>
    </div>
  );
}

