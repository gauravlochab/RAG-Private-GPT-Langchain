from dotenv import load_dotenv
from openai import OpenAI

openai_client = OpenAI()
load_dotenv()

from .ingest.routers.ingestfile import ingest_file_router
from .knowledgebase import knowledge_base_router
from .set_openai_url import openai_base_url_router
from .ingest.routers.listingesteddocs import list_docs_router
from .chat.chat_completion_router import chat_completion_router
from .chunks.chunks_router import context_chunk_retrieval_router
from .ingest.routers.deleteingesteddocs import delete_docs_router
from .ingest.routers.embedded import mark_embedded_router
from .blocks.document_summary import doc_summary_router
from .blocks.sentiment_analysis import sentiment_analysis_router
from .blocks.document_personalization import personalize_document_router
from .blocks.entity_extraction import entity_extraction_router

__all__ = [
    "ingest_file_router",
    "knowledge_base_router",
    "openai_base_url_router",
    "list_docs_router",
    "chat_completion_router",
    "context_chunk_retrieval_router",
    "delete_docs_router",
    "mark_embedded_router",
    "doc_summary_router",
    "sentiment_analysis_router",
    "personalize_document_router",
    "entity_extraction_router"]