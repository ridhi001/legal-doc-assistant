from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import io

from core import get_llm, setup_kb, create_graph, add_document_to_kb

app = FastAPI(title="Legal Document Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_llm = None
_embedder = None
_collection = None
_agent = None


@app.on_event("startup")
async def startup():
    global _llm, _embedder, _collection, _agent
    _llm = get_llm()
    _embedder, _collection = setup_kb()
    _agent = create_graph(_llm, _embedder, _collection)


class ChatRequest(BaseModel):
    question: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    thread_id: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    tid = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}}
    result = _agent.invoke({"question": req.question}, config=config)
    return ChatResponse(
        answer=result.get("answer", "Sorry, I couldn't process that."),
        sources=result.get("sources", []),
        thread_id=tid,
    )


@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    label: str = Form(default=""),
):
    content = await file.read()
    doc_label = label.strip() or file.filename or "Uploaded Document"
    doc_id = f"upload_{uuid.uuid4().hex[:8]}"

    if file.filename and file.filename.endswith(".pdf"):
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        except ImportError:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        text = content.decode("utf-8", errors="ignore")

    if not text.strip():
        return {"success": False, "error": "Could not extract text from file. Try a text-based PDF."}

    add_document_to_kb(_embedder, text, doc_id, doc_label)
    word_count = len(text.split())
    return {"success": True, "label": doc_label, "word_count": word_count, "doc_id": doc_id}


@app.get("/api/health")
async def health():
    return {"status": "ok", "model": "qwen2.5:3b", "project": "legal-doc-assistant"}
