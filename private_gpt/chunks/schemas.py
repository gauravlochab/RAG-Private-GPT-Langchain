from pydantic import BaseModel, Field
from typing import Optional, List

class ContextFilter(BaseModel):
    doc_ids: Optional[List[str]] = Field(None)

class ContextChunksRequest(BaseModel):
    text: str
    knowledge_base_id: Optional[str] = Field(None)
    context_filter: Optional[ContextFilter] = Field(None)
    limit: Optional[int] = Field(10)
    prev_next_chunks: Optional[int] = Field(2)
    min_score: Optional[float] = Field(0.0)

class Document(BaseModel):
    object: dict = Field({})
    doc_id: str
    doc_metadata: dict

class Chunk(BaseModel):
    object: dict = Field({})
    # score: float
    document: Document
    text: str
    previous_texts: Optional[List[str]] = Field(None)
    next_texts: Optional[List[str]] = Field(None)

class ContextChunksResponse(BaseModel):
    object: dict = Field({})
    model: dict = Field({})
    data: List[Chunk] = Field([])
