import json
import os
import sqlite3
import uuid
from contextlib import contextmanager, closing
from datetime import datetime, timezone
from pathlib import Path

from .parsing import clauses, diff_clauses, digest, obligation_candidates


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return uuid.uuid4().hex


class Store:
    def __init__(self, path=None):
        self.path = Path(path or os.getenv("REGULATORY_DB", Path(__file__).resolve().parents[1] / "data_v2/regulatory.sqlite3"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, source_id TEXT, url TEXT UNIQUE, title TEXT, regulator TEXT, source_kind TEXT);
            CREATE TABLE IF NOT EXISTS versions(id TEXT PRIMARY KEY, document_id TEXT REFERENCES documents(id), number INTEGER,
              fetched_at TEXT, content_hash TEXT, normalized_hash TEXT, raw BLOB, text TEXT, metadata TEXT, previous_id TEXT,
              UNIQUE(document_id,number));
            CREATE TABLE IF NOT EXISTS clauses(id TEXT PRIMARY KEY, version_id TEXT REFERENCES versions(id), data TEXT);
            CREATE TABLE IF NOT EXISTS obligations(id TEXT PRIMARY KEY, version_id TEXT REFERENCES versions(id), data TEXT);
            CREATE TABLE IF NOT EXISTS changes(id TEXT PRIMARY KEY, document_id TEXT REFERENCES documents(id), version_id TEXT,
              previous_id TEXT, detected_at TEXT, data TEXT);
            CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY AUTOINCREMENT, target_type TEXT, target_id TEXT, created_at TEXT, data TEXT);
            CREATE TABLE IF NOT EXISTS entities(id TEXT PRIMARY KEY, name TEXT, data TEXT);
            CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY, created_at TEXT, kind TEXT, data TEXT);
            CREATE TABLE IF NOT EXISTS sync_runs(id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT, checked_at TEXT, data TEXT);
            CREATE INDEX IF NOT EXISTS version_documents ON versions(document_id, number);
            CREATE INDEX IF NOT EXISTS review_targets ON reviews(target_type,target_id,id);
            """)
            for table in ["versions", "clauses", "obligations", "changes", "audit", "reviews", "entities", "documents", "sync_runs"]:
                for action in ["UPDATE", "DELETE"]:
                    db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'Append-only evidence'); END")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def ingest(self, *, source_id, url, title, regulator, raw, text, metadata=None, source_kind="official"):
        if len(text.strip()) < 100:
            raise ValueError("Document text is empty or too short for reliable ingestion")
        metadata = metadata or {}
        document_id = digest(url)[:24]
        raw_hash = digest(raw)
        normalized_hash = digest(" ".join(text.split()))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT OR IGNORE INTO documents VALUES(?,?,?,?,?,?)", (document_id, source_id, url, title, regulator, source_kind))
            previous = db.execute("SELECT * FROM versions WHERE document_id=? ORDER BY number DESC LIMIT 1", (document_id,)).fetchone()
            if previous and previous["content_hash"] == raw_hash:
                return {"document_id": document_id, "version_id": previous["id"], "created": False}
            version_id = uid()
            number = previous["number"] + 1 if previous else 1
            db.execute("INSERT INTO versions VALUES(?,?,?,?,?,?,?,?,?,?)", (version_id, document_id, number, now(), raw_hash, normalized_hash,
                raw, text, json.dumps(metadata), previous["id"] if previous else None))
            items = [{**item, "id": uid(), "version_id": version_id} for item in clauses(text)]
            db.executemany("INSERT INTO clauses VALUES(?,?,?)", [(item["id"], version_id, json.dumps(item)) for item in items])
            for obligation in obligation_candidates(items):
                db.execute("INSERT INTO obligations VALUES(?,?,?)", (uid(), version_id, json.dumps(obligation)))
            if previous:
                old = [json.loads(row["data"]) for row in db.execute("SELECT data FROM clauses WHERE version_id=? ORDER BY rowid", (previous["id"],))]
                change = {"changes": diff_clauses(old, items), "normalized_text_changed": previous["normalized_hash"] != normalized_hash,
                          "review_status": "pending", "detection": "text_diff_not_legal_interpretation"}
                db.execute("INSERT INTO changes VALUES(?,?,?,?,?,?)", (uid(), document_id, version_id, previous["id"], now(), json.dumps(change)))
        return {"document_id": document_id, "version_id": version_id, "created": True}

    def review(self, kind, target_id, data):
        tables = {"version": "versions", "obligation": "obligations", "entity": "entities"}
        if kind not in tables:
            raise ValueError("Unknown review target")
        with self.connect() as db:
            target = db.execute(f"SELECT * FROM {tables[kind]} WHERE id=?", (target_id,)).fetchone()
            if not target:
                raise ValueError("Review target not found")
            if kind == "obligation":
                original = json.loads(target["data"])
                clause = json.loads(db.execute("SELECT data FROM clauses WHERE id=?", (original["clause_id"],)).fetchone()[0])
                if data["quote"] not in clause["text"]:
                    raise ValueError("Review quote must be an exact fragment of the linked clause")
                if data["status"] == "approved" and not data["conditions"]["entity_types"]:
                    raise ValueError("Approved obligations need explicit applicability conditions")
            db.execute("INSERT INTO reviews(target_type,target_id,created_at,data) VALUES(?,?,?,?)", (kind, target_id, now(), json.dumps(data)))

    def latest_review(self, kind, target_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM reviews WHERE target_type=? AND target_id=? ORDER BY id DESC LIMIT 1", (kind, target_id)).fetchone()
        return {**json.loads(row["data"]), "reviewed_at": row["created_at"]} if row else None

    def review_history(self, kind, target_id):
        with self.connect() as db:
            return [{**json.loads(row["data"]), "reviewed_at": row["created_at"], "review_id": row["id"]}
                    for row in db.execute("SELECT * FROM reviews WHERE target_type=? AND target_id=? ORDER BY id", (kind, target_id))]

    def versions(self, document_id=None):
        with self.connect() as db:
            rows = db.execute("SELECT v.id,v.document_id,v.number,v.fetched_at,v.content_hash,v.normalized_hash,v.metadata,v.previous_id,d.title,d.regulator,d.url,d.source_kind,d.source_id FROM versions v JOIN documents d ON d.id=v.document_id " +
                ("WHERE d.id=? " if document_id else "") + "ORDER BY v.fetched_at DESC", (document_id,) if document_id else ()).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item["metadata"])
            item["review"] = self.latest_review("version", item["id"])
            item["status"] = item["review"]["status"] if item["review"] else item["metadata"].get("status", "unreviewed")
            result.append(item)
        return result

    def version(self, version_id):
        item = next((v for v in self.versions() if v["id"] == version_id), None)
        if not item:
            raise KeyError(version_id)
        with self.connect() as db:
            item["clauses"] = [json.loads(row[0]) for row in db.execute("SELECT data FROM clauses WHERE version_id=? ORDER BY rowid", (version_id,))]
        return item

    def obligations(self):
        versions = {v["id"]: v for v in self.versions()}
        with self.connect() as db:
            rows = db.execute("SELECT * FROM obligations ORDER BY rowid").fetchall()
        return [{"id": row["id"], "version_id": row["version_id"], **json.loads(row["data"]),
                 "review": self.latest_review("obligation", row["id"]), "version": versions[row["version_id"]]} for row in rows]

    def changes(self):
        with self.connect() as db:
            return [{**dict(row), "data": json.loads(row["data"])} for row in db.execute("SELECT c.*,d.title,d.regulator,d.url,d.source_kind FROM changes c JOIN documents d ON d.id=c.document_id ORDER BY detected_at DESC")]

    def import_entities(self, chroma_path):
        # Read the bundled baseline without opening a writable Chroma client.
        with closing(sqlite3.connect(Path(chroma_path).resolve().as_uri() + "?mode=ro", uri=True)) as source:
            rows = source.execute("SELECT id,key,string_value FROM embedding_metadata WHERE key IN ('company_name','regulator','vertical','source_doc','chroma:document')").fetchall()
        grouped = {}
        for record_id, key, value in rows:
            grouped.setdefault(record_id, {})[key] = value
        companies = {}
        for record in grouped.values():
            if record.get("company_name"):
                companies.setdefault(record["company_name"], []).append(record)
        with self.connect() as db:
            for name, records in companies.items():
                data = {"records": records, "profile_status": "unreviewed", "entity_types": [], "activities": [],
                        "source_kind": "secondary_dataset", "jurisdiction": None}
                db.execute("INSERT OR IGNORE INTO entities VALUES(?,?,?)", (digest(name)[:24], name, json.dumps(data)))
        return len(companies)

    def entities(self):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM entities ORDER BY name").fetchall()
        return [{"id": row["id"], "name": row["name"], **json.loads(row["data"]), "review": self.latest_review("entity", row["id"]),
                 "review_history": self.review_history("entity", row["id"])} for row in rows]

    def audit(self, kind, data):
        audit_id = uid()
        with self.connect() as db:
            db.execute("INSERT INTO audit VALUES(?,?,?,?)", (audit_id, now(), kind, json.dumps(data)))
        return audit_id

    def record_sync(self, source_id, data):
        with self.connect() as db:
            db.execute("INSERT INTO sync_runs(source_id,checked_at,data) VALUES(?,?,?)", (source_id, now(), json.dumps(data)))

    def sync_status(self):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM sync_runs WHERE id IN (SELECT max(id) FROM sync_runs GROUP BY source_id)").fetchall()
        return [{"source_id": row["source_id"], "checked_at": row["checked_at"], **json.loads(row["data"])} for row in rows]
