"""FastAPI router for the document Q&A (RAG) feature."""
import os
import shutil
import tempfile
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from rag_common import (
    build_rag_answer,
    get_vectorstore,
    list_indexed_documents,
    load_and_chunk_file,
)
from schemas import (
    DocumentChatRequest,
    DocumentChatResponse,
    DocumentInfo,
    DocumentListResponse,
    DocumentUploadResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


@router.get("", response_model=DocumentListResponse)
def list_documents():
    docs = list_indexed_documents()
    return DocumentListResponse(documents=[DocumentInfo(**d) for d in docs])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    # Prefix with a short uuid so re-uploads of the same filename don't collide,
    # but keep the original name in metadata for a human-readable listing.
    filename = file.filename or f"upload-{uuid.uuid4().hex[:8]}{ext}"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, filename)
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            chunks = load_and_chunk_file(tmp_path, filename, source_type="uploaded")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}") from exc

    if not chunks:
        raise HTTPException(status_code=400, detail="No extractable text found in file.")

    vectorstore = get_vectorstore()
    try:
        vectorstore.delete(where={"filename": filename})
    except Exception:
        pass
    vectorstore.add_documents(chunks)

    return DocumentUploadResponse(filename=filename, chunk_count=len(chunks), source_type="uploaded")


@router.post("/chat", response_model=DocumentChatResponse)
def chat_with_documents(req: DocumentChatRequest):
    vectorstore = get_vectorstore()
    try:
        docs = vectorstore.similarity_search(req.question, k=4)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {exc}") from exc

    answer, source_type = build_rag_answer(req.question, docs)
    sources = sorted({d.metadata.get("filename", "unknown") for d in docs})

    return DocumentChatResponse(answer=answer, sources=sources, source_type=source_type)
