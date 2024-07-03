from qdrant_client import QdrantClient,models
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from langchain_community.embeddings import HuggingFaceHubEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_community.document_transformers import LongContextReorder
from typing import List, Dict
from private_gpt.chunks.schemas import Document
from langchain_community.retrievers import QdrantSparseVectorRetriever
from langchain_community.vectorstores.pgvector import PGVector
from langchain.retrievers import  EnsembleRetriever
import json, psycopg2, os
from qdrant_client.http.models import Filter, FieldCondition

# Constants
EMBEDDINGS_URL = "EMBEDDINGS_URL"
SPLADE_EMBEDDINGS_URL = "SPLADE_EMBEDDINGS_URL"
EXTRA_RETRIVED = "EXTRA_RETRIVED"

# Environment Variables
QDRANT_SERVER = os.getenv("QDRANT_SERVER")
PG_VECTOR_SERVER = os.getenv("CONNECTION_STRING")
if not QDRANT_SERVER:
    raise ValueError("QDRANT_SERVER environment variable is not set")
client = QdrantClient(url=QDRANT_SERVER,port=None)
EMBEDDINGS_MODEL = os.getenv(EMBEDDINGS_URL)
if not EMBEDDINGS_MODEL:
    raise ValueError(f"{EMBEDDINGS_URL} environment variable is not set")

SPLADE_EMBEDDING = os.getenv(SPLADE_EMBEDDINGS_URL)
if not SPLADE_EMBEDDING:
    raise ValueError(f"{SPLADE_EMBEDDINGS_URL} environment variable is not set")

if not os.environ.get('EMBEDDINGS_API_KEY') or not os.environ.get('SPLADE_EMBEDDINGS_API_KEY'):
    EMBEDDINGS_MODEL = HuggingFaceHubEmbeddings(model=os.environ['EMBEDDINGS_URL'])
    SPLADE_EMBEDDING = HuggingFaceHubEmbeddings(model=os.environ['SPLADE_EMBEDDINGS_URL'])
else:
    EMBEDDINGS_MODEL = HuggingFaceHubEmbeddings(model=os.environ['EMBEDDINGS_URL'], huggingfacehub_api_token=os.environ['EMBEDDINGS_API_KEY'])
    SPLADE_EMBEDDING = HuggingFaceHubEmbeddings(model=os.environ['SPLADE_EMBEDDINGS_URL'], huggingfacehub_api_token=os.environ['SPLADE_EMBEDDINGS_API_KEY'])

REORDER_TOOL = LongContextReorder()

extra_retrived = os.getenv(EXTRA_RETRIVED, 0)
if not extra_retrived.isdigit():
    raise ValueError(f"{EXTRA_RETRIVED} environment variable should be an integer")

extra_retrived = int(extra_retrived)


def get_splade_values(val: str):
    data_dict=SPLADE_EMBEDDING.embed_documents([val])
    embedding_arr=data_dict[0]
    indexes=[i['index'] for i in embedding_arr]
    values=[i['value'] for i in embedding_arr]

    return indexes,values


def fetch_from_pg_vector(knowledge_base_id, doc_id, chunk_num, chunk_num_range):
    conn = psycopg2.connect(PG_VECTOR_SERVER)
    cur = conn.cursor()

    query = f"""
    SELECT uuid FROM langchain_pg_collection WHERE name = '{knowledge_base_id}'
    """

    cur.execute(query)
    uuid = cur.fetchone()[0]

    query = f"""
        SELECT DISTINCT ON (cmetadata->>'chunk_num') document, cmetadata
        FROM langchain_pg_embedding
        WHERE collection_id = '{uuid}'
          AND cmetadata->>'doc_id' = '{doc_id}'
          AND (cmetadata->>'chunk_num')::int >= {chunk_num_range[0]}
          AND (cmetadata->>'chunk_num')::int <= {chunk_num_range[1]}
          AND (cmetadata->>'chunk_num')::int != {chunk_num}
        ORDER BY cmetadata->>'chunk_num', (cmetadata->>'chunk_num')::int;
    """
    
    cur.execute(query)
    results = cur.fetchall()

    cur.close()
    conn.close()

    return results



def get_retrivers(doc_ids, limit, knowledge_base_id, min_score, retriever_type):
    # Create filter condition for the document IDs
    qdrant_filter = Filter(
        should=[
            FieldCondition(
                key="metadata.doc_id",  # Field name where document ID is stored
                match=MatchValue(
                    value=doc_id  # Single ID to match
                )
            ) for doc_id in doc_ids
        ]
    ) if doc_ids else None
    pg_vector_filter = {"doc_id":{"in":doc_ids}}
    sparse_retriever = QdrantSparseVectorRetriever(
        client=client,
        collection_name=knowledge_base_id+'_sparse',
        sparse_vector_name='sparse_vector',
        sparse_encoder=get_splade_values,
        k=limit+extra_retrived,
        filter=qdrant_filter,
        search_options={'score_threshold':min_score}
    )
    Qdrant_Vector_Store = Qdrant(
        client=client,
        collection_name=knowledge_base_id,
        embeddings=EMBEDDINGS_MODEL,
    )
    Pg_Vector_Store = PGVector(
        connection_string=PG_VECTOR_SERVER,
        embedding_function=EMBEDDINGS_MODEL,
        collection_name=knowledge_base_id
        )
    pg_vector_dense_retriever = Pg_Vector_Store.as_retriever(search_kwargs={"filter": pg_vector_filter, "k":10+extra_retrived,"score_threshold":min_score})
    qdrant_dense_retriever = Qdrant_Vector_Store.as_retriever(k=10+extra_retrived,search_kwargs={"filter": qdrant_filter,"score_threshold":min_score})

    qdrant_ensemble_retriever = EnsembleRetriever(
        retrievers=[sparse_retriever, qdrant_dense_retriever], weights=[0.5, 0.5],k=limit+extra_retrived
    )
    pg_vector_ensemble_retriever = EnsembleRetriever(
        retrievers=[sparse_retriever, pg_vector_dense_retriever], weights=[0.5, 0.5],k=limit+extra_retrived
    )

    if retriever_type == 'dense':
        return qdrant_dense_retriever, pg_vector_dense_retriever
    elif retriever_type == 'sparse':
        return sparse_retriever, "_"
    elif retriever_type == 'ensemble':
        return qdrant_ensemble_retriever, pg_vector_ensemble_retriever
    else:
        raise ValueError(f"Invalid retriever type: {retriever_type}. Expected 'dense', 'sparse', or 'ensemble'.")
    


def get_surrounding_chunks_json(chunks: Dict, target_chunk_number: int, number_of_chunks: int) -> Dict:
    previous_chunks = []
    next_chunks = []

    try:
        # Gathering previous chunks
        for i in range(target_chunk_number - number_of_chunks, target_chunk_number):
            if i in chunks:
                previous_chunks.append(chunks[i])

        # Gathering next chunks
        for i in range(target_chunk_number + 1, target_chunk_number + number_of_chunks+1):
            if i in chunks:
                next_chunks.append(chunks[i])
    except Exception as e:
        print(f"Error occurred while gathering chunks: {e}")
        previous_chunks = []
        next_chunks = []

    result = {
        'previous_chunks': previous_chunks,
        'next_chunks': next_chunks
    }

    return result


def extract_relevant_chunks(prev_next_chunks_list: List, chunk_num: int, prev_next_chunks: int) -> Dict:  
    if prev_next_chunks_list:
        relevant_chunks = [record for record in prev_next_chunks_list if chunk_num - int(prev_next_chunks) <= record['metadata']['chunk_num'] <= chunk_num + int(prev_next_chunks)]
        # Extract page_content from these chunks
        extracted_contents = {record['metadata']['chunk_num']: record['page_content'] for record in relevant_chunks}
    else:
        extracted_contents = {}
    return extracted_contents



def get_surrounding_chunks_content(document: Document, prev_next_chunks: int, knowledge_base_id: str, db: str) -> Dict:
    # Sort the results by chunk_num
    doc_id = document.metadata['doc_id']
    chunk_num = document.metadata['chunk_num']
    # Define the range to include previous and next chunks
    chunk_num_range = [chunk_num - int(prev_next_chunks), chunk_num + int(prev_next_chunks)]

    # Retrieve adjacent chunks
    if db == "qdrant":
        prev_next_chunks_list = client.scroll(
            collection_name=knowledge_base_id,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.doc_id",
                        match=models.MatchValue(value=doc_id),
                    ),
                    models.FieldCondition(
                        key="metadata.chunk_num",
                        range=models.Range(gte=chunk_num_range[0], lte=chunk_num_range[1]),
                    ),
                ],
                must_not=[
                    models.FieldCondition(
                        key="metadata.chunk_num",
                        match=models.MatchValue(value=chunk_num),
                    )
                ]
            ),
        )
        prev_next_chunks_list = [i.payload for i in prev_next_chunks_list[0]]
    else:
        res = fetch_from_pg_vector(knowledge_base_id, doc_id, chunk_num, chunk_num_range)
        prev_next_chunks_list = []
        for i in range(len(res)):
            prev_next_chunks_list.append({"page_content" : res[i][0], "metadata" : res[i][1]})
    
    extracted_contents = extract_relevant_chunks(prev_next_chunks_list, chunk_num, prev_next_chunks)
    surrounding_chunks_json = get_surrounding_chunks_json(extracted_contents, chunk_num, prev_next_chunks)
    return surrounding_chunks_json


def search_documents(json_input: str) -> str:
    # Parse the JSON input
    input_dict = json.loads(json_input)

    # Extract the parameters from the input
    text = input_dict['text']
    knowledge_base_id = input_dict.get('knowledge_base_id')
    doc_ids = input_dict.get('context_filter', {}).get('doc_ids')
    limit = input_dict.get('limit', 10)
    prev_next_chunks = input_dict.get('prev_next_chunks', 2)
    min_score = input_dict.get('min_score', 0.0)
    retriever_type = input_dict.get('retriever_type', 'ensemble')
    
    main_retriever, fall_back_retriever = get_retrivers(doc_ids,limit,knowledge_base_id,min_score,retriever_type)
    try:
        retrived_docs = main_retriever.get_relevant_documents(text)
        reordered_docs = REORDER_TOOL.transform_documents(retrived_docs)
        reordered_docs = reordered_docs[:int(limit)]
        db = "qdrant"
    except:
        retrived_docs = fall_back_retriever.get_relevant_documents(text)
        reordered_docs = REORDER_TOOL.transform_documents(retrived_docs)
        reordered_docs = reordered_docs[:int(limit)]
        db = "pg_vector"

    data = []
    for result in reordered_docs:
        surrounding_content = get_surrounding_chunks_content(result,prev_next_chunks,knowledge_base_id,db)
        data.append({
                "object": {},
                "document": {
                    "object": {},
                    "doc_id": result.metadata['doc_id'],
                    "doc_metadata": result.metadata
                },
                "text": str(result.page_content),
                "previous_texts": surrounding_content['previous_chunks'],
                "next_texts": surrounding_content['next_chunks']
            })

    # Create the JSON response
    response_dict = {
        "object": {},
        "model": {},
        "data": data
    }
    # Convert the response to a JSON string
    json_response = json.dumps(response_dict)
    return json_response
