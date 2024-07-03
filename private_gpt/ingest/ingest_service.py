from .schemas import IngestedDoc
from sqlalchemy.orm import Session
from private_gpt.db.crud import create_document, embed_document
import tempfile, os, boto3, uuid
from uuid import UUID
import requests
import json
from typing import BinaryIO,List
from google.cloud import storage
from google.oauth2 import service_account
from azure.storage.blob import BlobServiceClient
import os 


PRIVATE_GPT_BACKEND_URL=os.environ.get('PRIVATE_GPT_BACKEND_URL','')


cloud_type = os.environ.get('CLOUD_TYPE')
STATUS_URL = PRIVATE_GPT_BACKEND_URL + "/v1/ingest/embedded"

INGEST_URL = os.environ.get('INGEST_URL','')
EMBED_URL=INGEST_URL+'/ingest'

class IngestService:

    def ingest(self, file_name: str, raw_file_data: BinaryIO, knowledge_base_id: UUID, db: Session) -> List[IngestedDoc]:
        self.upload_to_cloud(file_name, raw_file_data, cloud_type)
        doc_id = uuid.uuid4()
        create_document(db, file_name, doc_id, knowledge_base_id, cloud_type)
        url = EMBED_URL

        payload = {
            "cloud_type": cloud_type,
            "file_key": file_name,
            "collection_name": str(knowledge_base_id),
            "file_id": str(doc_id),
            "status_url":STATUS_URL
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        print(response.json())
        # documents = response.json()
        # print(documents)
        # embed_document(db, doc_id)
        return [IngestedDoc.from_document(str(doc_id), str(knowledge_base_id))]
        # return [IngestedDoc.from_document(document, str(doc_id), str(knowledge_base_id)) for document in documents]
    

    def proxy_ingest(self,file_name:str,file_key:str,knowledge_base_id:UUID,db:Session):
        doc_id = uuid.uuid4()
        create_document(db, file_name, doc_id, knowledge_base_id, cloud_type)
        url = EMBED_URL
        payload = {
            "cloud_type": cloud_type,
            "file_key": file_key,
            "collection_name": str(knowledge_base_id),
            "file_id": str(doc_id),
            "status_url":STATUS_URL
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        print(response.json())
        return [IngestedDoc.from_document(str(doc_id), str(knowledge_base_id))]
    


    def upload_to_cloud(self, file_name: str, file: BinaryIO, cloud_type: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = f"{temp_dir}/{file_name}"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(file.read())
            if cloud_type == "aws":
                self.upload_file_to_s3(file_path, os.environ.get('AWS_BUCKET_NAME'), file_name)
            elif cloud_type == "gcp":
                self.upload_file_to_gcp(file_path, os.environ.get('GCP_BUCKET_NAME'), file_name)
            elif cloud_type == "azure":
                self.upload_file_to_azure(file_path, os.environ.get('AZURE_CONTAINER_NAME'), file_name)
            else:
                raise ValueError(f"Unsupported cloud type: {cloud_type}")

    def upload_file_to_s3(self, file_path, bucket_name, object_name):
        """
        Upload a file to an S3 bucket
        :param file_path: Path to the file to upload
        :param bucket_name: S3 bucket name
        :param object_name: S3 object name (key)
        :return: True if the file was uploaded successfully, else False
        """
        s3_client = boto3.client('s3')
        try:
            response = s3_client.upload_file(file_path, bucket_name, object_name)
            print("File uploaded successfully")
        except Exception as e:
            print(f"Error uploading file to S3: {e}")


    def upload_file_to_gcp(self, file_path, bucket_name, object_name):
        """
        Upload a file to Google Cloud Storage
        :param file_path: Path to the file to upload
        :param bucket_name: Google Cloud Storage bucket name
        :param object_name: Google Cloud Storage object name (key)
        :return: True if the file was uploaded successfully, else False
        """
        credentials_dict = os.environ.get('GCP_CREDS')
        storage_client = storage.Client(project=credentials_dict['project_id'], credentials=service_account.Credentials.from_service_account_info(credentials_dict))
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)

        try:
            blob.upload_from_filename(file_path)
            print("File uploaded successfully to Google Cloud Storage")
        except Exception as e:
            print(f"Error uploading file to Google Cloud Storage: {e}")


    def upload_file_to_azure(self, file_path, container_name, blob_name):
        """
        Upload a file to Azure Blob Storage
        :param file_path: Path to the file to upload
        :param container_name: Azure Blob Storage container name
        :param blob_name: Azure Blob Storage blob name (key)
        :return: True if the file was uploaded successfully, else False
        """
        connection_string = os.environ.get('AZURE_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container_name, blob_name)

        try:
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data)
            print("File uploaded successfully to Azure Blob Storage")
        except Exception as e:
            print(f"Error uploading file to Azure Blob Storage: {e}")


    # def list_ingested(self) -> list[IngestedDoc]:
    #     ingested_docs: list[IngestedDoc] = []
    #     try:
    #         docstore = self.storage_context.docstore
    #         ref_docs: dict[str, RefDocInfo] | None = docstore.get_all_ref_doc_info()

    #         if not ref_docs:
    #             return ingested_docs

    #         for doc_id, ref_doc_info in ref_docs.items():
    #             doc_metadata = None
    #             if ref_doc_info is not None and ref_doc_info.metadata is not None:
    #                 doc_metadata = IngestedDoc.curate_metadata(ref_doc_info.metadata)
    #             ingested_docs.append(
    #                 IngestedDoc(
    #                     object="ingest.document",
    #                     doc_id=doc_id,
    #                     doc_metadata=doc_metadata,
    #                 )
    #             )
    #     except ValueError:
    #         print("Got an exception when getting list of docs", exc_info=True)
    #         pass
    #     print("Found count=%s ingested documents", len(ingested_docs))
    #     return ingested_docs

    


# class IngestService_wo_cloud():

#     def select_file_loader(file_name: str) -> Any:
#         """Selects the appropriate file loader based on the file extension."""
#         if file_name.endswith('.pdf'):
#             return PDFLoader
#         elif file_name.endswith(('.xlsx', '.xls', '.csv', '.tsv', '.json')):
#             return TabularDataloader
#         else:
#             return FileLoader
    
#     def process_document(self, file_name: str, file_path: Path,knowledge_base_id: str) -> list[Document]:
#         doc_id = uuid.uuid4().hex
#         loader = self.select_file_loader(file_name)(file_path)
#         docs = loader.load()
#         for doc in docs:
#             doc.metadata["filename"] = file_name

#         pg_client = PGVector(connection_string=os.environ['POSTGRES_CONNECTION_STRING'], embedding_function=EMBEDDINGS_MODEL, collection_name=knowledge_base_id)

#         # Split documents into batches of 32
#         batch_size = 100
#         doc_batches = [docs[i:i + batch_size] for i in range(0, len(docs), batch_size)]

#         # Add documents to both vector stores in batches
#         for batch in doc_batches:
#             pg_client.aadd_documents(documents=batch)
#             Qdrant.afrom_documents(batch, EMBEDDINGS_MODEL, url=os.environ['QDRANT_SERVER'], collection_name=knowledge_base_id)

#         return docs, doc_id
    
#     def ingest_bin_data(self, file_name: str, raw_file_data: BinaryIO, knowledge_base_id: UUID) -> list[IngestedDoc]:
#         file_data = raw_file_data.read()
#         return self.ingest_file(file_name, file_data, knowledge_base_id.hex)

#     def ingest_file(self, file_name: str, file_data: AnyStr, knowledge_base_id: str) -> list[IngestedDoc]:
#         with tempfile.NamedTemporaryFile(delete=False) as tmp:
#             try:
#                 path_to_tmp = Path(tmp.name)
#                 if isinstance(file_data, bytes):
#                     path_to_tmp.write_bytes(file_data)
#             finally:
#                 tmp.close()
#         documents, doc_id = self.process_document(file_name, path_to_tmp, knowledge_base_id)
#         path_to_tmp.unlink()
#         return [IngestedDoc.from_document(document, doc_id, knowledge_base_id) for document in documents]