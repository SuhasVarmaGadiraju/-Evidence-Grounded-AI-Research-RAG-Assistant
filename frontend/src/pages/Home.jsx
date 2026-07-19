import React from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, MessageSquare, Quote, BarChart3, ArrowRight } from 'lucide-react';

export default function Home() {
  const navigate = useNavigate();

  const features = [
    {
      title: 'Upload Documents',
      description: 'Ingest PDFs and text files. The system handles chunking and extraction automatically.',
      icon: UploadCloud,
      path: '/upload',
      color: 'text-blue-500 bg-blue-50 dark:bg-blue-950/30 dark:text-blue-400',
    },
    {
      title: 'AI Chat',
      description: 'Interact with your documents using custom LLMs and advanced retrieval techniques.',
      icon: MessageSquare,
      path: '/chat',
      color: 'text-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 dark:text-indigo-400',
    },
    {
      title: 'Source-Cited Answers',
      description: 'Get transparent answers grounded in evidence with specific page and block references.',
      icon: Quote,
      path: '/documents',
      color: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-950/30 dark:text-emerald-400',
    },
    {
      title: 'Evaluation Dashboard',
      description: 'Monitor RAG system performance, retrieval relevance, and answer correctness using RAGAS.',
      icon: BarChart3,
      path: '/settings',
      color: 'text-amber-500 bg-amber-50 dark:bg-amber-950/30 dark:text-amber-400',
    },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-12 py-4">
      {/* Hero Section */}
      <div className="text-center space-y-6 max-w-3xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-slate-900 via-brand-600 to-indigo-600 dark:from-slate-100 dark:via-brand-400 dark:to-indigo-400 bg-clip-text text-transparent">
          Evidence-Grounded AI Research Assistant
        </h1>
        <p className="text-lg text-slate-600 dark:text-slate-400 leading-relaxed">
          A production-grade Retrieval-Augmented Generation (RAG) platform. Research academic papers, legal texts, and technical manuals with complete trust, transparency, and reference-backed evidence.
        </p>
        <div className="flex justify-center pt-4">
          <button
            onClick={() => navigate('/chat')}
            className="group flex items-center gap-2 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-700 hover:to-indigo-700 text-white font-semibold px-6 py-3 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 cursor-pointer"
          >
            Get Started
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </div>

      <hr className="border-slate-200 dark:border-slate-800" />

      {/* Features Grid */}
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
            Platform Capabilities
          </h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Explore components built to achieve fully verifiable AI responses.
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 gap-6">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <div
                key={idx}
                onClick={() => navigate(feature.path)}
                className="group p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700 transition-all duration-200 cursor-pointer"
              >
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-lg ${feature.color} shrink-0`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-bold text-lg text-slate-800 dark:text-slate-100 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors">
                      {feature.title}
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
