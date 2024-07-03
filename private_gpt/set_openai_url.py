from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

openai_base_url_router = APIRouter()

class URLItem(BaseModel):
    """
    A Pydantic model for a URLItem.

    Attributes:
        url (str): The URL string.
    """
    url: str

@openai_base_url_router.post("/set-openai-base-url")
async def set_url(item: URLItem):
    """
    Set the OpenAI base URL.

    Args:
        item (URLItem): The URLItem object containing the base URL.

    Returns:
        dict: A message indicating the success of setting the base URL.

    Raises:
        HTTPException: If there is an error setting the base URL.
    """
    try:
        # Set the OpenAI base URL environment variable
        os.environ["SCALEGEN_BASE_URL"] = item.url

        # Return a success message
        return {"message": "Openai Base URL set successfully"}
    except Exception as e:
        # Raise an HTTPException if there is an error setting the base URL
        raise HTTPException(status_code=500, detail=str(e))
