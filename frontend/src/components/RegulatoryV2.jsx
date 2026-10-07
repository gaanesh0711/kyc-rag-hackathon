import { useEffect, useState } from "react";
import { apiBase } from "../lib/api";
import "../styles/regulatory-v2.css";

const tabs = [["regulations", "Regulations"], ["changes", "What changed"], ["ask", "Ask a regulation"], ["compare", "Compare"], ["scenario", "Simulate"], ["sources", "Sources & review"]];
const entityTypes = [["ppi_issuer", "PPI issuer"], ["payment_aggregator", "Payment aggregator"], ["stock_broker", "Stock broker"]];
const labels = { matches_conditions: "Matches conditions", does_not_match: "Does not match", unknown: "Unknown — review needed", not_active: "Not active on this date" };
const presets = [
  ["Wallet limits", "ppi_issuer", "Hypothetical: PPI issuers must apply lower wallet balance limits and enhanced verification before limit increases."],
  ["Merchant review", "payment_aggregator", "Hypothetical: payment aggregators must reverify merchant onboarding information annually."],
  ["Investor disclosure", "stock_broker", "Hypothetical: stock brokers must display additional risk and fee disclosures before each transaction."],
];

async function request(path, body, signal) {
  if (!apiBase) throw new Error("Configure the V2 backend URL to connect this workspace.");
  const response = await fetch(`${apiBase}/v2${path}`, { signal, ...(body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {}) });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : `Request failed (${response.status}). Check your input or retry.`);
  return data;
}

function OfficialLink({ version }) {
  return <a className="text-link" href={version.url} target="_blank" rel="noreferrer">Open official source ↗</a>;
}

function Outcome({ item }) {
  return <div className={`v2-outcome outcome-${item.outcome}`}><strong>{labels[item.outcome]}</strong><ul>{item.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul>
    {item.missing_information.length > 0 && <p>Needed: {item.missing_information.join("; ")}</p>}</div>;
}

export default function RegulatoryV2({ section = "regulations" }) {
  const [data, setData] = useState(null);
  const [reload, setReload] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState(null);
  const [impact, setImpact] = useState(null);
  const [result, setResult] = useState(null);
  const [question, setQuestion] = useState("");
  const [effectiveOnly, setEffectiveOnly] = useState(true);
  const [asOf, setAsOf] = useState("");
  const [regulator, setRegulator] = useState("");
  const [rule, setRule] = useState(presets[0][2]);
  const [target, setTarget] = useState(presets[0][1]);
  const [activity, setActivity] = useState("");
  const [left, setLeft] = useState("");
  const [right, setRight] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    Promise.all(["/status", "/regulations", "/changes", "/entities", "/obligations"].map(path => request(path, null, controller.signal)))
      .then(([status, regulations, changes, entities, obligations]) => {
        setData({ status, regulations, changes, entities, obligations });
      }).catch(err => { if (!controller.signal.aborted) setError(err.message); else setError("Loading timed out. Check the V2 backend and retry."); })
      .finally(() => { clearTimeout(timeout); setLoading(false); });
    return () => { controller.abort(); clearTimeout(timeout); };
  }, [reload]);

  async function run(path, body, setter = setResult) {
    setBusy(true); setError("");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 90000);
    try { setter(await request(path, body, controller.signal)); }
    catch (err) { setError(err.name === "AbortError" ? "The request timed out. Please retry." : err.message); }
    finally { clearTimeout(timeout); setBusy(false); }
  }

  async function downloadAudit() {
    try {
      const audit = await request(`/audit/${result.audit_id}`);
      const url = URL.createObjectURL(new Blob([JSON.stringify(audit, null, 2)], { type: "application/json" }));
      const link = document.createElement("a"); link.href = url; link.download = `finvisors-audit-${result.audit_id}.json`; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) { setError(err.message); }
  }

  const auditButton = result?.audit_id && <button className="text-button" onClick={downloadAudit}>Download this review’s audit record</button>;
  return <div className="workspace content-width regulatory-v2">
    <div className="eyebrow">FINVISORS / KYC RAG V2</div><h1>From rule changes to reasons.</h1>
    <p className="v2-intro">Official evidence, preserved versions, and explicit conditions. Every unknown stays visible.</p>
    <nav className="v2-tabs" aria-label="Regulatory tools">{tabs.map(([key, label]) => <a key={key} href={`#v2/${key}`} aria-current={section === key ? "page" : undefined}>{label}</a>)}</nav>
    <div className="demo-note"><p>Research preview. Official documents and company profiles require review before applicability is established. Do not enter confidential information. Searches and scenario results are saved in a local audit record.</p></div>
    {error && <div role="alert" className="simulation-error"><p>{error}</p><button className="text-button" onClick={() => { setError(""); setLoading(true); setReload(value => value + 1); }}>Retry connection</button></div>}
    {loading && <p role="status">Loading the regulatory workspace…</p>}
    {data && <>
      <div className="v2-metrics"><span><strong>{data.status.documents}</strong> Official documents</span><span><strong>{data.status.versions}</strong> Preserved versions</span><span><strong>{data.entities.length}</strong> Company profiles</span><span><strong>{data.status.reviewed_profiles}</strong> Reviewed profiles</span></div>
      {section === "regulations" && <section><h2>The regulatory library.</h2><p>Publication and effective dates remain unknown until reviewed. A newer download is not proof that a rule is currently applicable.</p>
        {!data.regulations.length && <p className="v2-empty">No official documents have been imported yet. Run the source monitor to create the first baseline.</p>}
        <div className="v2-card-grid">{data.regulations.map(v => <article className="v2-card" key={v.id}><div className="eyebrow">{v.regulator} · VERSION {v.number} · {v.status}</div><h3>{v.title}</h3><p>Published: {v.review?.publication_date || v.metadata.publication_date || "Not established"}</p><p>Effective: {v.review?.effective_from || "Not established"}</p><p>Fetched: {new Date(v.fetched_at).toLocaleString()}</p><OfficialLink version={v} /><button className="text-button" disabled={busy} onClick={() => run(`/versions/${v.id}`, null, setDetail)}>Inspect clauses & version evidence</button></article>)}</div>
        {detail && <section className="v2-detail"><h2>{detail.title} — version {detail.number}</h2><p className="scope-caption">SHA-256: {detail.content_hash}</p><p>Text extraction uses paragraph locators; section headings are heuristic and require review.</p>
          {detail.clauses.slice(0, 40).map(c => <details key={c.id}><summary>{c.page ? `Page ${c.page} · ` : ""}{c.locator} · Section {c.section}</summary><p className="source-excerpt">{c.text}</p></details>)}<p className="scope-caption">Showing {Math.min(40, detail.clauses.length)} of {detail.clauses.length} parsed paragraphs. The complete document is available at the official source.</p></section>}
      </section>}
      {section === "changes" && <section><h2>What changed?</h2><p>Before/after text is preserved with both version IDs. Materiality and legal meaning require review.</p>
        {!data.changes.length && <div className="v2-empty"><h3>No version changes detected yet.</h3><p>The first successful download creates a baseline. A later changed download creates a before/after review here. We do not invent a historical version.</p></div>}
        {data.changes.map(change => <article className="v2-card" key={change.id}><div className="eyebrow">{change.regulator} · REVIEW PENDING</div><h3>{change.title}</h3><p>Detected {new Date(change.detected_at).toLocaleString()} · {change.data.changes.length} text change groups</p><OfficialLink version={change} />
          {!change.data.changes.length && <p>File bytes changed; no normalized paragraph changes were detected.</p>}
          {change.data.changes.slice(0, 30).map((delta, i) => <details key={i}><summary>{delta.type} — change group {i+1}</summary><div className="v2-diff"><div><h4>Before</h4>{delta.before.map(c => <p className="source-excerpt" key={c.id}>{c.text}</p>)}</div><div><h4>After</h4>{delta.after.map(c => <p className="source-excerpt" key={c.id}>{c.text}</p>)}</div></div></details>)}
          {change.data.changes.length > 30 && <p>Showing the first 30 change groups; the API retains the full diff.</p>}</article>)}
      </section>}
      {section === "ask" && <section><h2>Start with the official text.</h2><form onSubmit={event => { event.preventDefault(); run("/ask", { question, regulator: regulator || null, as_of: asOf || null, effective_only: effectiveOnly }); }}>
        <label htmlFor="v2-question">Regulatory question or clause reference</label><textarea id="v2-question" maxLength={2000} required minLength={3} value={question} onChange={e => setQuestion(e.target.value)} placeholder="Search for a requirement, exact phrase, or section number…" />
        <div className="v2-form-row"><div><label htmlFor="v2-regulator">Regulator</label><select id="v2-regulator" value={regulator} onChange={e => setRegulator(e.target.value)}><option value="">All regulators</option><option>RBI</option><option>SEBI</option></select></div><div><label htmlFor="v2-date">Assess as of (optional)</label><input type="date" id="v2-date" value={asOf} onChange={e => setAsOf(e.target.value)} /></div></div>
        <label className="v2-checkbox"><input type="checkbox" checked={effectiveOnly} onChange={e => setEffectiveOnly(e.target.checked)} /> Only reviewed versions effective on the assessment date</label>
        {!effectiveOnly && <p className="scope-caption">Research mode includes latest unreviewed and draft material; results do not establish current obligations.</p>}
        <button className="button" disabled={busy}>Find primary-source evidence</button></form>
        {result?.evidence && <section className="v2-detail"><h3>Evidence: {result.evidence_status.replaceAll("_", " ")}</h3><p>{result.answer}</p><p className="scope-caption">As of {result.as_of} · {result.retrieval_mode} · {result.excluded_versions} ineligible versions excluded · {result.conflicting_documents} overlapping document histories</p>{result.retrieval_notice && <p>{result.retrieval_notice}</p>}
          {result.evidence.map(c => <article className="v2-card" key={c.id}><h3>{c.version.title}</h3><p>{c.version.regulator} · version {c.version.number} · {c.version.status} · {c.locator}{c.page ? ` · page ${c.page}` : ""}</p><p className="source-excerpt">{c.text}</p><OfficialLink version={c.version} /></article>)}{auditButton}</section>}
      </section>}
      {section === "scenario" && <section><h2>Hypothetical scenario — not an actual rule.</h2><p>The same condition matcher powers actual impact and simulation. You explicitly choose the target class; we do not ask a model to guess who is licensed.</p>
        <div className="scenario-examples"><div>{presets.map(([label, type, text]) => <button className="scenario-example" key={type} onClick={() => { setTarget(type); setRule(text); }}>{label}</button>)}</div></div>
        <form onSubmit={e => { e.preventDefault(); run("/simulate", { rule, conditions: { entity_types: [target], jurisdiction: "IN", activity: activity.trim() || null } }); }}>
          <label htmlFor="v2-rule">Hypothetical requirement</label><textarea id="v2-rule" value={rule} minLength={3} maxLength={2000} required onChange={e => setRule(e.target.value)} />
          <div className="v2-form-row"><div><label htmlFor="v2-target">Assumed target entity type</label><select id="v2-target" value={target} onChange={e => setTarget(e.target.value)}>{entityTypes.map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></div><div><label htmlFor="v2-activity">Required activity (optional exact label)</label><input id="v2-activity" maxLength={100} value={activity} onChange={e => setActivity(e.target.value)} placeholder="e.g. customer_onboarding" /></div></div>
          <p className="scope-caption">Scope: India · all {data.entities.length} company profiles. Conditions above are assumptions supplied by you; results do not claim the rule text was legally interpreted.</p><button className="button" disabled={busy}>Evaluate scenario conditions</button>
        </form>{result?.hypothetical && <section className="v2-detail"><div className="eyebrow">HYPOTHETICAL / USER-STATED CONDITIONS</div><h3>{result.rule}</h3><p>{result.assumptions}</p><div className="v2-metrics">{Object.entries(result.counts).map(([key, count]) => <span key={key}><strong>{count}</strong>{labels[key]}</span>)}</div>
          {result.results.map(item => <details key={item.entity_id}><summary>{item.company} — {labels[item.outcome]}</summary><Outcome item={item} /></details>)}{auditButton}</section>}
      </section>}
      {section === "compare" && <section><h2>One obligation set. Side by side.</h2><p>Both profiles are evaluated against the same requirements and assessment date.</p><form onSubmit={e => { e.preventDefault(); run("/compare", { entity_ids: [left, right], as_of: asOf || null }); }}>
        <div className="v2-form-row">{[["left", left, setLeft, "First company"], ["right", right, setRight, "Second company"]].map(([id, value, setter, label]) => <div key={id}><label htmlFor={`v2-${id}`}>{label}</label><select id={`v2-${id}`} required value={value} onChange={e => setter(e.target.value)}><option value="">Select a company</option>{data.entities.map(entity => <option key={entity.id} value={entity.id}>{entity.name}</option>)}</select></div>)}</div>
        <label htmlFor="compare-date">Assess as of (optional)</label><input id="compare-date" type="date" value={asOf} onChange={e => setAsOf(e.target.value)} /><button className="button" disabled={busy || !left || !right || left === right}>Compare applicability</button></form>
        {result?.rows && <section className="v2-detail"><p>{result.reviewed_rows} of {result.total_obligations} candidate obligations shown · {result.as_of}. Reviewed obligations are prioritized.</p>{!result.rows.length && <p>No obligation candidates are available yet.</p>}
          {result.rows.map(row => <article className="v2-card" key={row.obligation.id}><h3>{row.obligation.version.title}</h3><p className="source-excerpt">{row.obligation.review?.quote || row.obligation.quote}</p><OfficialLink version={row.obligation.version} /><div className="v2-diff">{row.results.map(item => <div key={item.entity_id}><h4>{item.company}</h4><Outcome item={item} /></div>)}</div></article>)}{auditButton}</section>}
      </section>}
      {section === "sources" && <section><h2>Source health & review queue.</h2><p>Successful fetches establish freshness, not legal correctness. Ingestion and approvals run through the trusted local CLI; public visitors cannot approve evidence.</p>
        <div className="v2-card-grid">{data.status.sources.map(source => { const sync = data.status.sync_runs.find(run => run.source_id === source.id); return <article className="v2-card" key={source.id}><h3>{source.regulator} · {source.id.replaceAll("_", " ")}</h3><p>{source.coverage}</p><p>Last check: {sync ? new Date(sync.checked_at).toLocaleString() : "Never checked"}</p><p>Status: {sync?.status || "Not started"} · {sync?.checked || 0} documents fetched</p>{sync?.errors.length > 0 && <p>{sync.errors.length} fetch errors. Last check is not a successful sync.</p>}<a href={source.url} target="_blank" rel="noreferrer" className="text-link">Official listing ↗</a></article>; })}</div>
        <p className="scope-caption">Monitoring runs only while the separate hourly watch process is active. Lists may omit older documents; this preview does not claim complete regulator coverage.</p>
        <h3>Obligations awaiting review</h3><p>Extraction finds candidate “shall / must / required to” passages. It does not establish a complete rulebook.</p>
        {data.obligations.slice(0, 30).map(o => <details key={o.id}><summary>{o.version.regulator} · {o.review?.status || "pending"} · {o.action.slice(0, 120)}…</summary><p className="source-excerpt">{o.quote}</p><p className="scope-caption">Obligation ID: {o.id}</p><OfficialLink version={o.version} /><button className="text-button" disabled={busy} onClick={() => run(`/impact/${o.id}`, {}, setImpact)}>Explain applicability to company profiles</button></details>)}
        <p className="scope-caption">Showing {Math.min(30, data.obligations.length)} of {data.obligations.length} candidates. Complete records are available through the API and local review tools.</p>
        {impact && <div className="v2-detail"><h3>Actual-rule applicability review</h3>{impact.results.map(item => <details key={item.entity_id}><summary>{item.company} — {labels[item.outcome]}</summary><Outcome item={item} /></details>)}</div>}
      </section>}
    </>}{busy && <p className="v2-working" role="status">Working with the selected evidence…</p>}
  </div>;
}
