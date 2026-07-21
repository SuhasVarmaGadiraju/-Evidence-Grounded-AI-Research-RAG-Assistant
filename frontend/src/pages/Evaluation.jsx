import React, { useState, useEffect } from 'react';
import {
  Award,
  BarChart3,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Play,
  History,
  FileText,
  HelpCircle,
  Sparkles,
  TrendingUp,
  Target,
  FileCheck,
  ShieldCheck,
  BookOpen,
  Layers,
  Plus
} from 'lucide-react';
import api from '../services/api';

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

  // Load History and Report on Mount
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
      setError('Please enter a evaluation question.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload = {
      question: question.trim(),
      ground_truth: groundTruth.trim() || undefined,
      expected_documents: expectedDoc.trim() ? [expectedDoc.trim()] : undefined,
      expected_pages: expectedPage ? [parseInt(expectedPage, 10)] : undefined,
      top_k: parseInt(topK, 10) || 5
    };

    try {
      const response = await api.post('/evaluation/run', payload);
      if (response.success) {
        setCurrentEval(response.data);
        fetchHistoryAndReport(); // Refresh history table & aggregate statistics
      } else {
        setError(response.error || 'Failed to execute evaluation.');
      }
    } catch (err) {
      console.error('Error running evaluation:', err);
      setError(err.message || 'An error occurred during evaluation.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveToDataset = async () => {
    if (!question.trim() || !groundTruth.trim()) {
      alert('Both Question and Ground Truth are required to create a dataset entry.');
      return;
    }

    try {
      const response = await api.post('/evaluation/dataset', {
        question: question.trim(),
        ground_truth: groundTruth.trim(),
        expected_documents: expectedDoc.trim() ? [expectedDoc.trim()] : [],
        expected_pages: expectedPage ? [parseInt(expectedPage, 10)] : []
      });

      if (response.success) {
        alert('Dataset entry created successfully!');
      } else {
        alert(response.error || 'Failed to add dataset entry.');
      }
    } catch (err) {
      alert(err.message || 'Error saving to dataset.');
    }
  };

  const getScoreBadgeClass = (score) => {
    if (score >= 0.8) return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700';
    if (score >= 0.6) return 'bg-sky-100 text-sky-800 dark:bg-sky-950/60 dark:text-sky-300 border-sky-300 dark:border-sky-700';
    if (score >= 0.4) return 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border-amber-300 dark:border-amber-700';
    return 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border-rose-300 dark:border-rose-700';
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400">
              <Award className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              RAG Quality Evaluation Dashboard
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            RAGAS-inspired quality assessment measuring Context Precision, Recall, Faithfulness, Relevancy, and Citations.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl shrink-0">
          <button
            onClick={() => setActiveTab('evaluator')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
              activeTab === 'evaluator'
                ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Play className="w-4 h-4" />
            Evaluator
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
              activeTab === 'history'
                ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <History className="w-4 h-4" />
            History ({history.length})
          </button>
        </div>
      </div>

      {/* Aggregate Report Summary Cards */}
      {report && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-semibold uppercase">
              <span>Overall Avg Score</span>
              <TrendingUp className="w-4 h-4 text-brand-500" />
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
              {(report.overall_score_avg * 100).toFixed(1)}%
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Across {report.total_evaluations} evaluations
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-semibold uppercase">
              <span>Context Precision</span>
              <Target className="w-4 h-4 text-sky-500" />
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
              {((report.metrics_averages?.context_precision || 0) * 100).toFixed(1)}%
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Retrieval signal-to-noise
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-semibold uppercase">
              <span>Faithfulness</span>
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
              {((report.metrics_averages?.faithfulness || 0) * 100).toFixed(1)}%
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Answer context grounding
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-semibold uppercase">
              <span>Citation Coverage</span>
              <FileCheck className="w-4 h-4 text-purple-500" />
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
              {((report.metrics_averages?.citation_coverage || 0) * 100).toFixed(1)}%
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Statements with sources
            </div>
          </div>
        </div>
      )}

      {/* Main Evaluator View */}
      {activeTab === 'evaluator' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left: Input Form */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
                <Sparkles className="w-5 h-5 text-brand-500" />
                Run RAG Evaluation
              </h2>

              <form onSubmit={handleRunEvaluation} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Question / Query *
                  </label>
                  <textarea
                    rows={3}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Enter the evaluation prompt or user question..."
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Ground Truth / Reference Answer (Optional)
                  </label>
                  <textarea
                    rows={3}
                    value={groundTruth}
                    onChange={(e) => setGroundTruth(e.target.value)}
                    placeholder="Expected factual answer for measuring Context Recall and Precision..."
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Expected Doc Name
                    </label>
                    <input
                      type="text"
                      value={expectedDoc}
                      onChange={(e) => setExpectedDoc(e.target.value)}
                      placeholder="e.g. paper.pdf"
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Expected Page
                    </label>
                    <input
                      type="number"
                      value={expectedPage}
                      onChange={(e) => setExpectedPage(e.target.value)}
                      placeholder="e.g. 1"
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div className="flex justify-between items-center pt-2">
                  <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                    <span>Top K Chunks:</span>
                    <input
                      type="number"
                      min={1}
                      max={20}
                      value={topK}
                      onChange={(e) => setTopK(e.target.value)}
                      className="w-16 px-2 py-1 border border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={handleSaveToDataset}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" /> Save to Dataset
                  </button>
                </div>

                {error && (
                  <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Evaluating Retrieval & Generation...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Run Evaluation
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Right: Results Display */}
          <div className="lg:col-span-7 space-y-6">
            {currentEval ? (
              <div className="space-y-6">
                {/* Overall Score Banner */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Overall RAGAS Score
                    </span>
                    <h3 className="text-3xl font-extrabold text-slate-900 dark:text-white mt-1">
                      {(currentEval.overall_score * 100).toFixed(1)}%
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Latency: {currentEval.latency_ms} ms | Retrieved {currentEval.retrieved_chunks_count} context chunks
                    </p>
                  </div>

                  <div className={`px-4 py-2 rounded-xl border text-sm font-bold ${getScoreBadgeClass(currentEval.overall_score)}`}>
                    {currentEval.overall_score >= 0.8 ? 'Excellent Quality' : currentEval.overall_score >= 0.6 ? 'Good Quality' : 'Needs Optimization'}
                  </div>
                </div>

                {/* Metrics Breakdown Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {Object.entries(currentEval.metrics).map(([key, val]) => (
                    <div key={key} className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                      <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 capitalize">
                        {key.replace(/_/g, ' ')}
                      </div>
                      <div className="mt-2 text-xl font-bold text-slate-900 dark:text-white">
                        {(val * 100).toFixed(1)}%
                      </div>
                      <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                        <div
                          className="bg-brand-500 h-full rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, val * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Generated Answer Box */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-brand-500" />
                    Generated Answer
                  </h4>
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 text-slate-800 dark:text-slate-200 text-sm leading-relaxed whitespace-pre-wrap border border-slate-200 dark:border-slate-700">
                    {currentEval.generated_answer}
                  </div>
                </div>

                {/* Retrieved Chunks Preview */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                    <Layers className="w-4 h-4 text-brand-500" />
                    Top Retrieved Chunks ({currentEval.retrieved_chunks.length})
                  </h4>
                  <div className="space-y-3">
                    {currentEval.retrieved_chunks.map((chunk, idx) => (
                      <div key={idx} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-xs">
                        <div className="flex justify-between items-center font-semibold text-slate-700 dark:text-slate-300 mb-1">
                          <span>{chunk.document_name || 'Document'} {chunk.page_number ? `(p. ${chunk.page_number})` : ''}</span>
                          <span className="text-brand-600 dark:text-brand-400 font-mono">Score: {chunk.score?.toFixed(4)}</span>
                        </div>
                        <p className="text-slate-600 dark:text-slate-400 line-clamp-2">{chunk.snippet}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-slate-900 p-12 rounded-2xl border border-slate-200 dark:border-slate-800 text-center text-slate-500 dark:text-slate-400 flex flex-col items-center justify-center min-h-[380px]">
                <BarChart3 className="w-12 h-12 text-slate-300 dark:text-slate-700 mb-3" />
                <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">No Active Evaluation</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm">
                  Enter a question and click "Run Evaluation" to calculate RAGAS precision, recall, and faithfulness scores.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <History className="w-5 h-5 text-brand-500" />
              Evaluation History Log
            </h3>
            <button
              onClick={fetchHistoryAndReport}
              className="text-xs text-brand-600 dark:text-brand-400 font-semibold hover:underline"
            >
              Refresh Log
            </button>
          </div>

          {loadingHistory ? (
            <div className="p-12 text-center text-slate-500 dark:text-slate-400 flex items-center justify-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-brand-500" /> Loading evaluation history...
            </div>
          ) : history.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300 uppercase font-semibold border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Question</th>
                    <th className="px-4 py-3 text-center">Overall</th>
                    <th className="px-4 py-3 text-center">Ctx Precision</th>
                    <th className="px-4 py-3 text-center">Ctx Recall</th>
                    <th className="px-4 py-3 text-center">Faithfulness</th>
                    <th className="px-4 py-3 text-center">Citations</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {history.map((run, idx) => (
                    <tr key={run.eval_id || idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="px-4 py-3 whitespace-nowrap font-mono text-slate-500">
                        {run.timestamp ? run.timestamp.replace('T', ' ').replace('Z', '') : 'N/A'}
                      </td>
                      <td className="px-4 py-3 max-w-xs truncate font-medium text-slate-900 dark:text-white">
                        {run.question}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-md font-bold text-xs ${getScoreBadgeClass(run.overall_score || 0)}`}>
                          {((run.overall_score || 0) * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center font-mono">
                        {((run.metrics?.context_precision || 0) * 100).toFixed(0)}%
                      </td>
                      <td className="px-4 py-3 text-center font-mono">
                        {((run.metrics?.context_recall || 0) * 100).toFixed(0)}%
                      </td>
                      <td className="px-4 py-3 text-center font-mono">
                        {((run.metrics?.faithfulness || 0) * 100).toFixed(0)}%
                      </td>
                      <td className="px-4 py-3 text-center font-mono">
                        {((run.metrics?.citation_coverage || 0) * 100).toFixed(0)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-12 text-center text-slate-500 dark:text-slate-400 text-xs">
              No evaluation history recorded yet.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
