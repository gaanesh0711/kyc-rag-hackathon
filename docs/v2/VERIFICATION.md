# V2 verification

Verified locally on 7 October 2026. This is a research prototype; tests establish software behavior, not legal accuracy or completeness.

- 33 V2 unit/API tests pass: immutable snapshots, duplicate capture and reversion, source URL restrictions, access-challenge rejection, before/after diffs, review gates, exact quotes, effective periods, overlapping versions, historical profile selection, three-valued applicability, shared scenario/actual matching, symmetric comparison, audit records, and retrieval fallback disclosure.
- 16 existing company-RAG tests pass.
- Frontend lint and production build pass; Git whitespace checks pass.
- Backend `/health` reports ready with the company chain initialized. A live company question returned an answer with three retrieved sources using the locally configured key.
- Browser verification: official library, default exclusion of unreviewed regulations, explicit research search with real SEBI passages and BM25/MiniLM rank fusion, scenario evaluation across all 76 profiles, and comparison of Angel One and Zerodha against the same obligations. Unreviewed data correctly produces unknown results.
- Light/dark preference survives reload.

## Live data boundaries

Two SEBI documents were captured and parsed locally. Their dates and extracted obligation candidates remain unreviewed. All 76 name-grouped company profiles remain unreviewed; this count does not resolve aliases into verified legal entities. No fabricated live amendment was seeded. RBI RSS discovery worked, but document access returned an access challenge and is disclosed as a source failure. The hourly watch command is available but is not installed or running as a scheduler.

Runtime databases, credentials, downloaded source bodies, and test artifacts are excluded from the V2 commit. A fresh checkout needs source synchronization and profile import as described in OPERATIONS.md. The original committed company corpus remains inherited from the base commit.
