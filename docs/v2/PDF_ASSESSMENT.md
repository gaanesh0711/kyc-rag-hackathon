# KYC RAG V2: full PDF assessment and implementation decisions

Reviewed all 43 pages of `KYC RAG_ What You Should Build Next and How to Differentiate It.pdf` on 6 October 2026, against baseline commit `6d4c5cf` in `gaanesh0711/kyc-rag-hackathon`.

## Main finding

The report is right about the missing regulatory evidence layer. FinVisory company descriptions are secondary business context; they cannot establish official rule text, effective dates, licensing, or legal applicability. Keep the existing company RAG as the base and add a separate versioned primary-source layer.

Some observations in the report refer to the older repository: FinVisors already replaced “Verified Citations” with “Retrieved Evidence,” added a simulator, fixed backend readiness, and corrected the 80-record / 76-distinct-company distinction. The simulator critique still applies: asking Gemini to label companies from descriptions is exploratory inference, not deterministic applicability.

## Recommendation-by-recommendation disposition

| PDF pages | Recommendation | V2 decision and implementation | Remaining limits |
|---|---|---|---|
| 1-8, 33-34 | Separate official regulators from company context; source registry and adapters | Built RBI RSS and SEBI circular/master-circular adapters; bounded sync CLI and hourly watch mode; source-health UI | First listing/feed window plus bounded known-document rechecks, not an exhaustive archive. RBI document access currently challenged. IRDAI/FIU deferred |
| 8-10, 28, 32-35 | Immutable versions, hashes, before/after, temporal status | Append-only SQLite document/version/clause/change records, raw bytes, SHA-256, text diffs, explicit review/effective periods | Text diffs are not semantic legal diffs. Renumbering/moves and cross-document amendment/supersession require later relation mapping |
| 10-12, 28-29, 34 | Structured obligations and review gate | Candidate modal-language passages linked to exact version/paragraph; explicit reviewed conditions and action, exact-quote validation; trusted CLI approvals | Heuristic extraction is not complete. Complex thresholds, exceptions, conditional branches and deadlines are retained in text but not fully normalized |
| 12-13, 20-21, 31-34 | Explainable applicability with UNKNOWN | Shared deterministic engine for reviewed entity types, jurisdiction, optional activity, dates, profile history, explicit missing-fact reasons | Seeded company profiles have no verified licences; initial UNKNOWN results are intentional. Three target classes are supported |
| 19-21, 35 | Redesign hypothetical simulator | Dedicated V2 scenarios with explicit user-stated target conditions; same matcher as actual impact; separate audit kind and no writes to official corpus | Free-text rule is a scenario description, not silently parsed legal conditions. Original exploratory simulator remains on the base branch |
| 21-23, 36-37 | Evidence strength instead of numerical confidence | Show official URL, version/hash, review status, date eligibility, retrieval method, excluded versions, overlapping histories and freshness checks | No percentage or “strong” badge inferred from source count. Claim-level citation coverage and general cross-document contradiction detection deferred |
| 23-25, 37 | Symmetric comparison | Both companies evaluated against one shared obligation set; explanations and source text | UI initially shows 20 prioritized obligations and discloses total; endpoint maximum 50 per review |
| 24-25, 29-30, 36 | Regulation-first retrieval and routing | Separate V2 tools/routes; BM25 plus optional existing MiniLM semantic rank fusion; regulator/date/status filters; exact primary-source passages | Explicit UI routing, no opaque intent classifier. No cross-encoder reranker. V2 answers are extractive; existing company Gemini Q&A remains accessible |
| 25-26, 38-39 | Audit data before PDF memo | Persist inputs, outputs, exact evidence/version/profile reviews, timestamps and engine/retrieval identifiers; per-result JSON export | SQLite append-only triggers are not tamper-proof against database administrators. No signed audit ledger; PDF memo deferred |
| 3, 37-38 | Relevant notifications | Source-health and changes screens built | External alerts deferred until coverage, review, consent and reliable detection are established |
| 13-19, 39-42 | India-focused differentiation, avoid unrelated competitors/features | Position as transparent regulatory-impact research, not identity verification or AML transaction surveillance | Competitor acquisition/coverage claims in the PDF were not adopted as independently verified marketing claims |

## What we should not build now

- Transaction AML monitoring, sanctions screening, identity verification, trading surveillance, or automated eligibility decisions. The repository has neither the operational data nor validation for those products.
- Full GRC controls/policies/tasks or global jurisdiction coverage. Establish narrow rule-to-profile evidence first.
- Numerical legal-confidence scores, “verified” claims based on vector similarity, or a claim that all companies have established regulatory classifications.
- Automatic approval of extracted obligations, inferred licences, or unknown dates. A draft must never become an active requirement by default.
- Destructive regulator reindexing, replacing old source versions, or mixing hypothetical text into the official corpus.
- Scheduled emails/Slack alerts, polished PDF memos, or more UI decoration before reliable ingestion and reviewed examples exist.
- A new graph database, model provider, or enterprise infrastructure merely because a diagram resembles a graph. SQLite relational links are enough for this single-process prototype; PostgreSQL is the next step for hosted concurrent operation.

## Version preservation

- `main` preserves the original hackathon baseline.
- `codex/finvisors-public-demo` preserves the working FinVisors company RAG and original exploratory simulator.
- `kyc-rag_V2` branches from `6d4c5cf` and adds the regulatory foundation. It is not merged into either base.
- V2 runtime evidence is stored in ignored `data_v2/`; the original PDF and committed Chroma records remain in place.
- The unfinished light/dark preference was completed in V2; FinVisors remains the product brand.

## Concrete acceptance boundary

This is a working V2 research foundation, not a validated autonomous regulatory-intelligence service. Before calling it production-ready, obtain human-reviewed entity profiles and obligations, verify parser accuracy against a representative gold set, expand monitoring coverage with compliant access, implement authenticated tenant-bound audit/review access and retention, add hosted scheduler/health alerts and backups, and perform deployment security/cost testing.

A real “What changed?” event only appears after the same document changes between successful captures. The software is tested with synthetic before/after fixtures, but no synthetic amendment is presented as a live regulator update.

## Primary-source verification

The official RBI RSS page confirms feed-based notifications: https://www.rbi.org.in/Scripts/rss.aspx

SEBI publishes master circulars at: https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=6

The live local check discovered the RBI feed but encountered a document access challenge. SEBI official PDFs were successfully downloaded and parsed. These facts establish connector behavior, not regulatory completeness or current legal applicability.
