from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from private_gpt import openai_client
from enum import Enum
import json

entity_extraction_router = APIRouter()


class FieldType(str, Enum):
    """
    An enumeration of supported field types.
    
    Attributes:
        string (str): Represents a string field.
        boolean (str): Represents a boolean field.
        number (str): Represents a number field.
    """
    string = "string"
    boolean = "boolean"
    number = "number"

class SchemaField(BaseModel):
    """
    Represents a field in the schema for entity extraction.
    
    Attributes:
        required (Optional[bool]): Whether the field is required. Defaults to False.
        type (FieldType): The type of the field. Defaults to FieldType.string.
    """
    required: Optional[bool] = False
    type: FieldType = FieldType.string

class EntityExtractionRequest(BaseModel):
    """
    Represents a request for entity extraction.
    
    Attributes:
        document (str): The document to extract entities from.
        schema (Dict[str, SchemaField]): The schema that defines the entities to extract.
        model (Optional[str]): The model to use for extraction. Defaults to "gpt-3.5-turbo".
    """
    document: str
    schema: Dict[str, SchemaField]
    model: Optional[str] = "gpt-3.5-turbo"


def transform_entities(entities):
    """
    Transform the entities dictionary by converting values to their respective types.

    Args:
        entities (List[Dict[str, Union[str, bool, float]]]): The entities to transform.

    Returns:
        List[Dict[str, Union[str, bool, float]]]: The transformed entities.

    Raises:
        ValueError: If the entity type is not supported or cannot be converted to the specified type.
    """
    for entity in entities:
        entity_type = entity['type']
        value = entity['value']
        
        # Convert string value to string type
        if entity_type == 'string':
            entity['value'] = str(value)
        
        # Convert number value to float or int type
        elif entity_type == 'number':
            try:
                entity['value'] = float(value) if '.' in str(value) else int(value)
            except ValueError:
                raise ValueError(f"Cannot convert {value} to number")
        
        # Convert boolean value to boolean type
        elif entity_type == 'boolean':
            if isinstance(value, str):
                if value.lower() in ['true', '1']:
                    entity['value'] = True
                elif value.lower() in ['false', '0']:
                    entity['value'] = False
                else:
                    raise ValueError(f"Cannot convert {value} to boolean")
            else:
                entity['value'] = bool(value)
        
        # Raise error for unsupported type
        else:
            raise ValueError(f"Unsupported type: {entity_type}")
    
    return entities


@entity_extraction_router.post("/extract")
async def extract_entity(request: EntityExtractionRequest):
    """
    Extract entities from a document based on a provided schema.

    Args:
        request (EntityExtractionRequest): The request object containing the document and schema.

    Returns:
        List[Dict[str, Union[str, bool, float]]]: The extracted entities with their values transformed to their respective types.

    Raises:
        HTTPException: If an error occurs during the extraction process.
    """
    try:
        # Generate a prompt for the chatbot to extract entities
        schema_fields = ", ".join([f"{name}: {field.type} (required: {field.required})" for name, field in request.schema.items()])
        prompt = f"""
        You are an entity extraction tool.
        Extract the following entities from the document based on the provided schema.
        Fields: {schema_fields}
        Document: \"{request.document}\"
        """
        
        # Call the chatbot with the prompt and functions
        response = openai_client.chat.completions.create(
            model=request.model,
            messages=[{"role": "user", "content": prompt}],
            functions=[
                {
                    "name": "extract_entities",
                    "description": "Extracts specified entities from a document",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "entity": {"type": "string"},
                                        "value": {"type": "string"}
                                    },
                                    "required": ["type", "entity", "value"]
                                }
                            }
                        },
                        "required": ["entities"]
                    }
                }
            ],
            function_call="auto"
        )

        # Extract the entities from the response and transform their values to their respective types
        entities = response.choices[0].message.function_call.arguments
        entities_list = json.loads(entities)["entities"]
        return transform_entities(entities_list)
    except Exception as e:
        # Raise an HTTPException with the error details if an error occurs
        raise HTTPException(status_code=500, detail=str(e))
