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

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

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
    <div className={`min-h-screen ${isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-faf9f6 text-zinc-900'}`}>
      {/* 1. Public Top Navigation */}
      <header className={`sticky top-0 z-50 backdrop-blur-md border-b ${isDark ? 'bg-zinc-950/90 border-zinc-800' : 'bg-white/90 border-zinc-200'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to={isAuthenticated ? "/dashboard" : "/"} className="flex items-center gap-3 group cursor-pointer" title="Go to Dashboard">
            <div className="w-8 h-8 rounded-lg bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center text-white dark:text-zinc-900 font-bold shadow-xs">
              <BrainCircuit className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-sm tracking-tight text-main">Evidence AI</span>
              <span className="ml-2 text-[10px] font-mono px-2 py-0.5 rounded font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                SaaS v1.0
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 text-xs font-medium">
            <a href="#features" className="text-sub hover:text-main transition-colors">Features</a>
            <a href="#workflow" className="text-sub hover:text-main transition-colors">How it Works</a>
            <a href="#pricing" className="text-sub hover:text-main transition-colors">Pricing</a>
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
                  to="/signup"
                  className="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 text-xs font-semibold shadow-xs transition-all"
                >
                  Get Started
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
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            Next-Generation Evidence-Grounded AI Research Assistant
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight max-w-4xl mx-auto leading-tight">
            Research with Zero Hallucinations and 100% Citations
          </h1>

          <p className={`mt-4 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
            Accelerate literature reviews, paper analysis, and academic writing using Hybrid Vector-Lexical Search, Cross-Encoder Reranking, and automated RAGAS quality auditing.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center items-center">
            <button
              onClick={() => navigate(isAuthenticated ? '/dashboard' : '/signup')}
              className="w-full sm:w-auto px-6 py-3 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-semibold text-xs shadow-xs transition-all flex items-center justify-center gap-2"
            >
              Start Free Research Workspace
              <ArrowRight className="w-4 h-4" />
            </button>
            <a
              href="#workflow"
              className={`w-full sm:w-auto px-6 py-3 rounded-lg font-semibold text-xs border transition-all flex items-center justify-center gap-2 ${
                isDark ? 'border-zinc-800 hover:bg-zinc-900 text-zinc-300' : 'border-zinc-300 hover:bg-zinc-100 text-zinc-700'
              }`}
            >
              Explore Architecture
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
                  <span className="ml-2 text-xs font-mono text-muted-custom">evidence-ai // RAG Studio Console</span>
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

      {/* 3. Features Section */}
      <section id="features" className={`py-16 border-t ${isDark ? 'border-zinc-900 bg-zinc-950' : 'border-zinc-200 bg-zinc-100/50'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Engineered for Rigorous Academic & Clinical Research
            </h2>
            <p className={`mt-2 text-xs sm:text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Built on production-grade RAG principles so you can query complex technical literature with verifiable accuracy.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <div
                key={i}
                className={`p-5 rounded-xl border transition-all ${
                  isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
                }`}
              >
                <div className="w-10 h-10 rounded-lg bg-muted text-main border border-theme flex items-center justify-center mb-4">
                  <f.icon className="w-5 h-5 text-muted-custom" />
                </div>
                <h3 className="text-sm font-bold mb-1.5">{f.title}</h3>
                <p className={`text-xs leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. Workflow Steps */}
      <section id="workflow" className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <span className="text-xs font-semibold text-muted-custom font-mono uppercase tracking-widest">End-to-End Pipeline</span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mt-1">
              How Evidence AI Works
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {workflowSteps.map((ws, idx) => (
              <div
                key={idx}
                className={`p-5 rounded-xl border relative ${
                  isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
                }`}
              >
                <span className="text-3xl font-bold text-muted-custom font-mono mb-3 block">{ws.step}</span>
                <h3 className="text-sm font-bold mb-1.5">{ws.title}</h3>
                <p className={`text-xs leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{ws.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 5. Pricing Table */}
      <section id="pricing" className={`py-16 border-t ${isDark ? 'border-zinc-900 bg-zinc-950' : 'border-zinc-200 bg-zinc-100/50'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Flexible Plans for Every Researcher</h2>
            <p className={`mt-2 text-xs sm:text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Transparent pricing with no hidden tokens or surprise fees.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {pricingPlans.map((plan, i) => (
              <div
                key={i}
                className={`p-6 rounded-xl border flex flex-col justify-between relative ${
                  plan.popular
                    ? 'bg-zinc-900 dark:bg-zinc-900 border-zinc-700 text-white shadow-xl'
                    : isDark
                    ? 'bg-zinc-900 border-zinc-800'
                    : 'bg-white border-zinc-200'
                }`}
              >
                {plan.popular && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-2.5 py-0.5 rounded font-mono text-[10px] font-semibold bg-emerald-500 text-zinc-950 uppercase tracking-wider">
                    Most Popular
                  </span>
                )}
                <div>
                  <h3 className="text-base font-bold">{plan.name}</h3>
                  <p className="text-xs mt-1 text-muted-custom">{plan.desc}</p>
                  <div className="mt-4 mb-4">
                    <span className="text-3xl font-bold font-mono">{plan.price}</span>
                    <span className="text-xs ml-1.5 text-muted-custom font-mono">{plan.period}</span>
                  </div>
                  <ul className="space-y-2.5 text-xs">
                    {plan.features.map((feat, fIdx) => (
                      <li key={fIdx} className="flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <button
                  onClick={() => navigate('/signup')}
                  className={`mt-6 w-full py-2.5 rounded-lg font-medium text-xs transition-all ${
                    plan.popular
                      ? 'bg-zinc-100 text-zinc-900 hover:bg-white shadow-xs font-semibold'
                      : isDark
                      ? 'bg-zinc-800 hover:bg-zinc-700 text-white'
                      : 'bg-zinc-100 hover:bg-zinc-200 text-zinc-900'
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
            <span className="font-bold text-xs text-white tracking-tight">Evidence-Grounded AI Research Assistant</span>
          </div>
          <p className="text-[11px] text-zinc-500 font-mono">
            © {new Date().getFullYear()} Evidence AI Inc. All rights reserved. Powered by RAGAS Framework & NVIDIA Llama 3.1.
          </p>
        </div>
      </footer>
    </div>
  );
}
