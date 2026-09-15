"""Ingest sample and uploaded documents into the local ChromaDB vector store.

Re-runnable / idempotent: each document is identified by a deterministic
source id (filename), and re-ingesting the same file replaces its previous
chunks rather than duplicating them.

Usage:
    python src/ingest_documents.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from rag_common import (  # noqa: E402
    DOCS_DIR,
    get_embeddings,
    get_vectorstore,
    load_and_chunk_file,
)


def ingest_sample_documents() -> dict:
    """Ingest every file in data/documents/ as source_type='sample'."""
    if not os.path.isdir(DOCS_DIR):
        print(f"No documents directory found at {DOCS_DIR}")
        return {}

    vectorstore = get_vectorstore()
    summary = {}
    for filename in sorted(os.listdir(DOCS_DIR)):
        if not filename.lower().endswith((".md", ".txt")):
            continue
        path = os.path.join(DOCS_DIR, filename)
        chunks = load_and_chunk_file(path, filename, source_type="sample")

        # Idempotency: delete any existing chunks for this filename first.
        try:
            vectorstore.delete(where={"filename": filename})
        except Exception:
            pass

        if chunks:
            vectorstore.add_documents(chunks)
        summary[filename] = len(chunks)
        print(f"Ingested {filename}: {len(chunks)} chunks")

    return summary


if __name__ == "__main__":
    print(f"Using embeddings: {type(get_embeddings()).__name__}")
    result = ingest_sample_documents()
    total = sum(result.values())
    print(f"\nDone. {len(result)} document(s), {total} chunk(s) indexed.")
