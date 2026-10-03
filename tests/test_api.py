"""API contract tests: no live provider, embeddings, or vector database required."""
import importlib
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

rag_stub = types.ModuleType("rag_chain")
rag_stub.RetrievalQAChain = object
rag_stub.get_rag_chain = lambda **kwargs: None
with patch.dict(sys.modules, {"rag_chain": rag_stub}):
    api = importlib.import_module("main")


class ApiTests(unittest.TestCase):
    def setUp(self):
        api.request_counts.clear()
        self.doc = SimpleNamespace(page_content="Evidence " * 100,
            metadata={"company_name": "Example entity", "regulator": "SEBI",
                      "vertical": "Wealthtech", "source_doc": "example.pdf"})
        self.chain = SimpleNamespace(invoke=lambda value: {
            "result": "A grounded answer", "source_documents": [self.doc]})
        api.chain = self.chain
        self.client = TestClient(api.app)

    def test_answer_contract_and_complete_excerpt(self):
        response = self.client.post("/ask", json={"question": "  Regulatory question?  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["question"], "Regulatory question?")
        source = response.json()["sources"][0]
        self.assertEqual(source["company"], "Example entity")
        self.assertEqual(source["excerpt"], self.doc.page_content)
        self.assertEqual(response.json()["answer"], "A grounded answer")

    def test_blank_and_oversize_questions_are_rejected(self):
        self.assertEqual(self.client.post("/ask", json={"question": "   "}).status_code, 400)
        self.assertEqual(self.client.post("/ask", json={"question": "x" * 2001}).status_code, 422)

    def test_health_tracks_initialization(self):
        self.assertEqual(self.client.get("/health").json()["status"], "ready")
        api.chain = None
        self.assertEqual(self.client.get("/health").json()["status"], "degraded")
        self.assertFalse(self.client.get("/health").json()["chain_initialized"])

    def test_provider_error_does_not_expose_internal_message(self):
        def fail(value):
            raise RuntimeError("private-provider-key-and-internal-path")
        api.chain = SimpleNamespace(invoke=fail)
        with self.assertLogs(api.logger, level="ERROR"):
            response = self.client.post("/ask", json={"question": "Question"})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private-provider", response.text)

    def test_initialization_error_is_actionable(self):
        api.chain = None
        with patch.object(api, "get_rag_chain", side_effect=RuntimeError("secret")):
            with self.assertLogs(api.logger, level="ERROR"):
                response = self.client.post("/ask", json={"question": "Question"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret", response.text)

    def test_demo_rate_limit(self):
        for _ in range(10):
            self.assertEqual(self.client.post("/ask", json={"question": "Question"}).status_code, 200)
        response = self.client.post("/ask", json={"question": "Question"})
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)
        with patch.object(api.time, "monotonic", return_value=api.time.monotonic() + 61):
            self.assertEqual(self.client.post("/ask", json={"question": "Question"}).status_code, 200)

    def test_cors_allows_local_frontend_and_rejects_unknown_origin(self):
        headers = {"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"}
        self.assertEqual(self.client.options("/ask", headers=headers).status_code, 200)
        headers["Origin"] = "https://untrusted.example"
        self.assertEqual(self.client.options("/ask", headers=headers).status_code, 400)

    def test_capacity_guard_releases_slots(self):
        for _ in range(3):
            api.request_slots.acquire()
        try:
            self.assertEqual(self.client.post("/ask", json={"question": "Question"}).status_code, 503)
        finally:
            for _ in range(3):
                api.request_slots.release()
        self.assertEqual(self.client.post("/ask", json={"question": "Question"}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
