# chat_completions_service.py
import os
import json
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from private_gpt.chunks.chunks_service import search_documents
from private_gpt.chat.schemas import Message
from typing import List, Dict

openai_api_key = os.getenv("OPENAI_API_KEY")
def create_chat_model(request):
    temperature = request.get('temperature', 0)  # Default to 0 if no temperature provided
    streaming = request.get('stream', True) # Default to 0 if no temperature provided
    model = request.get('model', 'gpt-3.5-turbo')  # Default to 'gpt-3.5-turbo' if no model provided
    streaming = request.get('streaming', True)
    max_tokens = request.get('max_tokens', 100)  # Default to True if no streaming provided

    if os.environ.get("SCALEGEN_BASE_URL"):
        chat_model = ChatOpenAI(streaming=streaming,
            callbacks=[StreamingStdOutCallbackHandler()],
            openai_api_key=openai_api_key,
            openai_api_base=os.environ.get("SCALEGEN_BASE_URL"),
            temperature=temperature,
            model=model,
            max_tokens= max_tokens
        )
    else:
        chat_model = ChatOpenAI(streaming=streaming,
            callbacks=[StreamingStdOutCallbackHandler()],
            openai_api_key=openai_api_key,
            temperature=temperature,
            model=model,
            max_tokens= max_tokens
        )

    return chat_model

def generate_messages(messages_data: List[Dict[str, str]]) -> List[Message]:
    # Map role to message class
    role_to_class = {
        "system": SystemMessage,
        "user": HumanMessage,
        "assistant": AIMessage
    }
    
    messages = []
    for message_data in messages_data:
        role = message_data.get("role", "user")  # Default to 'user' if no role provided
        content = message_data["content"]

        # Check if role is valid
        if role not in role_to_class:
            raise ValueError(f"Invalid role: {role}. Valid roles are 'system', 'user', 'assistant'.")

        # Get the message class for the role
        MessageClass = role_to_class[role]

        # Create a message and add it to the list
        messages.append(MessageClass(content=content))

    return messages
def augment_prompt(query: str, response: str) -> str:
    data = json.loads(response)
    source_knowledge = "\n".join([item['text'] for item in data['data']])
    augmented_prompt = f"""Using the contexts below, answer the query.

    Contexts:
    {source_knowledge}

    Query: {query}"""
    return augmented_prompt

async def chat_and_augment(messages: List[Message], request):
    if "HumanMessage" not in str(type(messages[-1])):
        raise ValueError("Last message should be user message")
    last_user_message = messages[-1].content
    request['text'] = request['messages'][-1]['content']
    retrieval_input_str = json.dumps(request)
    search_response = search_documents(retrieval_input_str) 
    augmented_prompt = last_user_message
    if request['use_context']:
        augmented_prompt = augment_prompt(augmented_prompt, search_response)

    messages.append(HumanMessage(content=augmented_prompt))
    chat_model = create_chat_model(request)
    chat_response = await chat_model.agenerate([messages])
    
    return chat_response,search_response

# Remember to define or import `search_documents` function.

async def chat_and_augment_stream(messages: List[Message], request):
    if "HumanMessage" not in str(type(messages[-1])):
        raise ValueError("Last message should be user message")

    last_user_message = messages[-1].content
    request['text'] = request['messages'][-1]['content']
    retrieval_input_str = json.dumps(request)
    search_response = search_documents(retrieval_input_str)
    augmented_prompt = last_user_message
    if request['use_context']:
        augmented_prompt = augment_prompt(augmented_prompt, search_response)

    messages.append(HumanMessage(content=augmented_prompt))
    chat_model = create_chat_model(request)

    async for chunk in chat_model._astream(messages):  # Use async for loop here
        yield chunk, search_response