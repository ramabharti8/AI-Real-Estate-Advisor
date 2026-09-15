"""Shared helpers for the document Q&A (RAG) feature.

Follows the same graceful-degradation philosophy as app/insights.py:
- Embeddings: OpenAIEmbeddings if OPENAI_API_KEY is set, otherwise a free
  local HuggingFace sentence-transformers model (no API key required).
- Chat/answer generation: OpenAI-compatible LLM if a key is set, otherwise
  fall back to returning the most relevant retrieved chunk(s) verbatim.
"""
import os

from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = os.path.dirname(__file__)
DOCS_DIR = os.path.join(BASE_DIR, "..", "data", "documents")
CHROMA_DIR = os.path.join(BASE_DIR, "vectorstore", "chroma")
COLLECTION_NAME = "real_estate_docs"

_LOCAL_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_embeddings = None
_vectorstore = None


def get_embeddings():
    """Return a LangChain embeddings object, OpenAI if a key is set else local."""
    global _embeddings
    if _embeddings is not None:
        return _embeddings

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        from langchain_openai import OpenAIEmbeddings

        _embeddings = OpenAIEmbeddings(api_key=api_key, model="text-embedding-3-small")
    else:
        from langchain_huggingface import HuggingFaceEmbeddings

        _embeddings = HuggingFaceEmbeddings(model_name=_LOCAL_EMBED_MODEL)
    return _embeddings


def get_vectorstore():
    """Return (and lazily create) the persistent Chroma vector store."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    from langchain_chroma import Chroma

    os.makedirs(CHROMA_DIR, exist_ok=True)
    _vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_DIR,
    )
    return _vectorstore


def load_and_chunk_file(path: str, filename: str, source_type: str):
    """Load a .md/.txt/.pdf file and split into LangChain Documents with metadata."""
    from langchain_core.documents import Document

    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        with open(path, encoding="utf-8") as f:
            text = f.read()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=120, separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_text(text)

    docs = []
    for i, chunk in enumerate(chunks):
        docs.append(
            Document(
                page_content=chunk,
                metadata={
                    "filename": filename,
                    "source_type": source_type,
                    "chunk_index": i,
                },
            )
        )
    return docs


def list_indexed_documents() -> list[dict]:
    """Aggregate chunk metadata into a per-document summary."""
    vectorstore = get_vectorstore()
    try:
        raw = vectorstore.get(include=["metadatas"])
    except Exception:
        return []

    metadatas = raw.get("metadatas") or []
    summary: dict[str, dict] = {}
    for meta in metadatas:
        if not meta:
            continue
        filename = meta.get("filename", "unknown")
        entry = summary.setdefault(
            filename, {"filename": filename, "chunk_count": 0, "source_type": meta.get("source_type", "uploaded")}
        )
        entry["chunk_count"] += 1
    return sorted(summary.values(), key=lambda d: d["filename"])


RAG_SYSTEM_PROMPT = (
    "You are a concise, neutral real-estate document assistant. Answer the user's "
    "question using ONLY the provided context excerpts from property-related documents. "
    "If the context does not contain the answer, say so plainly rather than guessing. "
    "Keep answers to 2-5 sentences and avoid presenting anything as definitive legal advice."
)


def build_rag_answer(question: str, docs) -> tuple[str, str]:
    """Return (answer, source_type). Uses an LLM if a key is set, else a
    template-style fallback that returns the top retrieved chunk(s) verbatim."""
    api_key = os.getenv("OPENAI_API_KEY")
    context = "\n\n---\n\n".join(d.page_content for d in docs)

    if not api_key:
        if not docs:
            return (
                "No relevant indexed documents were found for this question. "
                "(Unranked retrieval fallback -- set OPENAI_API_KEY for AI-synthesized answers.)",
                "template",
            )
        top = docs[0].page_content.strip()
        note = (
            "\n\n[This is an unranked, un-synthesized excerpt retrieved from the most similar "
            "indexed document chunk -- not an LLM-generated answer. Set OPENAI_API_KEY for a "
            "synthesized response.]"
        )
        return top + note, "template"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}"
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        text = response.choices[0].message.content.strip()
        return text, "llm"
    except Exception:
        if docs:
            return docs[0].page_content.strip(), "template"
        return "Unable to generate an answer at this time.", "template"
