from pydantic import BaseModel, Field
from typing import Any, Literal, Optional, Dict,List
from langchain_core.documents import Document
from pydantic import BaseModel, Field

class IngestedDoc(BaseModel):
    doc_id: str = Field(examples=["c202d5e6-7b69-4869-81cc-dd574ee8ee11"])
    knowledge_base_id: str = Field(examples=["c202d5e6-7b69-4869-81cc-dd574ee8ee11"])
    doc_metadata: Optional[Dict[str, Any]] = Field(default=None,
        examples=[
            {
                "page_label": "2",
                "file_name": "Sales Report Q3 2023.pdf",
            }
        ]
    )

    @staticmethod
    # def from_document(document: Document, doc_id: str, knowledge_base_id: str) -> "IngestedDoc":
    def from_document(doc_id: str, knowledge_base_id: str) -> "IngestedDoc":
        return IngestedDoc(
            doc_id=doc_id,
            knowledge_base_id=knowledge_base_id,
            # doc_metadata=document['metadata'],
        )

class IngestFileResponse(BaseModel):
    object: Literal["list"]
    model: Literal["private-gpt"]
    data: List[IngestedDoc]