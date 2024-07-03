from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from private_gpt.chat.schemas import RequestModel
from private_gpt.chat.chat_completion_service import (
    chat_and_augment,
    generate_messages,
    chat_and_augment_stream
)
import json
from datetime import datetime

chat_completion_router = APIRouter()

@chat_completion_router.post("/chat_completions")
async def process_request(request: RequestModel):
    """
    Endpoint for processing chat completion requests.

    Args:
        request (RequestModel): The request model containing the chat messages and other parameters.

    Returns:
        dict or StreamingResponse: The response dictionary or streaming response based on the request parameters.

    Raises:
        HTTPException: If an error occurs during the processing of the request.
    """
    # Convert the request model to a dictionary
    input_data = request.dict()
    
    # Generate the messages from the input data
    messages = generate_messages(input_data['messages'])
    
    try:
        if input_data.get('stream', False):
            # Return the streaming response if streaming is enabled
            return await streaming_response(messages, input_data)
        else:
            # Process the chat and augment the messages
            chat_response, search_response = await chat_and_augment(messages, input_data)
            
            # Parse the search response from JSON
            search_response = json.loads(search_response)
            
            # Prepare the response dictionary
            response_dict = {
                "id": str(chat_response.run[0].run_id),  # Set the run ID
                "created": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),  # Set the creation timestamp
                "model": {"name": chat_response.llm_output["model_name"]},  # Set the model name
                "choices": [
                    {
                        "finish_reason": chat_response.generations[0][0].generation_info["finish_reason"],  # Set the finish reason
                        "delta": "null",  # Set the delta to null
                        "message": {
                            "role": "assistant",  # Set the role to assistant
                            "content": chat_response.generations[0][0].text  # Set the message content
                        },
                        "sources": search_response['data']  # Set the sources
                    }
                ]
            }
            
            # Return the response dictionary
            return response_dict
    except Exception as e:
        # Raise an HTTPException if an error occurs
        raise HTTPException(status_code=400, detail=str(e))

async def streaming_response(messages, input_data):
    """
    Generate a streaming response for the chat completion API endpoint.

    Args:
        messages (List[Message]): The list of messages in the chat conversation.
        input_data (dict): The input data for the chat completion.

    Returns:
        StreamingResponse: The streaming response containing the chat completion.
    """
    async def generate():
        """
        Generate the streaming response asynchronously.

        Yields:
            str: The JSON-encoded response dictionary for each chunk of the chat completion.
        """
        async for chunk, search_response in chat_and_augment_stream(messages, input_data):
            # Get the message content from the chunk
            chunk_text = chunk.message
            
            # Parse the search response from JSON
            search_response = json.loads(search_response)
            
            # Prepare the response dictionary
            response_dict = {
                "id": None,  # Set the ID to None (not used in streaming response)
                "created": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),  # Set the creation timestamp
                "model": {"name": 'null'},  # Set the model name to 'null' (not used in streaming response)
                "choices": [
                    {
                        "finish_reason": 'null',  # Set the finish reason to 'null' (not used in streaming response)
                        "delta": {"content": 'null'},  # Set the delta content to 'null' (not used in streaming response)
                        "message": {
                            "role": "assistant",  # Set the role to 'assistant'
                            "content": chunk_text.content  # Set the message content
                        },
                        "sources": search_response['data']  # Set the sources
                    }
                ]
            }
            
            # Yield the JSON-encoded response dictionary for each chunk
            yield json.dumps(response_dict) + '\n\n'
            
    # Return the streaming response
    return StreamingResponse(content=generate(), media_type="text/event-stream")
