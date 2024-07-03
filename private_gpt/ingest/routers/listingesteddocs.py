from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from private_gpt.db.database import get_db
from private_gpt.db.crud import list_ingested_docs
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


list_docs_router = APIRouter()


@list_docs_router.get("/list")
async def list_ingested_documents(
    knowledge_base_id: Optional[str] = None,  # Optional knowledge base ID for filtering documents
    db: Session = Depends(get_db)  # Dependency injection for the database session
) -> dict:
    """
    Lists ingested documents in the database.

    Args:
        knowledge_base_id (Optional[str], optional): The ID of the knowledge base to filter documents by. Defaults to None.
        db (Session, optional): The database session. Defaults to the result of get_db().

    Returns:
        dict: A dictionary with the following keys:
            - "object" (dict): An empty dictionary.
            - "model" (dict): An empty dictionary.
            - "data" (list): A list of ingested documents.

    Raises:
        HTTPException: If no documents are found or an error occurs while listing the documents.
    """
    try:
        # Get the list of ingested documents from the database
        docs = list_ingested_docs(db, knowledge_base_id)

        # If no documents are found, raise an exception
        if not docs:
            raise HTTPException(status_code=404, detail="Documents not found")

        # Create the response dictionary
        response = {
            "object": {},  # An empty object
            "model": {},  # An empty model
            "data": docs  # The list of ingested documents
        }

        return response

    except SQLAlchemyError as e:
        # If an SQLAlchemyError occurs, rollback the database session and raise an HTTPException
        print(f"Error occurred while listing ingested documents: {e}")
        db.rollback()
        raise HTTPException(500, "Internal server error occurred while listing ingested documents")

    except Exception as e:
        # If an unexpected error occurs, raise an HTTPException
        print(f"Unexpected error occurred while listing ingested documents: {e}")
        raise HTTPException(500, "Unexpected error occurred while listing ingested documents")
