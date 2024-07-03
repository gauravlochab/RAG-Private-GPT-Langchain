from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class KnowledgeBase(Base):
    __tablename__ = "knowledgebase"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class Document(Base):
    __tablename__ = "document"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledgebase.id"))
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    embedded_at = Column(DateTime)
    is_embedded = Column(Boolean)
    metadata_ = Column(Text)

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

KnowledgeBase.documents = relationship("Document", back_populates="knowledge_base")