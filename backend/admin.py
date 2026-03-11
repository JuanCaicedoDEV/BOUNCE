"""
Admin API — universities upload their program PDFs here.
Each document is stored in ChromaDB with university_id metadata
so the counselor agent can filter by tenant.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
from pypdf import PdfReader
import io
import uuid

router = APIRouter(prefix="/admin", tags=["admin"])

CHROMA_DIR = str(Path(__file__).parent / "chroma_db")
COLLECTION = "university_programs"

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

def _get_vectorstore() -> Chroma:
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION,
    )

def _extract_text(file_bytes: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n\n".join(
            page.extract_text() or "" for page in reader.pages
        ).strip()
    return file_bytes.decode("utf-8", errors="ignore").strip()


splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)


@router.post("/upload")
async def upload_program(
    university_id: str = Form(...),
    program_name: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload a program PDF and index it into ChromaDB."""
    content = await file.read()
    text = _extract_text(content, file.filename or "")

    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from file.")

    chunks = splitter.split_text(text)
    doc_id = str(uuid.uuid4())

    vs = _get_vectorstore()
    vs.add_texts(
        texts=chunks,
        metadatas=[
            {
                "university_id": university_id,
                "program_name": program_name,
                "filename": file.filename,
                "doc_id": doc_id,
            }
            for _ in chunks
        ],
        ids=[f"{doc_id}_{i}" for i in range(len(chunks))],
    )

    return {
        "status": "indexed",
        "program_name": program_name,
        "university_id": university_id,
        "chunks": len(chunks),
        "doc_id": doc_id,
    }


@router.get("/programs/{university_id}")
def list_programs(university_id: str):
    """List all programs uploaded by a university."""
    vs = _get_vectorstore()
    results = vs.get(where={"university_id": university_id})

    # Deduplicate by doc_id
    seen = {}
    for meta in results.get("metadatas", []):
        doc_id = meta.get("doc_id")
        if doc_id and doc_id not in seen:
            seen[doc_id] = {
                "doc_id": doc_id,
                "program_name": meta.get("program_name"),
                "filename": meta.get("filename"),
            }

    return {"university_id": university_id, "programs": list(seen.values())}


@router.delete("/programs/{university_id}/{doc_id}")
def delete_program(university_id: str, doc_id: str):
    """Delete all chunks of a program from ChromaDB."""
    vs = _get_vectorstore()
    results = vs.get(where={"doc_id": doc_id})
    ids = results.get("ids", [])

    if not ids:
        raise HTTPException(status_code=404, detail="Program not found.")

    # Verify ownership
    metas = results.get("metadatas", [])
    if any(m.get("university_id") != university_id for m in metas):
        raise HTTPException(status_code=403, detail="Not authorized.")

    vs.delete(ids=ids)
    return {"status": "deleted", "doc_id": doc_id, "chunks_removed": len(ids)}
