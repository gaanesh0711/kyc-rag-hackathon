import {
  ArrowUpRight,
  ArrowRight,
  FileText,
  Quote,
  ScanLine,
  Layers,
  Search,
} from "lucide-react";

const sectors = [
  "Wealthtech & investment",
  "Insurtech",
  "Payments & wallets",
  "Credit & lending",
  "Fintech infrastructure",
  "Crypto & VDA",
];

export default function Landing() {
  return (
    <>
      <section className="hero content-width">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="little-line" /> BUILT FOR A CLOSER LOOK
          </div>
          <h1>
            Ask the question.
            <br />
            Inspect the
            <br />
            <em>evidence.</em>
          </h1>
          <p className="hero-description">
            Follow official regulatory evidence from document versions to company
            applicability. Explore changes, compare profiles, and test hypothetical
            conditions with FinVisors.
          </p>
          <div className="hero-actions">
            <a href="#v2/regulations" className="button">
              Explore regulations <ArrowUpRight size={19} />
            </a>
            <a href="#approach" className="text-link">
              See how it works <ArrowRight size={17} />
            </a>
          </div>
          <p className="hero-caption">
            For compliance, legal, risk, and audit teams.
          </p>
        </div>
        <div
          className="evidence-illustration"
          aria-label="Illustration of a regulatory question connected to a source record"
        >
          <div className="illustration-index">
            FINVISORS / RESEARCH METHOD <span>001</span>
          </div>
          <div className="question-slip">
            <Search size={18} />
            <span>What does the source actually say?</span>
          </div>
          <div className="document-sheet">
            <div className="sheet-top">
              <span>
                <FileText size={19} /> SOURCE RECORD
              </span>
              <span>FV / 01</span>
            </div>
            <div className="sheet-title">
              Context.
              <br />
              Considerations.
              <br />
              <em>Evidence.</em>
            </div>
            <div className="document-lines">
              <span />
              <span />
              <span />
              <span />
            </div>
            <div className="highlight-line">The detail behind the answer.</div>
            <div className="sheet-bottom">
              <span>COMPANY · REGULATOR · SECTOR</span>
              <Quote size={23} />
            </div>
          </div>
          <div className="evidence-stamp">
            <ScanLine size={19} />
            <span>
              SOURCE
              <br />
              IN VIEW
            </span>
          </div>
          <div className="illustration-caption">
            <span className="little-line" /> An answer is the beginning of the
            review.
          </div>
        </div>
      </section>
      <section
        className="regulator-strip"
        aria-label="Dataset regulator coverage"
      >
        <div className="content-width">
          <span className="eyebrow">INDIAN FINTECH CONTEXT</span>
          <span>RBI</span>
          <span>SEBI</span>
          <span>IRDAI</span>
          <span>FIU-IND</span>
          <span className="strip-caption">
            As represented in the source dataset
          </span>
        </div>
      </section>
      <section id="approach" className="approach content-width section-space">
        <div className="section-heading">
          <div className="eyebrow">01 / THE APPROACH</div>
          <h2>
            A research desk.
            <br />
            With the footnotes attached.
          </h2>
          <p>
            Move from a focused question to an answer and its supporting
            records, without losing the context along the way.
          </p>
        </div>
        <div className="steps">
          {[
            [
              "01",
              Search,
              "Start with a question.",
              "Ask about a company, regulator, or compliance consideration within the dataset.",
            ],
            [
              "02",
              Layers,
              "Bring the records into view.",
              "Relevant company records are retrieved from the indexed source dataset.",
            ],
            [
              "03",
              FileText,
              "Read beyond the answer.",
              "Examine company, regulator, sector, document, and excerpt details alongside the response.",
            ],
          ].map(([number, Icon, title, text]) => (
            <article className="step" key={number}>
              <div className="step-top">
                <span>{number}</span>
                <Icon size={23} strokeWidth={1.5} />
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>
      <section id="coverage" className="coverage-section">
        <div className="content-width coverage-grid">
          <div>
            <div className="eyebrow">02 / THE RESEARCH CONTEXT</div>
            <h2>
              Different sectors.
              <br />A shared need for clarity.
            </h2>
            <p>
              The bundled FinVisory dataset describes company-level regulatory
              considerations across Indian fintech sectors.
            </p>
            <a href="#workspace" className="text-link">
              Explore company research <ArrowUpRight size={18} />
            </a>
          </div>
          <ul className="sector-list">
            {sectors.map((sector, index) => (
              <li key={sector}>
                <span className="sector-number">0{index + 1}</span>
                {sector}
              </li>
            ))}
          </ul>
        </div>
      </section>
      <section className="trust-section content-width section-space">
        <div className="eyebrow">03 / KNOW THE BOUNDARIES</div>
        <div className="trust-grid">
          <h2>
            Useful research.
            <br />
            <em>Human judgment.</em>
          </h2>
          <div>
            <p>
              FinVisors helps you explore the supplied dataset. It does not
              verify identities, screen sanctions, or determine whether an
              entity is compliant.
            </p>
            <p>
              Answers may be incomplete or incorrect. Inspect the source
              evidence and confirm current requirements with authoritative
              sources before making a decision.
            </p>
            <span className="boundary-label">
              Source-based context, not allegations of wrongdoing.
            </span>
          </div>
        </div>
      </section>
      <section className="closing-section">
        <div className="content-width">
          <div className="eyebrow">YOUR NEXT QUESTION STARTS HERE</div>
          <h2>
            Bring a question.
            <br />
            Leave with more context.
          </h2>
          <a className="button button-ivory" href="#workspace">
            Open the research workspace <ArrowUpRight size={18} />
          </a>
        </div>
      </section>
    </>
  );
}
