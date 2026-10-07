"""Trusted local administration. Review and ingestion writes are not public API routes."""
import argparse
import json
import time
from pathlib import Path
from .models import ObligationReview, ProfileReview, VersionReview
from .sources import REGISTRY, sync_all
from .sources.base import fetch_document
from .store import Store


def main():
    parser = argparse.ArgumentParser(description="FinVisors V2 source monitor and review tools")
    parser.add_argument("--db", help="Separate SQLite database path")
    commands = parser.add_subparsers(dest="command", required=True)
    sync = commands.add_parser("sync")
    sync.add_argument("--limit", type=int, default=3, choices=range(1, 26))
    sync.add_argument("--watch", action="store_true", help="Poll hourly while this process runs")
    fetch = commands.add_parser("fetch")
    fetch.add_argument("--regulator", required=True, choices=["RBI", "SEBI"])
    fetch.add_argument("--url", required=True)
    fetch.add_argument("--title", required=True)
    imp = commands.add_parser("import-companies")
    imp.add_argument("path")
    review = commands.add_parser("review")
    review.add_argument("kind", choices=["version", "obligation", "entity"])
    review.add_argument("id")
    review.add_argument("json_file", help="Explicit reviewer identity, evidence, scope and rationale")
    export = commands.add_parser("export-audit")
    export.add_argument("id")
    export.add_argument("output")
    commands.add_parser("status")
    args = parser.parse_args()
    store = Store(args.db)
    if args.command == "sync":
        while True:
            print(json.dumps(sync_all(store, args.limit), indent=2), flush=True)
            if not args.watch:
                break
            time.sleep(3600)
    elif args.command == "fetch":
        raw, text, metadata = fetch_document({"url": args.url, "title": args.title}, args.regulator)
        print(json.dumps(store.ingest(source_id="manual_official", regulator=args.regulator, url=args.url,
                                      title=args.title, raw=raw, text=text, metadata=metadata)))
    elif args.command == "import-companies":
        print(json.dumps({"company_profiles": store.import_entities(args.path), "review_status": "unreviewed"}))
    elif args.command == "review":
        model = {"version": VersionReview, "obligation": ObligationReview, "entity": ProfileReview}[args.kind]
        data = model.model_validate_json(Path(args.json_file).read_text(encoding="utf-8"))
        store.review(args.kind, args.id, data.model_dump(mode="json"))
        print("Review appended. Previous evidence and reviews retained.")
    elif args.command == "export-audit":
        with store.connect() as db:
            row = db.execute("SELECT * FROM audit WHERE id=?", (args.id,)).fetchone()
        if not row:
            parser.error("Audit record not found")
        # Exclusive creation prevents an export from overwriting a previous report.
        with Path(args.output).open("x", encoding="utf-8") as handle:
            json.dump({**dict(row), "data": json.loads(row["data"])}, handle, indent=2)
    else:
        print(json.dumps({"sources": REGISTRY, "sync_runs": store.sync_status(), "versions": len(store.versions()), "profiles": len(store.entities())}, indent=2))


if __name__ == "__main__":
    main()
