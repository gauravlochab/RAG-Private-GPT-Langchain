from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from private_gpt import openai_client

personalize_document_router = APIRouter()

class Example(BaseModel):
    """
    Example model for document personalization.

    Attributes:
        document (str): The original document to be personalized.
        target_audience (str): The target audience to whom the document is personalized.
        personalized_document (str): The personalized document.
    """
    document: str
    target_audience: str
    personalized_document: str

class PersonalizeRequest(BaseModel):
    """
    Request model for document personalization.

    Attributes:
        document (str): The original document to be personalized.
        target_audience (str): The target audience to whom the document is personalized.
        examples (Optional[List[Example]]): Optional examples of document personalization.
        model (Optional[str]): The model to be used for personalization. Defaults to "gpt-3.5-turbo".
    """
    document: str
    target_audience: str
    examples: Optional[List[Example]] = None
    model: Optional[str] = "gpt-3.5-turbo"


@personalize_document_router.post("/personalize")
async def personalize_document(request: PersonalizeRequest):
    """
    Personalize the given document based on the target audience.

    Args:
        request (PersonalizeRequest): The request object containing the document (str): The original document to be personalized.,
            target audience (str): The target audience to whom the document is personalized, examples (Optional[List[Example]]): Optional examples of document personalization and model (Optional[str]): The model to be used for personalization. Defaults to "gpt-3.5-turbo".

    Returns:
        dict: A dictionary containing the personalized document.

    Raises:
        HTTPException: If there is an error during the personalization process.
    """
    try:
        # Generate the examples text
        examples_text = ""
        if request.examples:
            examples_text += "Here are some examples of document personalization:\n"
            examples_text += "\n--".join([
                f"Original Document: \"{example.document}\"\n"
                f"Target Audience: \"{example.target_audience}\"\n"
                f"Personalized Document: {example.personalized_document}"
                for example in request.examples
            ])
        
        # Generate the prompt
        prompt = f"""
        You are a document personalization tool.
        Personalize the following document in a tone and style specific to the described target audience.
        Target Audience: {request.target_audience}
        {examples_text}
        Document: \"{request.document}\"
        """
        
        # Call the OpenAI API to get the personalized document
        response = openai_client.chat.completions.create(
            model=request.model,
            messages=[{"role": "user", "content": prompt}]
        )
        personalized_document = response.choices[0].message.content.strip()
        
        # Return the personalized document
        return {"personalized_document": personalized_document}
    
    # If there is an error, raise an HTTPException
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
