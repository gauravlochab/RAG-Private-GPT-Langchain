from fastapi import APIRouter, HTTPException
from private_gpt.chunks.schemas import ContextChunksRequest, ContextChunksResponse
from private_gpt.chunks.chunks_service import search_documents
import json

context_chunk_retrieval_router = APIRouter()

@context_chunk_retrieval_router.post("/chunks", response_model=ContextChunksResponse)
async def context_chunks_retrieval(request: ContextChunksRequest):
    """
    Endpoint for retrieving context chunks based on the provided request.

    Args:
        request (ContextChunksRequest): The request object containing the necessary parameters.

    Returns:
        ContextChunksResponse: The response object containing the retrieved context chunks.

    Raises:
        HTTPException: If an error occurs during the retrieval process.
    """
    try:
        # Convert the request to JSON
        json_input = request.json()

        # Call the search_documents function
        response = search_documents(json_input)
        
        # Convert the response from JSON
        response_dict = json.loads(response)

        return response_dict
    except Exception as e:
        # Raise an HTTPException with a 500 status code and the error detail
        raise HTTPException(status_code=500, detail=str(e))
