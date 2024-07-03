from fastapi import APIRouter, Depends, HTTPException
from private_gpt.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from private_gpt.db.crud import delete_ingested_doc

delete_docs_router = APIRouter()

@delete_docs_router.delete("/{doc_id}", response_model=dict)
async def delete_ingested_document(doc_id: str, db: Session = Depends(get_db)):
    """
    Delete an ingested document by its ID.

    Args:
        doc_id (str): The ID of the document to be deleted.

    Returns:
        dict: An empty dictionary.

    Raises:
        HTTPException: If an error occurs while deleting the document.
    """
    try:
        delete_ingested_doc(db, doc_id)
        return {"success":"Document deleted successfully"}
    except SQLAlchemyError as e:
        # If an SQLAlchemyError occurs, rollback the database session and raise an HTTPException
        print(f"Error occurred while deleting ingested document: {e}")
        db.rollback()
        raise HTTPException(500, "Internal server error occurred while deleting ingested document")
    except ValueError as e:
        # If the document ID is invalid, raise an HTTPException with an appropriate error message
        raise HTTPException(400, str(e))
    except Exception as e:
        # If any other error occurs, print the error message and raise an HTTPException with an appropriate error message
        print(f"Unexpected error occurred while deleting ingested document: {e}")
        raise HTTPException(500, "Unexpected error occurred while deleting ingested document")


