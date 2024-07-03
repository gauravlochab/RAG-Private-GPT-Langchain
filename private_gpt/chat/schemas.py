from pydantic import BaseModel, Field, Extra
from typing import List, Optional, Dict ,Any

class Message(BaseModel):
    role: Optional[str]
    content: str

class ContextFilter(BaseModel):
    doc_ids: Optional[List[str]]

class RequestModel(BaseModel):
    messages: List[Message]
    stream: bool
    knowledge_base_id: Optional[str]
    use_context: Optional[bool]
    context_filter: Optional[ContextFilter]
    include_sources: Optional[bool]
    max_tokens: Optional[int]
    temperature: Optional[float]
    limit: Optional[float]

class DocumentMetadata(BaseModel):
    class Config:
        extra = Extra.allow  # Allow additional properties

class Document(BaseModel):
    object: Optional[Dict[str, Any]]  # Assuming this is a generic dict
    doc_id: str
    doc_metadata: DocumentMetadata

class Source(BaseModel):
    object: Optional[Dict[str, Any]]  # Generic dict for the 'object'
    score: float
    document: Document
    text: str
    previous_texts: Optional[List[str]]
    next_texts: Optional[List[str]]

# class Delta(BaseModel):
#     content: Optional[str]

class Choice(BaseModel):
    finish_reason: Optional[str]
    delta: Optional[str]
    message: Optional[Message]
    sources: Optional[List[Source]]

class Model(BaseModel):
    class Config:
        extra = Extra.allow  # Allow additional properties

class ResponseSchema(BaseModel):
    id: str
    created: str  # Assuming this should be an integer
    model: Model
    choices: List[Choice]
