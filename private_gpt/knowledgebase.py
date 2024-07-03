from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from private_gpt.db.database import get_db
from sqlalchemy.orm import Session
from private_gpt.db.crud import create_knowledge__base

knowledge_base_router = APIRouter()

class KnowledgeBaseCreate(BaseModel):
    """
    Data model for creating a new knowledge base.

    Attributes:
        name (str): The name of the knowledge base.
        description (str, optional): The description of the knowledge base.
    """
    name: str = Field(..., description="Name of the knowledge base")
    description: Optional[str] = Field(None, description="Description of the knowledge base")


@knowledge_base_router.post("/knowledge_bases")
async def create_knowledge_base(
    knowledge_base: KnowledgeBaseCreate,  # Data model for creating a new knowledge base
    db: Session = Depends(get_db)  # The database session
):  # Return the newly created knowledge base
    """
    Endpoint for creating a new knowledge base.

    Args:
        knowledge_base (KnowledgeBaseCreate): The data model for creating a new knowledge base.

    Returns:
        KnowledgeBase: The newly created knowledge base.
    """
    # Create the knowledge base in the database
    return create_knowledge__base(
        db,  # The database session
        knowledge_base.name,  # The name of the knowledge base
        knowledge_base.description  # The description of the knowledge base
    )
