from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from private_gpt import openai_client
from enum import Enum

doc_summary_router = APIRouter()


class LengthEnum(str, Enum):
    """
    Enum class representing the length of a summary.

    Attributes:
        short (str): Short summary.
        medium (str): Medium length summary.
        long (str): Long summary.
    """
    short = "short"
    medium = "medium"
    long = "long"

class Example(BaseModel):
    """
    Example model for document summarization.

    Attributes:
        document (str): The original document to be summarized.
        summary (str): The summary of the document.
    """
    document: str
    summary: str

class SummaryRequest(BaseModel):
    """
    Request model for document summarization.

    Attributes:
        document (str): The original document to be summarized.
        examples (Optional[List[Example]]): Optional examples of document summarization.
        length (LengthEnum): The length of the summary. Defaults to "short".
        model (Optional[str]): The model to be used for summarization. Defaults to "gpt-3.5-turbo".
    """
    document: str
    examples: Optional[List[Example]] = None
    length: LengthEnum = LengthEnum.short  # Default to "short"
    model: Optional[str] = "gpt-3.5-turbo"

@doc_summary_router.post("/summarize")
async def summarize_document(request: SummaryRequest):
    """
    Summarize the given document based on the request parameters.

    Args:
        request (SummaryRequest): The request object containing the document (str): The original document to be summarized, examples (Optional[List[Example]]): Optional examples of document summarization, length (LengthEnum): The length of the summary. Defaults to "short", model (Optional[str]): The model to be used for summarization. Defaults to "gpt-3.5-turbo".

    Returns:
        dict: A dictionary containing the summarized document.

    Raises:
        HTTPException: If there is an error during the summarization process.
    """
    try:
        # Generate the examples text
        examples_text = ""
        if request.examples:
            examples_text += "Here are some examples of Document Summarization:"
            examples_text += "\n".join([f"Document: \"{example.document}\"\nSummary: {example.summary}" for example in request.examples])
        
        # Generate the prompt
        prompt = f"""
        You are a document summarization tool.
        Summarize the following document in a {request.length} summary.
        {examples_text}
        Document: \"{request.document}\"
        """
        
        # Call the OpenAI API to get the summary
        response = openai_client.chat.completions.create(
            model=request.model,
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.choices[0].message.content.strip()
        
        # Return the summary
        return {"summary": summary}
    
    # If there is an error, raise an HTTPException
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
