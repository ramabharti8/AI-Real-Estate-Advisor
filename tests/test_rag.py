import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi.testclient import TestClient  # noqa: E402

from ingest_documents import ingest_sample_documents  # noqa: E402
from main import app  # noqa: E402
from rag_common import get_vectorstore  # noqa: E402

client = TestClient(app)


def _ensure_ingested():
    result = ingest_sample_documents()
    assert sum(result.values()) > 0
    return result


def test_ingestion_produces_nonempty_collection():
    _ensure_ingested()
    vectorstore = get_vectorstore()
    raw = vectorstore.get(include=["metadatas"])
    assert len(raw.get("ids", [])) > 0


def test_documents_endpoint_lists_something():
    _ensure_ingested()
    resp = client.get("/documents")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["documents"]) > 0
    assert all("filename" in d and "chunk_count" in d for d in body["documents"])


def test_documents_chat_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _ensure_ingested()
    resp = client.post(
        "/documents/chat",
        json={"question": "What documents are needed for a home loan?", "history": []},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["source_type"] == "template"
    assert len(body["answer"]) > 0
