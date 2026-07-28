import React, { useState, useEffect } from 'react';
import {
  Loader2,
  Play,
  AlertCircle
} from 'lucide-react';
import api from '../services/api';
import CustomSelect from '../components/ui/CustomSelect';

export default function Evaluation() {
  const [question, setQuestion] = useState('');
  const [groundTruth, setGroundTruth] = useState('');
  const [expectedDoc, setExpectedDoc] = useState('');
  const [expectedPage, setExpectedPage] = useState('');
  const [topK, setTopK] = useState(5);

  const [loading, setLoading] = useState(false);
  const [currentEval, setCurrentEval] = useState(null);
  const [error, setError] = useState(null);

  const [history, setHistory] = useState([]);
  const [report, setReport] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [activeTab, setActiveTab] = useState('evaluator');

  useEffect(() => {
    fetchHistoryAndReport();
  }, []);

  const fetchHistoryAndReport = async () => {
    setLoadingHistory(true);
    try {
      const [histRes, repRes] = await Promise.all([
        api.get('/evaluation/history?limit=20'),
        api.get('/evaluation/report')
      ]);

      if (histRes.success) {
        setHistory(histRes.data || []);
      }
      if (repRes.success) {
        setReport(repRes.data || null);
      }
    } catch (err) {
      console.error('Error fetching evaluation history/report:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleRunEvaluation = async (e) => {
    e.preventDefault();
    if (!question.trim()) {
      setError('Please enter a query question to evaluate.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload = {
      question: question.trim(),
      ground_truth: groundTruth.trim() || undefined,
      expected_documents: expectedDoc.trim() ? [expectedDoc.trim()] : undefined,
      expected_pages: expectedPage.trim() ? [parseInt(expectedPage.trim(), 10)] : undefined,
      top_k: parseInt(topK, 10) || 5
    };

    try {
      const res = await api.post('/evaluation/run', payload);
      if (res.success) {
        setCurrentEval(res.data);
        fetchHistoryAndReport();
      } else {
        setError(res.error || 'Evaluation run failed.');
      }
    } catch (err) {
      console.error('Error running evaluation:', err);
      setError(err.message || 'Failed to execute evaluation query.');
    } finally {
      setLoading(false);
    }
  };

  const formatPercent = (val) => {
    if (val === undefined || val === null) return '0.0%';
    return (val * 100).toFixed(1) + '%';
  };

  const getMetricColor = (val) => {
    if (val >= 0.8) return 'text-emerald-500 border-emerald-500/20 bg-emerald-500/10';
    if (val >= 0.5) return 'text-amber-500 border-amber-500/20 bg-amber-500/10';
    return 'text-red-500 border-red-500/20 bg-red-500/10';
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-main">Evaluation</h1>
          <p className="text-xs text-sub mt-1">
            Automated RAGAS quality framework measuring Context Precision, Context Recall, Faithfulness, and Answer Relevancy.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1 bg-muted p-1 rounded-lg border border-theme self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('evaluator')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
              activeTab === 'evaluator' ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 font-semibold shadow-xs' : 'text-sub hover:text-main'
            }`}
          >
            Query Evaluator
          </button>
          <button
            onClick={() => setActiveTab('report')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
              activeTab === 'report' ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 font-semibold shadow-xs' : 'text-sub hover:text-main'
            }`}
          >
            Audit Report
          </button>
        </div>
      </div>

      {activeTab === 'evaluator' ? (
        <div className="space-y-6">
          {/* Query Form */}
          <div className="p-5 rounded-xl border border-theme bg-card">
            <form onSubmit={handleRunEvaluation} className="space-y-4">
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-muted-custom font-mono mb-1.5">
                  Evaluation Query Question
                </label>
                <input
                  type="text"
                  required
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="e.g. What is Retrieval Augmented Generation and how does it work?"
                  className="w-full px-3.5 py-2.5 rounded-lg border border-theme bg-input text-main placeholder-slate-400 text-xs sm:text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-muted-custom font-mono mb-1.5">
                  Ground Truth Reference (Optional)
                </label>
                <textarea
                  rows={2}
                  value={groundTruth}
                  onChange={(e) => setGroundTruth(e.target.value)}
                  placeholder="Expected ideal answer claim for context recall calculation..."
                  className="w-full p-3 rounded-lg border border-theme bg-input text-main placeholder-slate-400 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-sub mb-1">Expected Document Name:</label>
                  <input
                    type="text"
                    value={expectedDoc}
                    onChange={(e) => setExpectedDoc(e.target.value)}
                    placeholder="e.g. paper_blueprint.pdf"
                    className="w-full px-3 py-2 rounded-lg border border-theme bg-input text-main text-xs font-medium focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-sub mb-1">Expected Page Number:</label>
                  <input
                    type="number"
                    value={expectedPage}
                    onChange={(e) => setExpectedPage(e.target.value)}
                    placeholder="e.g. 1"
                    className="w-full px-3 py-2 rounded-lg border border-theme bg-input text-main text-xs font-medium focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-sub mb-1">Top-K Candidate Chunks:</label>
                  <CustomSelect
                    value={topK}
                    onChange={(e) => setTopK(e.target.value)}
                    options={[
                      { value: 3, label: '3 Chunks' },
                      { value: 5, label: '5 Chunks' },
                      { value: 10, label: '10 Chunks' },
                    ]}
                  />
                </div>
              </div>

              <div className="flex justify-end pt-1">
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-white dark:text-zinc-900 font-medium text-xs shadow-xs transition-all disabled:opacity-50 flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Evaluating Pipeline...
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5" />
                      Execute RAGAS Evaluation
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          {/* Current Evaluation Results */}
          {currentEval && (
            <div className="space-y-4">
              <div className="p-5 rounded-xl border border-theme bg-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-muted-custom font-mono">
                    Evaluation Results
                  </span>
                  <h3 className="text-base font-bold text-main mt-0.5">
                    Retrieved {currentEval.retrieved_chunks_count} Context Chunks
                  </h3>
                </div>

                <div className="text-right">
                  <div className="text-[10px] uppercase font-mono text-muted-custom">Overall RAGAS Score</div>
                  <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                    {(currentEval.overall_score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* RAGAS Metric Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {Object.entries(currentEval.metrics || {}).map(([key, val]) => (
                  <div key={key} className="p-3.5 rounded-xl border border-theme bg-card flex flex-col justify-between">
                    <span className="text-[11px] font-medium text-sub capitalize">
                      {key.replace('_', ' ')}
                    </span>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-lg font-bold font-mono text-main">{formatPercent(val)}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${getMetricColor(val)}`}>
                        {val >= 0.8 ? 'High' : val >= 0.5 ? 'Moderate' : 'Low'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-5 rounded-xl border border-theme bg-card space-y-2">
                <h3 className="text-[11px] font-bold uppercase tracking-wider text-muted-custom font-mono">Generated Answer</h3>
                <p className="text-xs text-sub leading-relaxed font-mono italic p-3.5 rounded-lg bg-muted/60 border border-theme">
                  "{currentEval.generated_answer}"
                </p>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Report View */
        <div className="space-y-4">
          {report ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-5 rounded-xl border border-theme bg-card">
                <span className="text-[11px] font-mono uppercase text-muted-custom">Total Evaluations</span>
                <div className="text-3xl font-bold text-main mt-1">{report.total_evaluations}</div>
              </div>

              <div className="p-5 rounded-xl border border-theme bg-card">
                <span className="text-[11px] font-mono uppercase text-muted-custom">Average Quality Score</span>
                <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400 font-mono mt-1">
                  {(report.overall_score_avg * 100).toFixed(1)}%
                </div>
              </div>

              <div className="p-5 rounded-xl border border-theme bg-card">
                <span className="text-[11px] font-mono uppercase text-muted-custom">Latest Run</span>
                <div className="text-xs font-semibold font-mono text-main mt-2">{report.latest_run_timestamp || 'N/A'}</div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-sub border border-dashed border-theme rounded-xl">Loading report metrics...</div>
          )}
        </div>
      )}
    </div>
  );
}
