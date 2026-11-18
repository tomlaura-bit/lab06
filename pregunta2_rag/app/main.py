from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db, initialize_database
from .generate import generate_answer
from .ingest import ingest_pdf
from .models import Chunk, Document
from .retrieve import search
from .schemas import AskIn, AskOut, DocumentOut, Passage


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="RAG documental para transporte", lifespan=lifespan)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "provider": settings.generator_provider}


@app.get("/api/documents", response_model=list[DocumentOut])
def documents(db: Session = Depends(get_db)):
    rows = db.execute(select(Document, func.count(Chunk.id)).outerjoin(Chunk).group_by(Document.id).order_by(Document.id)).all()
    return [DocumentOut.model_validate(doc).model_copy(update={"chunk_count": count}) for doc, count in rows]


@app.post("/api/ingest", response_model=DocumentOut)
async def ingest(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(415, "El archivo debe ser PDF")
    data = await file.read()
    current_pages = db.scalar(select(func.coalesce(func.sum(Document.page_count), 0))) or 0
    try:
        result = ingest_pdf(db, file.filename, data)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(422, f"No se pudo procesar el PDF: {exc}")
    if not result.skipped and current_pages + result.document.page_count > settings.max_total_pages:
        db.delete(result.document)
        db.commit()
        raise HTTPException(422, f"El total excedería {settings.max_total_pages} páginas")
    return DocumentOut.model_validate(result.document).model_copy(update={"chunk_count": result.chunks})


@app.post("/api/ask", response_model=AskOut)
def ask(body: AskIn, db: Session = Depends(get_db)):
    hits = search(db, body.question, body.top_k or settings.top_k, body.document_id)
    try:
        answer, provider = generate_answer(body.question, hits)
    except Exception as exc:
        citations = " ".join(f"[{h.document}, p. {h.page}]" for h in hits)
        answer = f"El modelo generativo no está disponible ({exc}). Evidencia recuperada: {citations}"
        provider = "recuperacion_con_error_de_generacion"
    passages = [Passage(document=h.document, page=h.page, content=h.content, score=round(h.score, 4)) for h in hits]
    return AskOut(answer=answer, passages=passages, provider=provider)
