import { useEffect, useRef, useState } from "react";
import { ArrowUpRight, FlaskConical, FileText } from "lucide-react";
import { simulationOptions, runSimulation } from "../lib/api";
import "../styles/simulator.css";

const examples = [
  { title: "Tighter wallet limits", regulator: "RBI", vertical: "PPI & Wallets", rule: "Hypothetical: RBI lowers permitted PPI wallet balances and requires additional verification before raising wallet limits. Which documented company activities could be affected and what should teams review?" },
  { title: "Aggregator due diligence", regulator: "RBI", vertical: "Payment Aggregators", rule: "Hypothetical: RBI requires payment aggregators to reverify merchant onboarding documents every year. Assess potential operational impacts using the dataset." },
  { title: "Investment disclosures", regulator: "SEBI", vertical: "Wealthtech & Investment Platforms", rule: "Hypothetical: SEBI requires investment platforms to show clearer product risk and fee disclosures before each transaction. Assess potential impacts on documented activities." },
];
const labels = { potential_impact: "Potential impact", no_clear_link: "No clear link", insufficient_evidence: "Insufficient evidence" };

export default function Simulator() {
  const [scope, setScope] = useState(null);
  const [scopeError, setScopeError] = useState("");
  const [retry, setRetry] = useState(0);
  const [rule, setRule] = useState("");
  const [regulator, setRegulator] = useState("");
  const [vertical, setVertical] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [cancelled, setCancelled] = useState(false);
  const [view, setView] = useState("potential_impact");
  const controller = useRef(null);

  useEffect(() => {
    const request = new AbortController();
    const timeout = setTimeout(() => request.abort(), 15000);
    simulationOptions(request.signal).then(setScope).catch(() => {
      setScopeError("The dataset could not be loaded. Check the backend and retry.");
    }).finally(() => clearTimeout(timeout));
    return () => { request.abort(); clearTimeout(timeout); controller.current?.abort(); };
  }, [retry]);

  async function submit(event) {
    event.preventDefault();
    if (!rule.trim() || !scope || controller.current) return;
    const request = new AbortController();
    controller.current = request;
    let timedOut = false;
    const timeout = setTimeout(() => { timedOut = true; request.abort(); }, 180000);
    setLoading(true); setError(""); setResult(null); setCancelled(false);
    try {
      const data = await runSimulation({ rule: rule.trim(), regulator: regulator || null, vertical: vertical || null }, request.signal);
      if (!request.signal.aborted) { setResult(data); setView("potential_impact"); }
    } catch (err) {
      if (request.signal.aborted && !timedOut) setCancelled(true);
      else setError(timedOut ? "The review took too long. Choose a narrower scope and retry." : err.message);
    } finally { clearTimeout(timeout); controller.current = null; setLoading(false); }
  }

  return <div className="workspace content-width simulator">
    <div className="workspace-heading">
      <div><div className="eyebrow">FINVISORS / SCENARIO LAB</div><h1>When the rules change.</h1><p>Explore potential impacts across the companies in your selected scope.</p></div>
      <span className="simulation-tag"><FlaskConical size={16} /> Hypothetical analysis</span>
    </div>
    <div className="demo-note"><FileText size={20} /><p>These scenarios are invented for exploration. Results are AI-generated inferences from the bundled dataset, not current rules or verified legal applicability. Keep inputs free of personal or confidential information.</p></div>
    <div className="scenario-examples"><span className="eyebrow">TRY A SCENARIO</span><div>
      {examples.map(example => <button className="scenario-example" key={example.title} disabled={loading || !scope} onClick={() => {
        setRule(example.rule); setRegulator(scope.regulators.includes(example.regulator) ? example.regulator : "");
        setVertical(scope.verticals.includes(example.vertical) ? example.vertical : "");
      }}>{example.title}<ArrowUpRight size={16} /></button>)}
    </div></div>
    {scopeError && <div role="alert" className="simulation-error"><p>{scopeError}</p><button className="text-button" onClick={() => { setScopeError(""); setRetry(value => value + 1); }}>Retry dataset connection</button></div>}
    <form className="research-form" onSubmit={submit}>
      <label htmlFor="rule">Describe a hypothetical rule change</label>
      <div className="question-field"><textarea id="rule" rows={4} maxLength={2000} value={rule} disabled={loading} onChange={event => setRule(event.target.value)} placeholder="What if RBI tightened PPI wallet limits? Describe the change you want to explore…" /></div>
      <div className="field-caption"><span>Every record in the selected scope is reviewed.</span><span>{rule.length} / 2,000</span></div>
      <div className="simulation-controls">
        <div><label htmlFor="simulation-regulator">Regulator</label><select id="simulation-regulator" value={regulator} disabled={loading || !scope} onChange={event => setRegulator(event.target.value)}><option value="">All regulators</option>{scope?.regulators.map(value => <option key={value}>{value}</option>)}</select></div>
        <div><label htmlFor="simulation-sector">Sector</label><select id="simulation-sector" value={vertical} disabled={loading || !scope} onChange={event => setVertical(event.target.value)}><option value="">All sectors</option>{scope?.verticals.map(value => <option key={value}>{value}</option>)}</select></div>
        <button className="button" disabled={loading || !scope || !rule.trim()} type="submit">Run impact review <ArrowUpRight size={17} /></button>
      </div>
      <p className="scope-caption">{scope ? `${scope.total_companies} companies · ${scope.total_records} source records in the dataset. Filters narrow the review; matching records are not automatically affected.` : "Loading dataset scope…"}</p>
    </form>
    {loading && <div className="simulation-progress" role="status"><FlaskConical size={24} /><h2>Tracing the potential impact.</h2><p>Reviewing the selected company records against your hypothetical rule. A whole-dataset review may take a few minutes.</p><button className="text-button" onClick={() => controller.current?.abort()}>Cancel review</button><p className="scope-caption">Cancellation stops waiting; provider processing may continue.</p></div>}
    {cancelled && <p role="status">Review cancelled. You can change the scope and try again.</p>}
    {error && <div className="simulation-error" role="alert"><h2>We couldn’t complete the review.</h2><p>{error}</p><p>Adjust the scope if needed, then select Run impact review to retry.</p></div>}
    {result && <section className="simulation-results" aria-label="Hypothetical impact results" aria-live="polite">
      <div className="eyebrow">HYPOTHETICAL / IMPACT REVIEW</div><h2>Potential effects, with evidence.</h2>
      <p className="scenario-result-rule">{result.rule}</p>
      <p className="scope-caption">Reviewed {result.reviewed_records} of {result.total_records} records ({result.reviewed_companies} companies). Regulator: {result.regulator || "All"}. Sector: {result.vertical || "All"}.</p>
      <div className="impact-filters" aria-label="Filter impact results">
        {[...Object.entries(labels), ["all", "All reviewed"]].map(([value, label]) => <button key={value} aria-pressed={view === value} onClick={() => setView(value)}>{label}<span>{value === "all" ? result.companies.length : result.companies.filter(item => item.status === value).length}</span></button>)}
      </div>
      <div className="impact-grid">{result.companies.filter(item => view === "all" || item.status === view).map(item => <article className="impact-card" key={item.record_id}>
        <div className="impact-card-heading"><h3>{item.company}</h3><span className={`impact-status ${item.status}`}>{labels[item.status]}</span></div>
        <p className="source-sector">{item.regulator} · {item.vertical}</p>
        <h4>Why it may matter</h4><p>{item.reasoning}</p><h4>Suggested review</h4><p>{item.review_action}</p>
        <details><summary>Inspect supporting record</summary><p className="source-document">{item.document}</p><p className="source-excerpt">{item.excerpt || "No excerpt available."}</p></details>
      </article>)}</div>
      {!result.companies.some(item => view === "all" || item.status === view) && <p className="simulation-empty">No records in this category. Inspect the other categories to see all reviewed records.</p>}
      <p className="scope-caption">“No clear link” does not establish exemption. Potential impacts need human review; the dataset may omit relevant activities or requirements.</p>
    </section>}
  </div>;
}
