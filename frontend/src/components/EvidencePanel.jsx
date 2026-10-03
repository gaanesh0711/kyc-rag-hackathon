import { FileText, ChevronDown } from "lucide-react";

export default function EvidencePanel({ sources }) {
  return (
    <aside className="evidence-panel" aria-label="Retrieved source evidence">
      <div className="panel-heading">
        <span className="eyebrow">RETRIEVED EVIDENCE</span>
        <span className="count-badge">{sources.length}</span>
      </div>
      <p className="panel-description">
        Retrieved records provide context. They are not independently verified
        citations.
      </p>
      {sources.length ? (
        sources.map((source, index) => (
          <article
            className="source-record"
            key={`${source.document}-${source.company}-${index}`}
          >
            <div className="source-index">
              <FileText size={17} /> RECORD {String(index + 1).padStart(2, "0")}
            </div>
            <h3>{source.company || "Company not specified"}</h3>
            <span className="regulator-label">
              {source.regulator || "Regulator not specified"}
            </span>
            <p className="source-sector">
              {source.vertical || "Sector not specified"}
            </p>
            <div className="source-document">
              <span>DOCUMENT</span>
              <p>{source.document || "Document not specified"}</p>
            </div>
            <details>
              <summary>
                Read source excerpt <ChevronDown size={16} />
              </summary>
              <p className="source-excerpt">
                {source.excerpt || "No excerpt was returned for this record."}
              </p>
            </details>
          </article>
        ))
      ) : (
        <div className="no-evidence">
          <FileText size={24} />
          <h3>No records returned.</h3>
          <p>
            This response has no supporting source records. Try a more focused
            question.
          </p>
        </div>
      )}
    </aside>
  );
}
