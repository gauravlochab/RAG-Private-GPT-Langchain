from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .models import Document, KnowledgeBase
from datetime import datetime
import uuid
from typing import Optional


def create_document(db: Session, file_name: str, doc_id: str, knowledge_base_id: str, cloud_type: str):
    document = Document(
        id=doc_id,
        knowledge_base_id=knowledge_base_id,
        file_name=file_name,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        is_embedded=False,
        metadata_=cloud_type
    )
    try:
        db.add(document)
        db.commit()
        db.refresh(document)
    except IntegrityError as e:
        print("Document already exists")
        db.rollback()
    except SQLAlchemyError as e:
        print(f"Error occurred while creating document: {e}")
        db.rollback()


def embed_document(db: Session, doc_id: str):
    document = db.query(Document).filter(Document.id == doc_id).first()
    if document:
        try:
            document.embedded_at = datetime.now()
            document.updated_at = datetime.now()
            document.is_embedded = True
            db.commit()
            db.refresh(document)
        except SQLAlchemyError as e:
            print(f"Error occurred while embedding document: {e}")
            db.rollback()
            return None
    else:
        print("Document not found")
        return None


def create_knowledge__base(db: Session, name: str, description: str):
    try:
        knowledge_base = KnowledgeBase(
            id=uuid.uuid4(),
            name=name,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(knowledge_base)
        db.commit()
        db.refresh(knowledge_base)
        return knowledge_base
    except IntegrityError as e:
        print(f"Error occurred while creating knowledge base: {e}")
        db.rollback()
        return None
    except SQLAlchemyError as e:
        print(f"Error occurred while creating knowledge base: {e}")
        db.rollback()
        return None


def list_ingested_docs(db: Session, knowledge_base_id: Optional[str] = None):
    try:
        query = db.query(Document)
        if knowledge_base_id:
            query = query.filter(Document.knowledge_base_id == knowledge_base_id)
        documents = query.all()
        return documents
    except SQLAlchemyError as e:
        print(f"Error occurred while listing ingested documents: {e}")
        db.rollback()
        return []


def delete_ingested_doc(db: Session, doc_id: str):
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            db.delete(document)
            db.commit()
            return True
        else:
            print("Document not found")
            return False
    except SQLAlchemyError as e:
        print(f"Error occurred while deleting ingested document: {e}")
        db.rollback()
        return False
