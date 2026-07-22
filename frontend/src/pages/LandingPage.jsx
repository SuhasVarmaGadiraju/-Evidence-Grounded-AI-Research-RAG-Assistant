import React, { useState } from 'react';
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
  Users,
  Quote,
  HelpCircle,
  Sun,
  Moon
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

export default function LandingPage() {
  const { isDark, toggleTheme } = useTheme();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [openFaq, setOpenFaq] = useState(null);

  const features = [
    {
      icon: Layers,
      title: 'Hybrid Retrieval Engine',
      description: 'Combines dense FAISS vector embeddings with BM25 keyword search using Reciprocal Rank Fusion (RRF).',
    },
    {
      icon: Cpu,
      title: 'Cross-Encoder Reranking',
      description: 'Re-scores candidate evidence passages with HuggingFace Cross-Encoders for pinpoint precision.',
    },
    {
      icon: ShieldCheck,
      title: '100% Citation Grounding',
      description: 'Every answer snippet is explicitly cited with precise document names and page numbers.',
    },
    {
      icon: BarChart3,
      title: 'RAGAS Quality Metrics',
      description: 'Automated evaluation framework measuring Faithfulness, Context Recall, Answer Relevancy, and Precision.',
    },
    {
      icon: Sparkles,
      title: 'Prompt Optimization Studio',
      description: 'Fine-tune system prompts with context budget minification, token counter, and live template preview.',
    },
    {
      icon: Zap,
      title: 'Low-Latency NVIDIA LLM',
      description: 'Powered by NVIDIA Llama-3.1 8B Instruct with persistent connection pooling for sub-3s response speeds.',
    },
  ];

  const workflowSteps = [
    {
      step: '01',
      title: 'Ingest Research PDFs',
      desc: 'Upload multi-page research papers, documentation, or textbooks. Text is extracted, chunked, and tokenized automatically.',
    },
    {
      step: '02',
      title: 'Hybrid Vector & Lexical Indexing',
      desc: 'Generates 384-dim SentenceTransformer embeddings into FAISS while indexing key terms into BM25.',
    },
    {
      step: '03',
      title: 'Reranked RAG Chat',
      desc: 'Query the AI assistant to receive grounded answers complete with inline citations [Paper, Page X].',
    },
    {
      step: '04',
      title: 'Automated Audit',
      desc: 'Run automated RAGAS audits to verify context recall, hallucination prevention, and faithfulness scores.',
    },
  ];

  const pricingPlans = [
    {
      name: 'Starter Academic',
      price: '$0',
      period: 'Forever free',
      desc: 'Ideal for students, individual researchers, and open-source testing.',
      features: [
        'Up to 50 PDF Document Ingestions',
        'Hybrid Semantic + BM25 Search',
        'Cross-Encoder Candidate Reranking',
        'Standard RAG Citation Grounding',
        'Basic Evaluation Metrics',
      ],
      cta: 'Start Free Trial',
      popular: false,
    },
    {
      name: 'Pro Researcher',
      price: '$29',
      period: 'per user / month',
      desc: 'For professional researchers, data scientists, and research labs.',
      features: [
        'Unlimited PDF Document Storage',
        'High-Speed NVIDIA Llama-3.1 LLM',
        'Full RAGAS Quality Audit Suite',
        'Prompt Minification & Studio',
        'Exportable Evaluation Reports',
        'Priority API Latency Route',
      ],
      cta: 'Get Started Pro',
      popular: true,
    },
    {
      name: 'Enterprise Lab',
      price: 'Custom',
      period: 'Tailored deployment',
      desc: 'Dedicated infrastructure with custom LLM endpoints & security SLA.',
      features: [
        'Custom Fine-Tuned Embedding Models',
        'On-Premise / Private Cloud Vector Store',
        'Dedicated Connection Pools',
        'Custom Evaluation Metrics',
        'Role-Based Admin Access',
        '24/7 Priority Support SLA',
      ],
      cta: 'Contact Sales',
      popular: false,
    },
  ];

  const testimonials = [
    {
      quote:
        'Evidence AI completely transformed how our team reads through literature. The inline citations down to exact page numbers save us hours of manual fact-checking.',
      author: 'Dr. Aris Thorne',
      title: 'Lead AI Researcher, BioTech Labs',
    },
    {
      quote:
        'The transparent breakdown between BM25 lexical search and FAISS vector retrieval makes this the best RAG platform for production auditing.',
      author: 'Elena Rostova',
      title: 'Senior NLP Engineer, DeepTech Inc.',
    },
  ];

  const faqs = [
    {
      q: 'How does Evidence AI prevent LLM hallucinations?',
      a: 'We use a strict two-stage retrieval pipeline (FAISS + BM25 + Cross-Encoder) coupled with a system prompt that mandates explicit evidence citations. If relevant context is missing, the model explicitly notifies the user.',
    },
    {
      q: 'Can I test individual search components like BM25 or Reranking?',
      a: 'Yes! The platform includes dedicated diagnostic tools for Semantic Search, BM25 Search, Hybrid Fusion, and Cross-Encoder Reranking so you can analyze retrieval performance independently.',
    },
    {
      q: 'How is response latency kept low?',
      a: 'We use persistent HTTP session connection pooling for the NVIDIA Llama-3.1 API and maintain singletons in memory for SentenceTransformers and FAISS indexes.',
    },
    {
      q: 'What formats of documents are supported?',
      a: 'Currently, multi-page PDFs with text layers are fully supported. OCR and text file formats are in active development.',
    },
  ];

  return (
    <div className={`min-h-screen ${isDark ? 'bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
      {/* 1. Public Top Navigation */}
      <header className={`sticky top-0 z-50 backdrop-blur-md border-b ${isDark ? 'bg-slate-950/80 border-slate-800' : 'bg-white/80 border-slate-200'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-brand-500/20">
              <BrainCircuit className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight">Evidence AI</span>
              <span className="ml-2 text-xs px-2 py-0.5 rounded-full font-semibold bg-brand-500/10 text-brand-500 border border-brand-500/20">
                SaaS v1.0
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium">
            <a href="#features" className="hover:text-brand-500 transition-colors">Features</a>
            <a href="#workflow" className="hover:text-brand-500 transition-colors">How it Works</a>
            <a href="#pricing" className="hover:text-brand-500 transition-colors">Pricing</a>
            <a href="#faq" className="hover:text-brand-500 transition-colors">FAQs</a>
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-lg border transition-colors ${
                isDark ? 'border-slate-800 hover:bg-slate-900 text-slate-400' : 'border-slate-200 hover:bg-slate-100 text-slate-600'
              }`}
              title="Toggle theme"
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {isAuthenticated ? (
              <button
                onClick={() => navigate('/dashboard')}
                className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm transition-all shadow-md shadow-brand-600/20 flex items-center gap-2"
              >
                Go to Dashboard
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <>
                <Link
                  to="/login"
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isDark ? 'hover:bg-slate-900 text-slate-300' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  Log In
                </Link>
                <Link
                  to="/signup"
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white text-sm font-semibold shadow-md shadow-brand-500/20 transition-all hover:scale-[1.02]"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* 2. Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-16 lg:pt-28 lg:pb-24">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-brand-500/10 blur-[120px] rounded-full pointer-events-none"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-brand-500/10 border border-brand-500/20 text-brand-400 mb-8 animate-fade-in">
            <Sparkles className="w-3.5 h-3.5 text-brand-400" />
            Next-Generation Evidence-Grounded AI Research Assistant
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight max-w-4xl mx-auto leading-tight sm:leading-none">
            Research with <span className="text-gradient">Zero Hallucinations</span> and 100% Citations
          </h1>

          <p className={`mt-6 text-lg sm:text-xl max-w-2xl mx-auto font-normal ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Accelerate literature reviews, paper analysis, and academic writing using Hybrid Vector-Lexical Search, Cross-Encoder Reranking, and automated RAGAS quality auditing.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button
              onClick={() => navigate(isAuthenticated ? '/dashboard' : '/signup')}
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-semibold text-base shadow-xl shadow-brand-500/25 transition-all hover:scale-[1.02] flex items-center justify-center gap-2"
            >
              Start Free Research Workspace
              <ArrowRight className="w-5 h-5" />
            </button>
            <a
              href="#workflow"
              className={`w-full sm:w-auto px-8 py-4 rounded-xl font-semibold text-base border transition-all flex items-center justify-center gap-2 ${
                isDark ? 'border-slate-800 hover:bg-slate-900 text-slate-300' : 'border-slate-300 hover:bg-slate-100 text-slate-700'
              }`}
            >
              Explore Architecture
            </a>
          </div>

          {/* Interactive RAG Platform Preview Graphic */}
          <div className="mt-16 max-w-5xl mx-auto rounded-2xl p-2 bg-gradient-to-b from-brand-500/20 to-indigo-500/10 border border-slate-800 shadow-2xl overflow-hidden">
            <div className={`rounded-xl p-4 sm:p-6 ${isDark ? 'bg-slate-900' : 'bg-white'}`}>
              <div className="flex items-center justify-between border-b pb-4 mb-4 border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
                  <span className="ml-2 text-xs font-mono text-slate-500">evidence-ai // RAG Studio Console</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-brand-400 font-mono">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  Latency: 2.89s | Faithfulness: 98.4%
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
                {/* Stage 1 */}
                <div className={`p-4 rounded-lg border ${isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                  <div className="text-xs font-semibold text-brand-400 uppercase tracking-wider mb-2">Stage 1: Hybrid Retrieval</div>
                  <div className="text-sm font-medium mb-1">FAISS (Dense) + BM25 (Sparse)</div>
                  <p className="text-xs text-slate-400">Queried 52 vectors and tokenized terms. Merged via RRF in 92.4ms.</p>
                </div>
                {/* Stage 2 */}
                <div className={`p-4 rounded-lg border ${isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                  <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-2">Stage 2: Cross-Encoder Rerank</div>
                  <div className="text-sm font-medium mb-1">ms-marco-MiniLM-L-6-v2</div>
                  <p className="text-xs text-slate-400">Re-scored top 20 candidates into top 5 evidence blocks in 243.8ms.</p>
                </div>
                {/* Stage 3 */}
                <div className={`p-4 rounded-lg border ${isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                  <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Stage 3: Grounded Answer</div>
                  <div className="text-sm font-medium mb-1">NVIDIA Llama-3.1 8B</div>
                  <p className="text-xs text-slate-400">Generated 384 tokens with inline [Doc, Page X] citations in 2.55s.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Features Section */}
      <section id="features" className={`py-20 border-t ${isDark ? 'border-slate-900 bg-slate-950/50' : 'border-slate-200 bg-slate-100/50'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Engineered for Rigorous Academic & Clinical Research
            </h2>
            <p className={`mt-4 text-base sm:text-lg ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              Built on production-grade RAG principles so you can query complex technical literature with verifiable accuracy.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((f, i) => (
              <div
                key={i}
                className={`p-6 rounded-2xl border glow-card transition-all ${
                  isDark ? 'bg-slate-900/60 border-slate-800 hover:border-brand-500/50' : 'bg-white border-slate-200 hover:border-brand-500/50'
                }`}
              >
                <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 mb-5">
                  <f.icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold mb-2">{f.title}</h3>
                <p className={`text-sm leading-relaxed ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. Workflow Steps */}
      <section id="workflow" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-semibold text-brand-400 uppercase tracking-widest">End-to-End Pipeline</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
              How Evidence AI Works
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {workflowSteps.map((ws, idx) => (
              <div
                key={idx}
                className={`p-6 rounded-2xl border relative ${
                  isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
                }`}
              >
                <span className="text-4xl font-extrabold text-brand-500/20 font-mono mb-4 block">{ws.step}</span>
                <h3 className="text-lg font-bold mb-2">{ws.title}</h3>
                <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{ws.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 5. Pricing Table */}
      <section id="pricing" className={`py-20 border-t ${isDark ? 'border-slate-900 bg-slate-950/40' : 'border-slate-200 bg-slate-100/40'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Flexible Plans for Every Researcher</h2>
            <p className={`mt-4 text-base sm:text-lg ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              Transparent pricing with no hidden tokens or surprise fees.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {pricingPlans.map((plan, i) => (
              <div
                key={i}
                className={`p-8 rounded-2xl border flex flex-col justify-between relative ${
                  plan.popular
                    ? 'bg-slate-900 border-brand-500 shadow-2xl shadow-brand-500/10'
                    : isDark
                    ? 'bg-slate-900/60 border-slate-800'
                    : 'bg-white border-slate-200'
                }`}
              >
                {plan.popular && (
                  <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold bg-brand-500 text-white uppercase tracking-wider">
                    Most Popular
                  </span>
                )}
                <div>
                  <h3 className="text-xl font-bold">{plan.name}</h3>
                  <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{plan.desc}</p>
                  <div className="mt-6 mb-6">
                    <span className="text-4xl font-extrabold">{plan.price}</span>
                    <span className={`text-xs ml-2 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{plan.period}</span>
                  </div>
                  <ul className="space-y-3 text-sm">
                    {plan.features.map((feat, fIdx) => (
                      <li key={fIdx} className="flex items-center gap-2.5">
                        <CheckCircle2 className="w-4 h-4 text-brand-400 flex-shrink-0" />
                        <span className={isDark ? 'text-slate-300' : 'text-slate-700'}>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <button
                  onClick={() => navigate('/signup')}
                  className={`mt-8 w-full py-3 rounded-xl font-semibold text-sm transition-all ${
                    plan.popular
                      ? 'bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/30'
                      : isDark
                      ? 'bg-slate-800 hover:bg-slate-700 text-white'
                      : 'bg-slate-100 hover:bg-slate-200 text-slate-900'
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. Testimonials & FAQ */}
      <section id="faq" className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Frequently Asked Questions</h2>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                className={`rounded-xl border overflow-hidden ${
                  isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
                }`}
              >
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full p-5 text-left font-semibold text-base flex justify-between items-center"
                >
                  <span>{faq.q}</span>
                  <ChevronDown className={`w-5 h-5 transition-transform ${openFaq === idx ? 'rotate-180' : ''}`} />
                </button>
                {openFaq === idx && (
                  <div className={`p-5 pt-0 text-sm leading-relaxed ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 7. Public Footer */}
      <footer className={`border-t py-12 ${isDark ? 'border-slate-900 bg-slate-950 text-slate-400' : 'border-slate-200 bg-slate-900 text-slate-400'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <span className="font-bold text-white tracking-tight">Evidence-Grounded AI Research Assistant</span>
          </div>
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} Evidence AI Inc. All rights reserved. Powered by RAGAS Framework & NVIDIA Llama 3.1.
          </p>
        </div>
      </footer>
    </div>
  );
}
