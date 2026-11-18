import hashlib
import io
import re
from dataclasses import dataclass
from pypdf import PdfReader
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .config import settings
from .embedding import encode
from .models import Chunk, Document


@dataclass
class IngestResult:
    document: Document
    chunks: int
    skipped: bool


def split_text(text: str, size: int, overlap: int) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    result, start = [], 0
    while start < len(clean):
        end = min(start + size, len(clean))
        if end < len(clean):
            boundary = clean.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        result.append(clean[start:end].strip())
        if end >= len(clean):
            break
        start = max(end - overlap, start + 1)
    return result


def ingest_pdf(db: Session, filename: str, data: bytes) -> IngestResult:
    digest = hashlib.sha256(data).hexdigest()
    existing = db.scalar(select(Document).where(Document.sha256 == digest))
    if existing:
        count = db.scalar(select(func.count(Chunk.id)).where(Chunk.document_id == existing.id)) or 0
        return IngestResult(existing, count, True)

    reader = PdfReader(io.BytesIO(data), strict=False)
    if len(reader.pages) > settings.max_pdf_pages:
        raise ValueError(f"{filename} tiene {len(reader.pages)} páginas; el máximo por archivo es {settings.max_pdf_pages}")

    doc = Document(filename=filename, sha256=digest, page_count=len(reader.pages), blank_pages=0, read_errors=0)
    db.add(doc)
    db.flush()
    pending: list[tuple[int, int, str]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            doc.read_errors += 1
            continue
        pieces = split_text(text, settings.chunk_size, settings.chunk_overlap)
        if not pieces:
            doc.blank_pages += 1
            continue
        pending.extend((page_number, index, piece) for index, piece in enumerate(pieces))

    for offset in range(0, len(pending), 64):
        batch = pending[offset:offset + 64]
        vectors = encode([item[2] for item in batch])
        for (page, index, content), vector in zip(batch, vectors):
            db.add(Chunk(document_id=doc.id, page_number=page, chunk_index=index, content=content, embedding=vector))
    db.commit()
    db.refresh(doc)
    return IngestResult(doc, len(pending), False)
