from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session
from .embedding import encode_one
from .models import Chunk, Document


@dataclass
class Hit:
    document: str
    page: int
    content: str
    score: float


def search(db: Session, question: str, top_k: int, document_id: int | None = None) -> list[Hit]:
    vector = encode_one(question)
    distance = Chunk.embedding.cosine_distance(vector)
    stmt = select(Chunk, Document.filename, distance.label("distance")).join(Document).order_by(distance).limit(top_k)
    if document_id is not None:
        stmt = stmt.where(Chunk.document_id == document_id)
    rows = db.execute(stmt).all()
    return [Hit(filename, chunk.page_number, chunk.content, max(0.0, 1.0 - float(dist))) for chunk, filename, dist in rows]
