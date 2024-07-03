from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from private_gpt import openai_client


sentiment_analysis_router = APIRouter()


class Example(BaseModel):
    """
    Example model for sentiment analysis.

    Attributes:
        document (str): The original document to be analyzed.
        sentiment (str): The sentiment of the document.
    """
    document: str
    sentiment: str

class TextRequest(BaseModel):
    """
    Request model for sentiment analysis.

    Attributes:
        document (str): The original document to be analyzed.
        examples (Optional[List[Example]]): Optional examples of sentiment analysis.
        model (Optional[str]): The model to be used for analysis. Defaults to "gpt-3.5-turbo".
    """
    document: str
    examples: Optional[List[Example]] = None
    model: Optional[str] = "gpt-3.5-turbo"

@sentiment_analysis_router.post("/analyze-sentiment")
async def analyze_sentiment(request: TextRequest):
    """
    Analyze the sentiment of a given document using OpenAI's GPT-3 model.

    Args:
        request (TextRequest): The request object containing the document
            to be analyzed, and optional examples of sentiment analysis.

    Returns:
        dict: A dictionary containing the sentiment of the document.

    Raises:
        HTTPException: If there is an error during the sentiment analysis
            process.
    """
    try:
        # Generate examples text
        examples_text = ""
        if request.examples:
            examples_text += "Here are some examples of sentiment analysis:"
            examples_text += "\n".join([
                f"Document: \"{example.document}\"\nSentiment: {example.sentiment}"
                for example in request.examples
            ])
        
        # Generate prompt
        prompt = f"""
        You are a sentiment analysis tool.
        Analyze the sentiment of the following text and classify it as positive, negative, or neutral. Return it as a single word answer.
        {examples_text}
        Document: \"{request.document}\"
        """
        
        # Call OpenAI API to get sentiment
        response = openai_client.chat.completions.create(
            model=request.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1,
            temperature=0 
        )
        sentiment = response.choices[0].message.content.strip()
        
        # Return sentiment
        return {"sentiment": sentiment}
    
    # If there is an error, raise an HTTPException
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
