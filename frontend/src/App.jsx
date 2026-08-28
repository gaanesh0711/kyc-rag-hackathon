import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Search, 
  Send, 
  BookOpen, 
  Building2, 
  Scale, 
  FileText, 
  Loader2, 
  AlertCircle, 
  Copy, 
  Check, 
  ChevronDown, 
  ChevronUp,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const SUGGESTIONS = [
  "What SEBI-related regulatory challenges does Zerodha face?",
  "What compliance rules apply to PhonePe UPI and PPI wallets?",
  "What escrow and due-diligence rules apply to Razorpay?",
  "What AML/CFT requirements apply to crypto exchanges like CoinDCX?",
  "What credit bureau reporting guidelines apply to CIBIL & Experian?"
];

const REGULATOR_COLORS = {
  "SEBI": "bg-blue-900/40 text-blue-300 border-blue-700/50",
  "RBI": "bg-emerald-900/40 text-emerald-300 border-emerald-700/50",
  "IRDAI": "bg-amber-900/40 text-amber-300 border-amber-700/50",
  "FIU-IND / Income Tax Department / Government of India": "bg-purple-900/40 text-purple-300 border-purple-700/50",
  "RBI / regulated financial-institution customers": "bg-teal-900/40 text-teal-300 border-teal-700/50",
  "default": "bg-slate-800 text-slate-300 border-slate-700"
};

export default function App() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [expandedExcerpts, setExpandedExcerpts] = useState({});

  const handleSearch = async (queryToRun) => {
    const q = queryToRun || question;
    if (!q.trim() || loading) return;

    setLoading(true);
    setError(null);
    setCopied(false);

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q.trim() }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server responded with status ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      if (queryToRun) setQuestion(queryToRun);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to reach the API server at http://127.0.0.1:8000");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleCopy = () => {
    if (!result?.answer) return;
    navigator.clipboard.writeText(result.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleExcerpt = (idx) => {
    setExpandedExcerpts(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-slate-700 selection:text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-10 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-slate-800 rounded-lg border border-slate-700 text-slate-200">
              <ShieldCheck className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-base font-semibold tracking-tight text-white flex items-center gap-2">
                FinVisory KYC & Regulatory RAG
                <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800/60">
                  v1.0
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Grounded Compliance Intelligence across 80 Indian Fintech Entities (SEBI • RBI • IRDAI • FIU-IND)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-mono">API: 127.0.0.1:8000</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8 flex flex-col gap-6">
        
        {/* Search Input Box */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl">
          <div className="relative flex items-center">
            <Search className="w-5 h-5 text-slate-400 absolute left-3.5 pointer-events-none" />
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a compliance or regulatory question (e.g. 'What SEBI challenges does Zerodha face?')..."
              className="w-full pl-11 pr-28 py-3 bg-slate-950 border border-slate-700/80 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
              disabled={loading}
            />
            <button
              onClick={() => handleSearch()}
              disabled={loading || !question.trim()}
              className="absolute right-2 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600 text-white rounded-md text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Query</span>
                </>
              )}
            </button>
          </div>

          {/* Quick Suggestions */}
          <div className="mt-3 flex items-center gap-2 flex-wrap">
            <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-indigo-400" /> Suggestions:
            </span>
            {SUGGESTIONS.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleSearch(s)}
                className="text-xs bg-slate-800/80 hover:bg-slate-750 hover:border-slate-600 text-slate-300 px-2.5 py-1 rounded-md border border-slate-700/60 transition cursor-pointer text-left"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-950/40 border border-red-800/60 rounded-xl p-4 flex items-start gap-3 text-red-200 text-sm">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-300">Request Error</p>
              <p className="text-xs text-red-400/90 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Loading Skeleton */}
        {loading && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 animate-pulse flex flex-col gap-4">
            <div className="h-4 bg-slate-800 rounded w-1/4"></div>
            <div className="space-y-2">
              <div className="h-3 bg-slate-800 rounded w-full"></div>
              <div className="h-3 bg-slate-800 rounded w-5/6"></div>
              <div className="h-3 bg-slate-800 rounded w-4/6"></div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="h-20 bg-slate-800/60 rounded"></div>
              <div className="h-20 bg-slate-800/60 rounded"></div>
              <div className="h-20 bg-slate-800/60 rounded"></div>
            </div>
          </div>
        )}

        {/* Results View */}
        {result && !loading && (
          <div className="flex flex-col gap-6">
            
            {/* Answer Section */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  <Scale className="w-4 h-4 text-indigo-400" />
                  Regulatory Assessment & Findings
                </div>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-800 px-2.5 py-1 rounded border border-slate-700 transition"
                  title="Copy answer"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>

              {/* Answer Markdown Body */}
              <div className="prose prose-invert prose-sm max-w-none text-slate-200 space-y-3 leading-relaxed">
                <ReactMarkdown
                  components={{
                    ul: ({node, ...props}) => <ul className="list-disc pl-5 space-y-1.5 my-2" {...props} />,
                    li: ({node, ...props}) => <li className="text-slate-300" {...props} />,
                    strong: ({node, ...props}) => <strong className="font-semibold text-slate-100" {...props} />,
                    h3: ({node, ...props}) => <h3 className="text-sm font-semibold text-indigo-300 mt-4 mb-2" {...props} />
                  }}
                >
                  {result.answer}
                </ReactMarkdown>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between">
                <span>Compliance Note: Reflects activity-dependent regulatory/operational impacts, not claims of violations.</span>
                <span>Question: &ldquo;{result.question}&rdquo;</span>
              </div>
            </div>

            {/* Citations Panel */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  <BookOpen className="w-4 h-4 text-emerald-400" />
                  Verified Citations & Source Entities ({result.sources?.length || 0})
                </div>
                <span className="text-xs text-slate-500">Vector Similarity Retrieved</span>
              </div>

              {/* Source Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {result.sources?.map((src, idx) => {
                  const regColor = REGULATOR_COLORS[src.regulator] || REGULATOR_COLORS["default"];
                  const isExpanded = !!expandedExcerpts[idx];

                  return (
                    <div 
                      key={idx}
                      className="bg-slate-950 border border-slate-800 rounded-lg p-4 flex flex-col justify-between hover:border-slate-700 transition"
                    >
                      <div>
                        {/* Company & Regulator Badge */}
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex items-center gap-1.5 font-medium text-sm text-white">
                            <Building2 className="w-4 h-4 text-indigo-400 shrink-0" />
                            <span className="truncate">{src.company || "Unknown"}</span>
                          </div>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border uppercase tracking-wider shrink-0 ${regColor}`}>
                            {src.regulator || "N/A"}
                          </span>
                        </div>

                        {/* Sector / Vertical */}
                        <p className="text-xs text-slate-400 mb-2 font-mono">
                          {src.vertical || "Fintech"}
                        </p>

                        {/* Document File Tag */}
                        <div className="flex items-center gap-1 text-[11px] text-slate-400 bg-slate-900 px-2 py-1 rounded border border-slate-800 mb-3 truncate">
                          <FileText className="w-3 h-3 text-slate-400 shrink-0" />
                          <span className="truncate" title={src.document}>{src.document || "FinVisory Merged Dataset"}</span>
                        </div>
                      </div>

                      {/* Excerpt Toggle */}
                      <div className="border-t border-slate-800/80 pt-2 mt-2">
                        <button
                          onClick={() => toggleExcerpt(idx)}
                          className="w-full flex items-center justify-between text-[11px] text-indigo-400 hover:text-indigo-300 font-medium cursor-pointer"
                        >
                          <span>{isExpanded ? "Hide Excerpt" : "View Source Excerpt"}</span>
                          {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        </button>
                        
                        {isExpanded && (
                          <div className="mt-2 text-[11px] text-slate-300 bg-slate-900 p-2.5 rounded border border-slate-800 font-mono whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                            {src.excerpt}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        )}

        {/* Empty State / Welcome Guide */}
        {!result && !loading && !error && (
          <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-8 text-center flex flex-col items-center justify-center gap-3">
            <div className="p-3 bg-slate-800 rounded-full text-indigo-400 border border-slate-700">
              <BookOpen className="w-6 h-6" />
            </div>
            <h2 className="text-base font-semibold text-slate-200">
              Ready for Regulatory & KYC Queries
            </h2>
            <p className="text-xs text-slate-400 max-w-lg leading-relaxed">
              This system indexes 80 company-level compliance entries across Wealthtech, Insurtech, Payment Aggregators, PPIs, Lending, SaaS, and Crypto. Select a suggested query above or type your question.
            </p>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/40 px-6 py-3 text-center text-xs text-slate-500">
        FinVisory Regulatory Intelligence • RAG Hackathon Edition • Strictly Compliant Citations
      </footer>
    </div>
  );
}
