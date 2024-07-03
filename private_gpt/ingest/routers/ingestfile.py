import os
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from private_gpt.ingest.schemas import IngestFileResponse
from private_gpt.ingest.ingest_service import IngestService
from private_gpt.db.database import get_db
from uuid import UUID


ingest_file_router = APIRouter()

@ingest_file_router.post("/file", response_model=IngestFileResponse)
async def ingest_file(
    file: UploadFile = File(...),  # The uploaded file
    knowledge_base_id: Optional[str] = Form(UUID(os.environ['DEFAULT_KNOWLEDGE_BASE'])),  # The knowledge base to ingest the file into
    db: Session = Depends(get_db)  # The database session
):
    """
    Endpoint to ingest a file into the knowledge base.

    Args:
        file (UploadFile): The uploaded file.
        knowledge_base_id (Optional[str]): The knowledge base to ingest the file into. Defaults to the default knowledge base.
        db (Session): The database session.

    Returns:
        IngestFileResponse: The response containing the ingested documents.

    Raises:
        HTTPException: If there is an error while ingesting the file.
    """
    try:
        service = IngestService()  # Create an instance of the ingest service
        if file.filename is None:
            raise HTTPException(400, "No file name provided")  # If no filename is provided, raise an exception
        ingested_documents = service.ingest(  # Ingest the file into the knowledge base
            file.filename, file.file, knowledge_base_id, db
        )
        return IngestFileResponse(  # Return the response containing the ingested documents
            object="list", model="private-gpt", data=ingested_documents
        )
    except Exception as e:
        print(f"Error while ingesting file: {str(e)}")  # Print the error message
        raise HTTPException(500, "Internal server error while ingesting file")  # Raise an exception with an appropriate error message



@ingest_file_router.post("/proxy", response_model=IngestFileResponse)
async def proxy_ingest_file(
    file_name: str,  # The name of the file to be ingested
    file_key: str,  # The key of the file to be ingested
    knowledge_base_id: Optional[str] = Form(UUID(os.environ['DEFAULT_KNOWLEDGE_BASE'])),  # The knowledge base to ingest the file into. Defaults to the default knowledge base.
    db:Session = Depends(get_db)  # The database session
):
    """
    Endpoint to ingest a file into the knowledge base using a proxy.

    Args:
        file_name (str): The name of the file to be ingested.
        file_key (str): The key of the file to be ingested.
        knowledge_base_id (Optional[str]): The knowledge base to ingest the file into. Defaults to the default knowledge base.
        db (Session): The database session.

    Returns:
        IngestFileResponse: The response containing the ingested documents.

    Raises:
        HTTPException: If there is an error while ingesting the file.
    """
    try:
        # Check if file name is provided
        if file_name is None:
            raise HTTPException(400, "No file name provided")
        
        # Create an instance of the ingest service
        service = IngestService()
        
        # Ingest the file using the proxy
        ingested_documents = service.proxy_ingest(file_name, file_key, knowledge_base_id, db)
        
        # Return the response containing the ingested documents
        return IngestFileResponse(object="list", model="private-gpt", data=ingested_documents)
    except ValueError as e:
        # If file name or knowledge base ID is invalid, raise an exception with an appropriate error message
        raise HTTPException(400, str(e))
    except FileNotFoundError as e:
        # If file is not found, raise an exception with an appropriate error message
        raise HTTPException(404, str(e))
    except IOError as e:
        # If there is an IO error, raise an exception with an appropriate error message
        raise HTTPException(500, str(e))
    except Exception as e:
        # If there is any other error, print the error message and raise an exception with an appropriate error message
        print(f"Error while ingesting file: {str(e)}")
        raise HTTPException(500, "Internal server error while ingesting file")

