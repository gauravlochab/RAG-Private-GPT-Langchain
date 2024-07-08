from fastapi import FastAPI, APIRouter
import sentry_sdk, uvicorn
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from fastapi.middleware.cors import CORSMiddleware
import private_gpt
import os 


sentry_sdk.init(
    dsn="your_dns_link",
    traces_sample_rate=1.0,
)

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/", status_code=200)
def hello_world():
    return "Server is running!"

@app.get("/health")
def health_check():
    return {"status": "UP"}

@app.get("/version")
def get_version():
    return "v1"

root_router = APIRouter(prefix="/v1")
ingest_router = APIRouter(prefix="/ingest", tags=["ingest"])
ingest_router.include_router(private_gpt.ingest.routers.ingestfile.ingest_file_router)
ingest_router.include_router(private_gpt.ingest.routers.listingesteddocs.list_docs_router)
ingest_router.include_router(private_gpt.ingest.routers.deleteingesteddocs.delete_docs_router)
ingest_router.include_router(private_gpt.ingest.routers.embedded.mark_embedded_router)
root_router.include_router(ingest_router)
root_router.include_router(private_gpt.knowledgebase.knowledge_base_router, tags=["knowledgebase"])
root_router.include_router(private_gpt.set_openai_url.openai_base_url_router, tags=["set-openai-url"])
root_router.include_router(private_gpt.chat.chat_completion_router.chat_completion_router, tags=["chat-completion"])
root_router.include_router(private_gpt.chunks.chunks_router.context_chunk_retrieval_router, tags=["chunk-retrieval"])
blocks_router = APIRouter(prefix="/blocks", tags=["blocks"])
blocks_router.include_router(private_gpt.blocks.document_summary.doc_summary_router)
blocks_router.include_router(private_gpt.blocks.sentiment_analysis.sentiment_analysis_router)
blocks_router.include_router(private_gpt.blocks.document_personalization.personalize_document_router)
blocks_router.include_router(private_gpt.blocks.entity_extraction.entity_extraction_router)
root_router.include_router(blocks_router)

app.include_router(root_router)

app = SentryAsgiMiddleware(app)

