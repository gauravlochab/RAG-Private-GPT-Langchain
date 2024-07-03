from fastapi import APIRouter, HTTPException, Depends, Body
from private_gpt.db.database import get_db
from private_gpt.db.crud import embed_document
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from pydantic import BaseModel


class EmbeddedDocumentRequest(BaseModel):
    """
    A model for a request to embed a document.

    Attributes:
        status (str): The status of the embedding process.
        id (str): The id of the document.
        chunk_ids (List[str]): The ids of the chunks of the document.
    """
    status: str
    id: str
    chunk_ids: List[str]


mark_embedded_router = APIRouter()


@mark_embedded_router.post("/embedded")
async def list_ingested_documents(
    request: EmbeddedDocumentRequest = Body(...), 
    db: Session = Depends(get_db)
):
    """
    List ingested documents in the database and embed them.

    Args:
        request (EmbeddedDocumentRequest): The request object containing the necessary parameters.
        db (Session, optional): The database session. Defaults to the result of get_db().

    Returns:
        dict: A dictionary with the following keys:
            - id (str): The id of the document.
            - status (str): The status of the embedding process.
            - chunk_ids (List[str]): The ids of the chunks of the document.

    Raises:
        HTTPException: If an error occurs while embedding the document.
    """
    try:
        embed_document(db, request.id)
        response = {
            "id": request.id, 
            "status": request.status, 
            "chunk_ids": request.chunk_ids
        }
        return response
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        elif isinstance(e, SQLAlchemyError):
            raise HTTPException(status_code=500, detail="Error occurred while accessing the database")
        elif isinstance(e, KeyError) and "id" in str(e):
            raise HTTPException(status_code=400, detail="Missing id field in the request")
        else:
            raise HTTPException(status_code=500, detail="An unexpected error occurred")
