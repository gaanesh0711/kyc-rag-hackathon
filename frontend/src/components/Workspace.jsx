import { useEffect, useRef, useState } from "react";
import {
  ArrowUpRight,
  Search,
  Copy,
  Check,
  AlertCircle,
  ArrowRight,
  FileText,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { askQuestion, checkHealth } from "../lib/api";
import ProcessingState from "./ProcessingState";
import EvidencePanel from "./EvidencePanel";

const suggestions = [
  ["Wealthtech", "What SEBI-related regulatory challenges does Zerodha face?"],
  ["Payments", "What compliance rules apply to PhonePe UPI and PPI wallets?"],
  ["Aggregators", "What escrow and due-diligence rules apply to Razorpay?"],
  [
    "Crypto & VDA",
    "What AML/CFT requirements apply to crypto exchanges like CoinDCX?",
  ],
];
const healthLabels = {
  checking: "Checking service",
  ready: "Service available",
  warming: "Service initializing",
  offline: "Service unavailable",
  unconfigured: "Backend not connected",
};

export default function Workspace() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [health, setHealth] = useState("checking");
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");
  const [cancelled, setCancelled] = useState(false);
  const controller = useRef(null);
  const copyTimer = useRef(null);
  const resultRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    const healthController = new AbortController();
    const timeout = setTimeout(() => healthController.abort(), 8000);
    checkHealth(healthController.signal)
      .then((value) => {
        if (mounted) setHealth(value);
      })
      .catch(() => {
        if (mounted) setHealth("offline");
      })
      .finally(() => clearTimeout(timeout));
    return () => {
      mounted = false;
      healthController.abort();
      controller.current?.abort();
      clearTimeout(copyTimer.current);
    };
  }, []);

  async function submit(value = question) {
    const text = value.trim();
    if (!text || controller.current) return;
    setQuestion(text);
    setError("");
    setCancelled(false);
    setCopied(false);
    setCopyError("");
    setLoading(true);
    setResult(null);
    const requestController = new AbortController();
    controller.current = requestController;
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      requestController.abort();
    }, 90000);
    try {
      const data = await askQuestion(text, requestController.signal);
      if (requestController.signal.aborted) return;
      setResult(data);
      setHealth("ready");
    } catch (err) {
      if (requestController.signal.aborted && !timedOut) setCancelled(true);
      else
        setError(
          timedOut
            ? "The service took too long to respond. Try a narrower question or retry in a moment."
            : err.message || "Something went wrong. Please try again.",
        );
    } finally {
      clearTimeout(timeout);
      controller.current = null;
      setLoading(false);
    }
  }

  useEffect(() => {
    if (loading || result || error)
      resultRef.current?.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
        block: "start",
      });
  }, [loading, result, error]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(result.answer);
      setCopied(true);
      setCopyError("");
      clearTimeout(copyTimer.current);
      copyTimer.current = setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopyError(
        "Copy is unavailable. You can select and copy the answer manually.",
      );
    }
  }

  return (
    <div className="workspace content-width">
      <div className="workspace-heading">
        <div>
          <div className="eyebrow">FINVISORS / RESEARCH WORKSPACE</div>
          <h1>Start with a question.</h1>
          <p>Explore the dataset. Read the answer. Inspect the evidence.</p>
        </div>
        <div className="service-status" data-state={health}>
          <span aria-hidden="true" />
          {healthLabels[health]}
        </div>
      </div>
      <div className="demo-note">
        <FileText size={17} />
        <p>
          Public demo using the bundled FinVisory dataset. Please keep questions
          free of personal or confidential information.
        </p>
      </div>
      <form
        className="research-form"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <label htmlFor="question">What would you like to understand?</label>
        <div className="question-field">
          <Search size={20} aria-hidden="true" />
          <textarea
            id="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            maxLength={2000}
            rows={2}
            disabled={loading}
            placeholder="Ask about a company, regulator, or compliance consideration…"
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing
              ) {
                event.preventDefault();
                submit();
              }
            }}
          />
          <button
            className="button"
            disabled={loading || !question.trim()}
            type="submit"
          >
            {loading ? "Researching" : "Ask FinVisors"}
            <ArrowUpRight size={18} />
          </button>
        </div>
        <div className="field-caption">
          <span>Enter to ask · Shift + Enter for a new line</span>
          <span>{question.length}/2,000</span>
        </div>
      </form>
      {!result && !loading && (
        <div className="suggestions">
          <div className="eyebrow">A FEW PLACES TO START</div>
          <div className="suggestion-grid">
            {suggestions.map(([label, text]) => (
              <button
                className="suggestion"
                key={label}
                onClick={() => submit(text)}
              >
                <span>{label}</span>
                <p>{text}</p>
                <ArrowRight size={17} aria-hidden="true" />
              </button>
            ))}
          </div>
        </div>
      )}
      <p className="sr-only" role="status">
        {result
          ? `Research response ready with ${result.sources.length} retrieved source records.`
          : ""}
      </p>
      <div ref={resultRef} className="result-anchor" aria-busy={loading}>
        {loading && (
          <ProcessingState onCancel={() => controller.current?.abort()} />
        )}
        {error && (
          <div className="request-error" role="alert">
            <AlertCircle size={22} />
            <div>
              <h3>We couldn’t complete that research.</h3>
              <p>{error}</p>
              <button className="text-button" onClick={() => submit()}>
                Try again <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}
        {cancelled && (
          <p className="cancel-note" role="status">
            Request cancelled. You can refine your question and try again.
          </p>
        )}
        {result && (
          <div className="results-grid">
            <article className="answer-panel">
              <div className="panel-heading">
                <span className="eyebrow">RESEARCH RESPONSE</span>
                <button onClick={copy} className="copy-button">
                  {copied ? <Check size={16} /> : <Copy size={16} />}
                  {copied ? "Copied" : "Copy answer"}
                </button>
              </div>
              <h2>{result.question}</h2>
              <div className="markdown-answer">
                <ReactMarkdown>
                  {result.answer ||
                    "The service returned no answer. Try a more focused question."}
                </ReactMarkdown>
              </div>
              {copyError && (
                <p className="copy-error" role="status">
                  {copyError}
                </p>
              )}
              <div className="answer-boundary">
                Based on the supplied dataset. This is research context, not a
                compliance determination or an allegation of wrongdoing.
              </div>
            </article>
            <EvidencePanel sources={result.sources} />
          </div>
        )}
        {!result && !loading && !error && !cancelled && (
          <div className="workspace-empty">
            <div className="empty-mark">
              <FileText size={27} strokeWidth={1.5} />
            </div>
            <h2>The evidence starts here.</h2>
            <p>
              Ask a focused question to bring the relevant company records into
              view.
            </p>
          </div>
        )}
      </div>
      <div className="workspace-boundary">
        <span className="eyebrow">A NOTE ON THE DEMO</span>
        <p>
          This tool does not verify identities, perform sanctions screening, or
          calculate risk scores. Review generated answers and check current
          requirements against authoritative sources.
        </p>
      </div>
    </div>
  );
}
